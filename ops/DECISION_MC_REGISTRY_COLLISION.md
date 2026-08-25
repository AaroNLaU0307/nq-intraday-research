# DECISION REQUIRED — two ratified artifacts cannot both be implemented

    ITEM_ID       = MC-REG-COLLISION-001
    RAISED        = 2026-08-25, during N12 (MC registry parser)
    RAISED_BY     = Opus 5, builder seat
    STATUS        = OPEN — no repair attempted, nothing ratified was edited
    BLOCKS        = the first real MC run — the registry append that
                    authorizes it cannot be made while this is open
    DOES_NOT_BLOCK= N12 itself, which is complete and green
    NOT_ON_TODAY'S_CRITICAL_PATH = N13 is separately blocked anyway: it
                    depends on N11, which is unimplemented
                    (`GridReplayAuthority` / `KReplayEvidence` do not exist
                    in the repo), which depends on N10, which depends on
                    N09 — an Aaron execution-authorization node. So this
                    ruling is not urgent. It is simply much cheaper to make
                    now than at N16, with a run pending.

---

## 1. The contradiction, in one paragraph

**G8 (RATIFIED AS MODIFIED, 2026-08-24)** puts the MC run registry rows in
`ops/TRIAL_REGISTRY.md` and dirty-allowlists that file and no other
(`DIRTY_ALLOWLIST=ops/TRIAL_REGISTRY.md_ONLY`).

**The N05 supplement grammar (`ND1_RECOMMENDED_PROFILE_R2`, approved
2026-08-23)** lists `MC_RUN_AUTHORIZED` and `MC_RUN_STARTED` in
`ND3_DEFERRED_TOKENS` and refuses them **by name**, and
`ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION` makes that refusal total — not
one row, the whole file.

Both are ratified. Together they are not implementable. The day-strata
supplement is an **input** to the MC run, so the first real MC run would
break the mechanism that proves its own input was authorized.

---

## 2. What was measured, not inferred

Reproduced against the real `ops/TRIAL_REGISTRY.md` at HEAD. No registry
content was read into the session — only verdict codes were printed.

| registry state | supplement resolution | S0-T001 authorization |
|---|---|---|
| today, unmodified | no refusal, 0 chains | live commit found, `ok` |
| `+ MC_RUN_AUTHORIZED` row | **`token_deferred_to_nd3`, 0 chains** | live commit found, `ok` |
| `+ MC_RUN_STARTED` row | **`token_deferred_to_nd3`, 0 chains** | — |
| `+ MC_BRANCH_SEALED` row | no refusal (skipped as foreign) | — |
| `+ MC_RUN_FAILED_POSTSTART` row | no refusal (skipped as foreign) | — |
| `+ RUN_AUTHORIZED` row, unprefixed | no refusal (skipped) | **live commit LOST** — `RUN_AUTHORIZED row does not contain the verbatim packet §10 sentence` |

Pinned in the suite as
`tests/test_mc_registry_contract.py::test_a_ratified_mc_row_breaks_supplement_resolution`.
It is a reproduction, not a defect to be "fixed" by editing the test.

### 2.1 The spelling is not the way out

G1's ruling says «逐字复用 S0-T001 实史模式». S0-T001's real tokens are
**unprefixed** — `PACKET_APPROVED`, `READY_FOR_RUN_AUTHORIZATION`,
`RUNNER_IMPLEMENTED`, `RUN_AUTHORIZATION_SUPERSEDED`, `RUN_AUTHORIZED`.
Taking "verbatim" literally, and reusing the unprefixed strings, breaks
S0-T001's own resolver instead (last row of the table above), because
`resolve_authorizations` validates **every** `RUN_AUTHORIZED` row against
S0's trial and returns a chain-level problem on the first one that fails.

So a prefix is forced. And the prefix is not a free choice either — three
independent places in this repo already anticipate exactly
`MC_RUN_AUTHORIZED`:

- `supplement_contract.ND3_DEFERRED_TOKENS`
- `real_input.prepare_real_mc_input` docstring — "until Aaron + Codex
  introduce the MC registry vocabulary"
- `consumer.MC_AUTHORIZATION_EVENT = "MC_RUN_AUTHORIZED"`

Every reachable spelling breaks one of two ratified parsers. This is a
governance contradiction, not a naming problem.

### 2.2 A second coupling, found the same way and also measured

