# QUANT_WORKFLOW — the operating model for Aaron's quant research (v2)

> **v2, activated by Aaron 2026-09-26; no retroactivity.** The v1 text (2026-09-12) is
> kept at `Workspace Docs/workflow-evolution-2026-09-22/QUANT_WORKFLOW_VNEXT_v1_TEXT_2026-09-12.md`
> (this root is not a git repository). The change table and the activation record are in
> the same folder. The filename stays `QUANT_WORKFLOW_VNEXT.md` because every pointer
> references it.

Applies to every agent doing quant research in this workspace.

## 0. Precedence

1. **An Aaron decision, or a hard research invariant.** Invariants: lockbox and
   one-shot holdouts; immutable sealed artifacts, `runs/`, `audits/` and decision
   logs; read-only discipline; no writes to source repos; declared outcome blindness.
   A delegate decision within §4's delegated scope exercises Owner authority at this
   level, but never overrides a hard invariant and changes an active sealed contract
   only through §8. Aaron's own decision overrides the delegate's.
2. **An active sealed contract or preregistration for the research in hand.** It may
   be stricter than this file.
3. **This file.**
4. Project-local workflow or convenience instructions.
5. Global instruction files and model defaults.

A stale project-local document cannot revive retired machinery (§12). Only levels
1–2 add obligations, and level 2 only for its own research. `PROJECT_STATE.md`
records state, never authority; a claim in it that contradicts this file is a defect
in that file. A conflict this list does not settle is halted and reported, not
reconciled by the session that meets it.

## 1. Priorities

correct research **>** reproducibility **>** essential safety **>** finishing the
research **>** framework perfection.

Tokens and time are spent on what protects a conclusion, never on decorating a record.

## 2. Lifecycle — five stages, then stop

```
S0 FRAME → S1 DESIGN+SEAL → S2 BUILD → S3 RUN → S4 VERDICT → STOP
```

**S0 FRAME** (includes discovery). Work mechanism → family → candidate object; never
"give me N strategies"; zero S1-worthy candidates is a valid end. **Anti-revival:** a
new instrument, lookback, threshold, wrapper, holding period, scaling or announcement
family alone does not make a candidate new; the delegate judges equivalence on
mechanical overlap evidence. **Point-in-time first:** before design effort, confirm
every load-bearing input is reconstructible as known at the decision timestamp;
if not, the candidate is `PARKED_PRE_OUTCOME`. For price-only or trivially
reconstructible inputs this is a one-line statement, never an audit document; a full
data-authority freeze applies only where retrieval feasibility materially determines
the design. The builder states mechanism, rivals
and kill criteria; the delegate decides `RESEARCH | PARK | REJECT`.

**S1 DESIGN+SEAL.** The builder drafts the preregistration. Before seal it shows:

- **resolvability** — admissible n and minimum detectable effect against the
  smallest effect of interest; a design that can only return `unresolved` is
  redesigned or stopped, not run;
- **a verdict rule** — a mechanical map from primary results to KB status (§11);
- **enforced data rules** — every window, terminal-period, universe and NA rule the
  runner can check is checked in code, not only stated in prose;
- **validity checks** — each measurement instrument has a check that runs, and must
  pass, before the primary result is read;
- **design contributions** by any seat, disclosed.

Prereg validators run; the delegate reproduces and seals. The seal is a sha256
manifest over the prereg and the code and data identities that define the object
under test.

**S2 BUILD — the light loop.** Implement, test, repair, replay; mechanical validators
over model review; no review seat, packet or evidence document for ordinary changes.
Post-seal changes are classified (§8) first.

**S3 RUN.** Mechanical gate, checking only what is material: code identity · data
identity · prereg binding · environment where relevant · runner safety · replay where
relevant · outcome-access state · a live one-shot grant. **Green gate ⇒ the delegate
may authorize.** A seal is not authorization. The runner writes the consumption row
**before** touching outcomes; a grant with any evidence of use — partial, crashed,
indeterminate — is consumed; guards fail closed on missing or ambiguous records.
Development, synthetic and replay runs that touch no sealed outcome need no grant.

**S4 VERDICT.** Tooling recomputes and applies the sealed verdict rule. For a
consequential claim the builder first runs its own adversarial pass (§7) and fixes or
discloses; the delegate then reproduces and decides verdict and claim wording. **No
seat departs from the sealed verdict rule after outcome**; a rule that cannot be
applied yields `unresolved`, with the reason recorded. The verdict row names its
decider, what was reproduced, and any external review (normally none). Write the KB
result and **STOP**.

## 3. Seats

| seat | who | role |
|---|---|---|
| Owner | **Aaron** | Owner-retained gates (§4); overrides any delegated decision; activates workflow changes |
| Delegate | **Fable 5.1**, the session Aaron names | decides delegated gates; accepts by reproduction; routes; writes authorization-only messages; designs on request. Never builds, never writes in a project repository |
| Builder | **Opus 5.5 / Claude Code**, one per project | designs, implements, tests, runs authorized runs, keeps the project's records; autonomous under §5 |

