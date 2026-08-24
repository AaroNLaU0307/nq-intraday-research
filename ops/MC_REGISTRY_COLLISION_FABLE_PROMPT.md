```ini
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=adversarial auditor — ruling PROPOSAL on one governance contradiction
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=the session that built mc_contract.py / mc_registry.py (Opus 5,
            builder seat); must not be a subagent of it
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
SUBAGENT_OR_WORKFLOW_BUDGET=0 workflows — read-only, single question
WHY_THIS_MODEL=Aaron's standing instruction: decisions that would otherwise
            need him go to Fable. The builder found the contradiction and
            argued a side, so the builder cannot also rule on it.
```

# One question. Read the record, propose the ruling.

## Transport

Recompute and match before doing any work. On mismatch, truncation or
absence: **STOP and report**, do not proceed on chat-carried bytes.

| SHA256 | bytes | path |
|---|---|---|
| `3D9A4E385FF88D18914C92C4942291813370955C4E077AC46FAAD89AA7FD5295` | 10194 | `ops/DECISION_MC_REGISTRY_COLLISION.md` |
| `817419CD5910FD352BF291C8C74D6E4723CC6AFEFCD1A1F5FE3CB1326BD88E34` | 10894 | `src/itsf/mc/mc_contract.py` |
| `B56D4205AAEC5E2A7EAFCC10E2BA2FABFF46EAD5C6C4E809DA4D97A2F0C6D005` | 23458 | `src/itsf/mc/mc_registry.py` |
| `9BE097BCBD982F48165F33728FED714D6D69F4872EE4A1A256E19BF75213EE8D` | 12736 | `tests/test_mc_registry_contract.py` |
| `73E837FA94421B97FD9ABDF034102FA2E32BA00203ED23277752D1B7A0BAA1F0` | 25548 | `tests/test_mc_registry_parser.py` |

Repo: `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
HEAD at the time of writing: `13fb936`. The five files above are
**uncommitted** working-tree state; hash the working tree, not HEAD.

`ops/DECISION_MC_REGISTRY_COLLISION.md` is the record. Read it first. It
states the contradiction, the measurements, the candidates and the builder's
recommendation. This prompt does not restate it.

## What is being asked

**Exactly one decision:** does `MC-REG-COLLISION-001` resolve as **R1** (a
separate MC registry file) or **R2** (discharge the expired deferral guard,
conditioned on `mc_registry` retaining prefix ownership)? A third option you
construct is admissible if you name it and argue it.

Emit a **ruling proposal**, in the same shape as
`ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`:

```
ITEM_ID=MC-REG-COLLISION-001
RULING=<R1 | R2 | R3-as-you-define-it>
CONDITIONS=<what must hold for the ruling to be safe>
FALSIFIER=<what observation would show this ruling was wrong>
COLLATERAL=<which ratified artifacts must be amended, by exact file and
            symbol, and which must NOT be touched>
```

A fresh Sol session ratifies or modifies your proposal afterwards. You are
proposing, not sealing.

## The four things worth attacking

The builder recommends R2 and has an interest in R2 being right. Attack it.

1. **Is the guard actually expired?** R2's whole case is that
   `token_deferred_to_nd3` was a *temporal* guard whose stated condition —
   "deferred to N-D3, not implemented by the N-D1 grammar" — has been
   discharged by the N-D3 ruling. If that reading is wrong, R2 is a silent
   loosening of a ratified refusal dressed up as a cleanup.

2. **Does prefix ownership really replace what is lost?** R2 is conditioned
   on `mc_registry.is_mc_row` owning every `MC_*` token and refusing unknown
   ones. Verify that claim against the code, not the docstring. Find a
   string the old by-name guard refused that prefix ownership lets through.

   The builder already found one and recorded it against its own
   recommendation — §4's "R2's real weakness": the refusal relocates by
   **call site**, and nothing calls `mc_registry` yet, so R2 landing before
   N13's wiring leaves a real coverage window. Do not stop at that one.
   Look for a second, and judge whether the ordering condition the record
   proposes actually closes the first.

3. **Is R1 cheaper than the record admits?** The builder argues R1 needs G8
   amended anyway and splits the global sequence namespace. The second claim
   was checked and is NOT prose — `_check_global_sequence` enforces it, and
   §2.2 records the measurement. What is left to attack is whether the
   coupling it creates is a reason to keep one file or a reason to split:
   the same measurement can be read either way, and the record reads it one
   way without arguing the other.

4. **Is there a fourth reading nobody has taken?** In particular: does
   anything in G1/G8 or the N-D2/N-D3 ruling text actually *require* MC rows
   to coexist with supplement rows during the same window, or is there a
   sequencing that makes the collision unreachable — e.g. all supplement
   chains resolved and closed before any MC row is appended? If sequencing
   alone dissolves it, that beats both R1 and R2 and amends nothing.

## Standing prohibitions — unchanged, in force

- No real Development data read. No supplement / MC / S0 / strategy
  execution. No directory creation under `C:\Users\Aaron\quant-data\`.
- No write probes. No registry appends. No exposure or registry events. No
  READY or authorization events. No push, tag or amend.
- **Read-only.** Do not repair, do not edit `supplement_contract.py`,
  `supplement_registry.py`, `mc_contract.py` or `mc_registry.py`. A proposal
  is prose plus exact file-and-symbol references; a patch is not authorized.
- Do not change samples, labels, NA policy, costs, Primary, Oracle,
  feasibility or run definitions.
- Do not decide Stage I vs discretionary Tier-1. Do not infer LANE or STAGE.
- No recursive workflow spawning; no subagent may modify production code.

## What the builder did and did not do

Did: built `mc_contract` (the ratified sixteen, transitions, the modified
authorization sentence) and `mc_registry` (parser, validator, chain
resolver) — 76 tests, green. Reproduced the collision against the real
`ops/TRIAL_REGISTRY.md`, printing verdict codes only, never registry
content. Tightened two transition edges that G7 forbids
(`MC_RUN_COMPLETED → MC_PRIMARY_REVEALED` and
`MC_PRIMARY_REVEALED → MC_RUN_CLOSED`) — that tightening is inside the
ruling and is not part of this question.

Did not: edit any ratified artifact; pick a winner between two ratified
artifacts; touch `scripts/s0_real_run.py`.