`SEQUENCE_NAMESPACE=GLOBAL` is enforced, not prose:
`supplement_registry._check_global_sequence` computes "highest so far" over
**every numbered row in the file, foreign ones included**, and then demands
the NEXT value — not merely a larger one.

Measured: a `MC_BRANCH_SEALED` row at sequence 99, dropped into a file whose
highest was 5, makes the next numbered supplement row illegal
(`supplement_seq_not_next_value`) — permanently. The two lifecycles can wedge
each other through the sequence cell alone, with no token collision involved.

This one the builder **did** implement rather than escalate, because the rule
is a property of the FILE and is already ratified, and it reads identically
whether MC rows share `ops/TRIAL_REGISTRY.md` or get their own file — so
enforcing it presumes nothing about how this item is resolved.
`mc_registry` now refuses `mc_seq_not_next_value` / `mc_seq_duplicate` /
`mc_seq_not_integer`, and
`test_a_gappy_mc_sequence_would_wedge_every_other_lifecycle` states the
coupling from both sides.

It is recorded here because it is evidence about R1: the global sequence
namespace is real and enforced, so splitting the file splits something that
currently works.

---

## 3. Why the builder did not resolve it

QROS precedence: a sealed research contract and ratified artifacts sit above
implementation. Reconciling two ratified artifacts is a **decision**.
"Ambiguous write permission → keep the restrictive reading and stop."
Nothing ratified was edited: `supplement_contract.py` and
`supplement_registry.py` are byte-unchanged.

---

## 4. Candidate resolutions

### R2 — discharge the deferral guard *(builder's recommendation)*

Stop refusing `MC_RUN_AUTHORIZED` / `MC_RUN_STARTED` by name in the
supplement grammar; skip them as foreign-lifecycle rows, exactly as
`MC_BRANCH_SEALED` is already skipped today.

The argument is that the guard's own stated condition has expired. Its
refusal message reads: *"deferred to N-D3 (§D.3.4) and is NOT implemented by
the N-D1 grammar"*. It was a **temporal** guard — it existed so nobody could
write an MC row while the meaning of one was undecided. N-D3 has now been
ruled and the meaning exists. Retiring it is discharging a guard, not
weakening one.

The fail-closed property is **preserved and relocated, not lost**, and this
is the condition on R2: `mc_registry` owns the `MC_` prefix and refuses any
`MC_*` token it does not know (`mc_unknown_event_token`), rather than
skipping it. That is already built and tested —
`test_an_unknown_mc_token_is_refused` covers `MC_RUN_AUTHORIZEDD`,
`MC_RUN_SEALED`, `MC_RUN_FAILED`, `MC_ANYTHING_AT_ALL`. Without prefix
ownership, R2 would be a genuine loosening; with it, every string the old
guard refused is still refused, by the grammar that owns it.

- **Cost:** changes an N05-ratified vocabulary's *behaviour* (not its token
  list). Two lines in `supplement_registry`, plus the parametrized test
  `test_nd3_deferred_tokens_refused_by_name` narrowing from 5 tokens to 3.
- **Residual:** `ND3_DEFERRED_TOKENS` would still name `MC_RUN_SEALED` and
  `MC_RUN_FAILED`, which the ruling never created (see §5). Harmless —
  they are refused twice over.

#### R2's real weakness, found by the builder against its own recommendation

The refusal does not merely relocate from one grammar to another; it
relocates from one **call site** to another. Today `resolve_supplement_chains`
runs on `ops/TRIAL_REGISTRY.md` from four production paths
(`supplement_runner`, `day_strata_supplement`, `real_input`, `consumer`).
**Nothing calls `mc_registry` at all** — the wiring is N13's work, and
`consumer.authorize_real_mc` still refuses by substring rather than by
parse.

So between R2 landing and `mc_registry` being wired into those same paths,
a stray `MC_RUN_SEALED` row would be refused by *nobody*: the supplement
grammar would skip it and no MC parser would run. That window is a genuine
loss of coverage, not a theoretical one.

**Therefore R2, if ruled, should be conditioned on ordering:** the two
tokens come off the by-name list only in the same change that wires
`mc_registry.resolve_mc_chains` into every path that today resolves
supplement chains over that file. Ruling R2 without that condition is worse
than ruling R1.

### R1 — a separate MC registry file

`ops/MC_RUN_REGISTRY.md`, with its own dirty allowlist entry.