Builder and delegate are separate top-level sessions of one model family. That
separates context and authorship; it is **not** model diversity and never empirical
replication. The structural substitutes are reproduction-first acceptance and
rule-computed verdicts. A subagent is never independent of its spawner. No seat
certifies its own material contribution: the delegate's acceptance of an element it
designed counts as `REASONED`, not independent. Aaron may bring in any external
reviewer for a consequential verdict; none is a default seat.

## 4. Authority

**Owner-retained — Aaron alone, acting or granting directly, never through a relay:**
spending money · live capital, broker connections, real orders · credentials and
private data · pushing or publishing anything off this machine (push, PR, public
repository) · permanent deletion.

**Delegated to the delegate, informed by the builder:** S0 decisions · sealing · run
authorization on a green gate · statistical reveal · S4 verdict · promotion,
falsification, retirement, project closure · scope and methodology changes (samples,
labels, NA policy, costs, Primary definitions, exposure and trial accounting) · data
access beyond a grant, where it costs nothing and needs no credentials · local merges.

The builder never authorizes its own run, reveal or verdict, and never widens its own
grant. Anything binding that arrives by message is written verbatim to the decision
log, with sender session and UTC, before it is acted on: session memory is not a
record. **Governance audit ≠ governance execution:** under audit, review, plan or
propose instructions, never self-escalate into writing; ambiguous write permission →
restrictive reading, ask.

## 5. Builder autonomy

Research goal and sealed objects fixed · method the builder's · current hypotheses
challengeable · historical evidence immutable · external and irreversible actions
Aaron's.

Before seal the builder may redesign method, open or stop branches, and close a
candidate pre-outcome, recording why. After seal, method moves only through §8. The
builder returns to the delegate when a gate is needed or a result materially changes
understanding, not to report progress. The delegate sends decisions, grants and
findings, never agendas, question lists or method prescriptions; a HOLD names
blockers and does not plan the repair.

## 6. Records — few, current, one writer

The builder is the only writer of a project's records:

- **`PROJECT_STATE.md`** — current state only, **rewritten, not appended**, at every
  checkpoint; one screen (≈60 lines). Fields as relevant: `RESEARCH_QUESTION` ·
  `STAGE` · active lineages and stage · `LIVE_GRANTS` (or NONE) · `LIVE_OBLIGATIONS`
  with dates · `OUTCOME_EXPOSURE` · `OPEN_BLOCKERS` · `NEXT_DECISION` and who holds
  it. A closed lineage leaves it: one line and a pointer to its closeout. Superseded
  facts are deleted, not annotated. Inactive projects get none.
- **Decision log** — append-only; one row per grant, consumption, seal, reveal,
  verdict, disposition, methodology change or delegate/Owner decision: `id · UTC ·
  decider · decision · evidence pointer (commit)`. Written when the event happens,
  never reconstructed from a later state; an event that cannot be established is
  `UNKNOWN`. Existing ledgers may serve as this log, but one grant lives in one place.
- **Sealed contracts, `runs/`, `audits/`** — immutable; corrections are new dated
  files citing what they correct.
- **Reviews that inform a decision** are saved into the project on receipt; an
  unpersisted review carries no evidential weight.

A derived fact — count, status, liveness — is generated from or points to its source,
never hand-copied into a second document; derived never overrides authority.
Validators check that expected facts are **present and incompatible live facts
absent**.

**Checkpoint.** At every research boundary (seal, run complete, verdict, stop) and
whenever the builder chooses: rewrite `PROJECT_STATE`; regenerate or point derived
facts; run the project's reproduce command and link check; commit; message the
delegate the checkpoint id and commit hash. The delegate reproduces from the
repository at that commit, never from the message. After a merge or push, the same
checks run once on the revision readers will see. The commit and the log row are the
evidence; there is no completion token.

## 7. Acceptance, review, token economy

**Acceptance is reproduction first.** The delegate runs the reproduce command, checks
commit order (prereg → predictions → unseal → scoring), recomputes headline numbers
from committed outputs, and confirms the sealed validity checks ran and passed before
the primary result was read. Every statement carries `REPRODUCED | REASONED |
SELF-REPORTED`; self-reported never passes or blocks on its own. **A PASS lists what
it reproduced; a PASS that reproduced nothing is not acceptance.** Reproduction shows
the numbers follow from the bytes, not that a measurement is valid — hence the sealed
validity checks.

**Bounded review.** PASS = move on. HOLD needs a blocking finding — a concrete threat
and failure path on the current or next stage — and buys one bounded repair. At most
two substantive rounds per gate per lineage, then Aaron. No review creates another; a
finding becomes a row, a bounded repair or a decision. Transport or tool failure is
not a round.

**Governance budget.** Every control must reduce a concrete research risk more than it
costs; otherwise simplify or remove. No control because another failed; no
meta-controls.

