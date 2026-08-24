```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=High
EXECUTION_MODE=STANDARD
ROLE=formal reviewer — ratify, modify, or reject one ruling proposal
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=the Fable 5 session that authored the proposal; the Opus 5
            builder session that authored the record and the code; any
            subagent of either
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
SUBAGENT_OR_WORKFLOW_BUDGET=0 — read-only, one item
WHY_THIS_MODEL=Established two-step for this project: Fable proposes under
            Aaron's standing delegation, a fresh Sol ratifies, Aaron
            adjudicates. Same shape as the N-D2/N-D3 batch of 32.
```

# MC-REG-COLLISION-001 — ratify, modify, or reject

## Transport

Recompute and match before any work. On mismatch, truncation or absence:
**STOP and report.** Chat-carried bytes are never a source of truth.

| SHA256 | bytes | path |
|---|---|---|
| `03C42848C14962A168B49586C75D67655784D0A0D2A955AFBCC6FD282BCF06D6` | 16230 | `ops/RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md` |
| `3D9A4E385FF88D18914C92C4942291813370955C4E077AC46FAAD89AA7FD5295` | 10194 | `ops/DECISION_MC_REGISTRY_COLLISION.md` |
| `DA64A3D68454E6F129287412F200EA51309EE85DAAD9D9BDB7465D9765E47991` | 86999 | `ops/DECISION_PACKET_N00_AND_ND1.md` |
| `B56D4205AAEC5E2A7EAFCC10E2BA2FABFF46EAD5C6C4E809DA4D97A2F0C6D005` | 23458 | `src/itsf/mc/mc_registry.py` |
| `C1628B51D94A54750BCCBB5E5060F2C210DFE160898A03CE96097CC192096613` | 65079 | `src/itsf/mc/supplement_registry.py` |
| `C51D25E58545F7C4E4C71EF93DACF29808FDE5E93EA7A3D5A11D32EFC91B72EB` | 18166 | `src/itsf/mc/supplement_contract.py` |

Repo: `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
HEAD: `ba9745340b07650a396136c2f9820cc504295ed1`. All six are committed;
worktree carries only this prompt.

## What is being asked

Fable's proposal rules **R2** — discharge the expired by-name deferral for
`MC_RUN_AUTHORIZED` and `MC_RUN_STARTED` only, under five conditions
C1–C5 — and rejects R1, R3 and a fourth (sequencing) reading it constructed
itself. Ratify it, modify it, or reject it, in the shape the N-D2/N-D3
ratification used:

```
ITEM_ID=MC-REG-COLLISION-001
RULING=RATIFIED_UNCHANGED | RATIFIED_AS_MODIFIED | REJECTED
MODIFICATIONS=<if any, exact and quotable>
CONDITIONS_AS_RATIFIED=<C1..Cn as they stand after your pass>
```

**Ratifying changes no code today.** C2 binds the discharge to the same
change that wires MC resolution into the production path — and that wiring
is N13, which is separately blocked (N11 unimplemented, N09 awaiting
Aaron's P2). So this ruling governs a future change; it is not a patch
order. Nobody should expect a diff to follow ratification.

## What the builder already verified independently — do not spend the pass re-doing it

The builder (Opus 5) checked Fable's load-bearing claims against the code
rather than accepting them:

- **Transport chain sound end to end.** Fable's four reported file hashes
  and the record's hash match the committed tree byte-for-byte, recomputed
  by the builder after the fact.
- **Finding 3 confirmed, and the builder's record was wrong.** The record
  claims four production paths run `resolve_supplement_chains`. Measured:
  outside `supplement_registry` itself, nothing in `src` calls it except
  `supplement_runner._default_resolver` (RESOLVER_SEAM, line 911) →
  `resolve_supplement_chain` → `resolve_supplement_chains` (line 1416).
  `consumer.authorize_real_mc` and `day_strata_supplement.authorize_supplement`
  are both `-> NoReturn` with no conditional path; `real_input` calls the
  former. The window is one seam, not four.
- **Finding 1 confirmed.** The record's §4 and §5 contradict each other on
  `MC_RUN_SEALED`. Under the recorded R2 shape it stays refused by name.
- **Finding 5 confirmed.** HEAD moved 13fb936 → 0991d6f → ba97453.
- **Attack 2's residual reproduced.** See the next section.

The record is deliberately **not** being corrected. New findings go in a new
record; editing an artifact a reviewer has held is the failure that cost a
whole Sol session on 2026-08-24. Fable's proposal is that new record.

## The five things worth your pass

**1. F3 is the root, and only you can settle it.** Fable's whole case is
that §D.3.4 of `ops/DECISION_PACKET_N00_AND_ND1.md` conditions the deferral
on nothing beyond the N-D3 ruling — it quotes `CONSEQUENCE=在 N-D3 裁定前…`
and `REASON=其生命周期定义…尚不完整`. Read §D.3.4 yourself. If any reading
survives under which the deferral of these two tokens is also conditioned
on something else — the GRID-replay coupling, a wiring precondition,
anything — the discharge is premature and the ruling is wrong at its
foundation. Fable named this as its own F3; it is the one question where a
second reader is genuinely load-bearing.

**2. Is C2 an invariant or still an inventory?** Fable's stated improvement
over the record is that C2 is quantified over *all* production readers
rather than today's list. Read C2 as written and decide whether it actually
achieves that, or whether "every production path that treats
`ops/TRIAL_REGISTRY.md` as an authorization or chain-resolution source"
smuggles the same inventory back in under different words. If it does, the
fix is yours to specify.

**3. A residual Fable classified out of scope — builder proposes an
optional C6; you decide.** Attack 2 found that case and prefix variants
escape both grammars. The builder reproduced it, and reports the first
attempt was **confounded** (the surrounding chain held a real
`MC_RUN_AUTHORIZED`, so the refusal fired on that row). Isolated:

```
one variant row alone in an otherwise clean supplement registry
  mc_run_authorized      MC=-                  SUPPLEMENT=-                  sup_chains=1
  Mc_Run_Authorized      MC=-                  SUPPLEMENT=-                  sup_chains=1
  XMC_RUN_AUTHORIZED     MC=-                  SUPPLEMENT=-                  sup_chains=1
  MC_RUN_AUTHORIZED      MC=mc_utc_malformed   SUPPLEMENT=token_deferred_to_nd3  sup_chains=0