- **Cost:** contradicts G8's `DIRTY_ALLOWLIST=ops/TRIAL_REGISTRY.md_ONLY`
  literally, so it needs G8 amended anyway — the same class of change as R2,
  against a *newer* ruling.
- Splits the global sequence namespace, which the supplement grammar
  explicitly relies on ("a numbered supplement row has to slot into the same
  increasing integer sequence the S0 rows already occupy").
- Two files to keep in the clean-gate allowlist instead of one, on the exact
  path where a dirty-worktree mistake ends a run.

### R3 — teach S0's resolver to filter by trial ref

Rejected by the builder before reaching this record. `scripts/s0_real_run.py`
governed a **completed** run whose evidence is sealed; changing its
authorization semantics after the fact is the one thing that must not
happen here.

---

## 5. A recorded divergence, for whoever rules

`ND3_DEFERRED_TOKENS` anticipated four MC tokens. The ruling created two of
them and not the other two:

| anticipated | ruled | why |
|---|---|---|
| `MC_RUN_AUTHORIZED` | ✔ same | — |
| `MC_RUN_STARTED` | ✔ same | — |
| `MC_RUN_SEALED` | ✘ → `MC_BRANCH_SEALED` | sealing is branch-scoped: both branches are precomputed blind |
| `MC_RUN_FAILED` | ✘ → `MC_RUN_FAILED_POSTSTART` | G4 splits failure on whether the exposure slot was already consumed |

Consequence either way: the by-name list refuses two names no registry will
ever emit, and does not name the two that replaced them. Under prefix
ownership that costs nothing.

---

## 6. What is NOT being asked

- Not asking to run anything, authorize anything, or append any registry row.
- Not asking to change samples, labels, NA policy, costs, Primary, Oracle,
  feasibility or run definitions.
- Not asking to amend the preregistration or move exposure state.

The question is exactly one sentence: **which of R1 or R2 reconciles G8 with
the N05 supplement grammar** — and, if R2, that it is conditioned on
`mc_registry` retaining prefix ownership.

---

## STATUS — CLOSED, 2026-08-25

**Appended, not rewritten.** Everything above is the record as the reviewers
held it, including the two errors Fable found in it (§4's example token
contradicts §5; §4 says four production paths resolve, and only
`supplement_runner` does). Correcting a held artifact in place is what cost a
review session on 2026-08-24 — findings go in new records, and this closure
is one.

```
RULING        = R2, AS MODIFIED
PROPOSED_BY   = Fable 5        (ops/RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md)
RATIFIED_BY   = Codex GPT-5.6 Sol, fresh session   (ops/RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md)
ADJUDICATED_BY= Aaron, 2026-08-25
DELEGATED     = YES   —— 提案与批准都是委托，不是 Aaron 本人的判断
```

Sol replaced C2 outright. Fable's version required every production reader to
be covered but still allowed each to take its own read of a MUTABLE shared
file, so MC validation could pass against one version while supplement
resolution acted on another — four independent `read_text` calls on this path
existed at the time. The ratified C2 requires ONE shared validation boundary:
one read, both lifecycles against the identical immutable snapshot, and a
refusal from either leaving nothing usable.

Implemented in the same change, as C2 requires:

- `src/itsf/mc/registry_boundary.py` — the boundary.
- `supplement_runner.run_supplement_production` obtains its chain through it;
  an MC refusal arrives as the chain's own `problem`, so the existing
  A_PRECHECK gate enforces the coupling with no gate changed.
- `supplement_contract` — the discharge as an explicit exclusion (C3). The
  ratified five-name transcription is unchanged and still verifiable.
- Two tests C2 names: architecture/no-bypass and behavioural. Both
  mutation-proved.

**Measured after the change, against the real registry:** a complete,
well-formed MC chain appended to `ops/TRIAL_REGISTRY.md` leaves the boundary
usable, supplement resolution unrefused, and MC-R001 carrying 7 events and 1
live authorization. Before, the same append refused everything.

**Not adopted, tracked separately:** C6 — case and prefix variants
(`mc_run_authorized`) are invisible to both grammars. Pre-existing,
machine-inert, neither created nor widened by R2.

**A limitation that travels with this ruling:** Sol disclosed that it authored
the C2 modification and is therefore not independent of that condition's
design. C2's text has had no independent review. The implementation goes
through N14; nobody may read this as "C2 was independently reviewed".