**Token economy.** Inline by default: mechanical checks, state rewrites, gate checks,
S2 and checkpoint acceptance. Fan-out (subagents, workflows, ultracode) only where
parallel adversarial coverage can change a decision: S0 mechanism search and
anti-revival overlap · pre-S3 lookahead/leakage hunt · the builder's S4 red-team of a
consequential claim · a project exhaustion audit. Subagent output is a builder claim
until reproduced. The builder needs from the delegate grants, PASS/HOLD with named
blockers, and decisions — not agendas, restated context or re-review of mechanically
settled items.

## 8. Post-seal changes and defects

Classify before changing; ambiguity goes to the delegate. No automatic rerun,
amendment or trial-count change.

| change | seal / lineage | boundary |
|---|---|---|
| `IMPLEMENTATION_FIX` | preserved; same lineage only when restoring the contract | builder |
| `DATA_FIX` | preserved; same lineage only when restoring a frozen input rule | a new source, sample or NA rule is methodology |
| `ANALYSIS_EXTENSION` | original seal and evidence unchanged | delegate; non-confirmatory; no rescue |
| `METHODOLOGY_CHANGE` | amendment or new seal | delegate; same lineage only before exposure |
| `HYPOTHESIS_CHANGE` | new preregistration, seal and lineage | delegate; no transfer as confirmation; disclose reuse |

A confirmed research-affecting defect gets one decision-log entry: defect · affected ·
demonstrably unaffected · unknown · recomputation needed or not, and why ·
evidence-use restriction · runs not recomputed.

## 9. Exposure, blinding, trials

`LANE`, `TRIAL_ACCOUNTING` and `OUTCOME_EXPOSURE` are orthogonal; never infer one from
another, and record exposure even when `N_trials` does not move. `N_trials` lives in
`SAMPLE_REUSE.md` and the prereg; an open accounting decision is settled before an S4
relies on it.

An `EXPOSURE_LEDGER` exists only where blinding, contamination or reveal state need
independent tracking. Exposure is monotonic: once revealed, never regressed; a
missing record means `UNKNOWN`, never `NONE`; an unrecorded exposure is itself a defect.

A lockbox or one-shot holdout is used once, for the pre-committed test. Build a sealed
arm only when a planned test will consume it.

**The repository is not blind:** commit subjects, logs and `PROJECT_STATE` carry
outcomes. A seat that must stay blind gets a sealed bundle, not repository access. The
bundle is an on-demand capability, never a stage.

## 10. Shared mechanical infrastructure

Reuse; existence never makes use mandatory. **Machine checks before model checks.**

| capability | where |
|---|---|
| KB vocabulary, schemas, validator | `quant-research-knowledge-base/` (`python -m quant_kb.validate`) |
| seal / freshness / identity check | `qros check` / `qros status`, on demand only |
| identity, preflight, replay, governed run, reproduce command | each project's `scripts/` or `tools/` |
| sealed / blind bundle builder | `Intraday Trend Strategy Framework/scripts/build_code_review_bundle.py` |

Each active project keeps **one reproduce command** that re-derives its checkpoint
evidence. Never inferred across: builder claim ≠ mechanical evidence ≠ independent
verification; synthetic ≠ real governed evidence; infrastructure readiness ≠ alpha;
prior data access ≠ future execution or reveal authority; a code-quality PASS ≠
research authorization.

## 11. Stopping and status

A verdict is a KB `research_status` — `confirmed supported not_promoted falsified
active archived experimental unresolved` — plus one disposition: `RUN_TO_VERDICT |
CLOSED_PRE_OUTCOME | PARKED_PRE_OUTCOME | NOT_STANDALONE`. No other verdict vocabulary.
When in doubt, `not_promoted`.

Negative results are legitimate completion, for a lineage or a whole project: the
builder declares, the delegate accepts; deletion or publication at closure is Aaron's.
No automatic search after a failure. Re-research needs a genuinely untested
subspace or a demonstrably invalid prior design. `unresolved` licenses no rescue,
threshold change, same-sample retuning or relabelling; no observed power. KB
`FailureMode` links explain future eligibility, never a new verdict.

## 12. Retired

Readable history, never routing or a gate: QROS · L6 and L6-Lite · A–L stages ·
`qros next/packet/prompt` · Review Packets · standing reviewer seats ·
review-of-review · closure and residual-verification packages · mandatory blind
transport · `PASS_WITH_BACKLOG` · automatic nodes from findings · telemetry and qros
runtime dependency · Astra and ChatGPT seats and their prompt formats · K1/K2 ·
vNext's `SUPPORTED | FALSIFIED | INSUFFICIENT_EVIDENCE | PARKED` tokens · per-project
re-confirmation of the delegate's standing authority.

## 13. A new quant project

Needs only this file, a minimal `PROJECT_STATE.md`, two per-project artifacts — a
decision log (an existing ledger may serve) and a reproduce command — and a
preregistration from S1. No governance architecture of its own.

## 14. Messages and prompts

No universal header; a prompt carries what the task needs. Builder and delegate
message directly: a checkpoint message carries id, commit hash and the decision
needed; a decision message carries decision, scope, grant id, one-shot or standing.
The repository, not the chat, is the source of truth. `ROLE / WINDOW / MUST_NOT_BE`
only where independence matters. Model and effort are execution choices; never
silently substitute a model.