```

Fable is right that it is pre-existing (the old guard was exact-match too),
not widened by R2, and unreachable by any machine reader. The builder's
counter-argument for closing it anyway: `mc_registry`'s stage-1 scan only
inspects row-shaped lines beginning with `|`, so a case-insensitive variant
check there cannot false-positive on prose, and the residual is exactly the
"a row belonging to nobody is a row that passes" shape this module exists to
prevent — one layer down. A human skimming the registry table could read
such a row as an authorization.

Proposed optional condition, **not** smuggled into the ruling:

```
C6 (optional): mc_registry's stage-1 row scan refuses a row-shaped line
   whose event cell case-insensitively matches an MC token but does not
   match it exactly. Pre-existing, out of R2's scope by Fable's reading;
   included only if you judge it belongs to this ruling rather than to a
   separate hardening item.
```

**4. One consequence of leaving `_TOKEN_SCAN_RE` untouched.** Fable's
COLLATERAL keeps the supplement grammar's stage-1 scan covering `MC_RUN_*`
as "harmless belt-and-braces". After R2 that means a *malformed*
`MC_RUN_*` row-shaped line produces a supplement-family refusal code
(`supplement_row_malformed`) for a row the MC grammar owns. Fail-closed in
the right direction, but it attributes the defect to the wrong lifecycle in
the error a human reads. Worth a note in the ruling, or not — your call.

**5. Attack the ruling, not just its reasoning.** Fable argued itself into
R2 from four directions and answered its own F1–F4. The failure mode of a
well-argued proposal is that the argument is sound and the conclusion still
wrong. If you can construct a fifth reading, or show that R1's cost
accounting reverses under a premise Fable did not test, say so.

## Standing prohibitions — in force, unchanged

- Read-only. Do not repair, do not patch, do not edit
  `supplement_contract.py`, `supplement_registry.py`, `mc_contract.py`,
  `mc_registry.py`, or any ratified record. A ratification is prose plus
  exact file-and-symbol references.
- No real Development data read. No supplement / MC / S0 / strategy
  execution. No directory creation under `C:\Users\Aaron\quant-data\`
  (both `supplements\` subtrees must stay non-existent).
- No write probes. No registry appends. No exposure events. No READY or
  authorization events. No push, tag, or amend.
- Do not change samples, labels, NA policy, costs, Primary, Oracle,
  feasibility or run definitions.
- Do not decide Stage I vs discretionary Tier-1. Do not infer LANE or STAGE.
- This ruling is not MC-run authorization. Ratifying it authorizes no run.
- No recursive workflow spawning; no subagent may modify production code.

## Provenance line to carry forward

Fable proposed this under Aaron's standing instruction routing
would-otherwise-need-Aaron decisions to that seat. Your ratification is
likewise a **delegated** act. Anything citing the outcome must carry
`DELEGATED=YES` and must not be written as Aaron's own judgement.
