# REVIEWER CONTRACT — QROS-CF v2 (ITSF)

```
RECORD_TYPE = REVIEWER_CONTRACT (QROS-CF v2 §2.8, §2.9; DEC-0001, DEC-0007)
APPLIES_TO  = every review or verification dispatched by this project from 2026-09-07
```

## 1. Verdict shape

```
VERDICT ∈ { PASS, PASS_WITH_BACKLOG, HOLD }
HOLD requires ≥ 1 BLOCKING finding.
A BLOCKING finding names exactly one threat (T1 research correctness · T2 look-ahead/leakage ·
T3 data identity/provenance · T4 reproducibility · T5 real-run execution safety ·
T6 independent-verification validity), a concrete failure path, and its evidence class.
Evidence class ∈ { REPRODUCED (the reviewer reproduced it), REASONED (a design counterexample; may be BLOCKING),
                   SELF-REPORTED (restates the producer's claim; never BLOCKING on its own) }.
NON-BLOCKING findings are listed and become rows in ops/BACKLOG.md; they never hold.
Findings table: id | BLOCKING? | threat | evidence class | evidence | minimal fix | minimal test that settles it
A review that cannot name a threat for its objection returns PASS_WITH_BACKLOG.
```

Rounds: HOLD → builder fixes → ONE re-review covering the fix plus a builder-declared, reviewer-contestable impact scope → still HOLD → Aaron. Two rounds per issue lineage, counted continuously across renames, stages and new rows. Reviewers classify; builders may not reclassify. Where a minimal test can be written, the test decides; where none can, Aaron decides materiality.

## 2. When a seat is mandatory (and only then)

| Situation | Seat | Blindness | Budget |
|---|---|---|---|
| FULL pre-seal design challenge (S2) | fresh `OWNER_DEFAULT_INDEPENDENT_REVIEWER` | outcome-blind (pre-reveal) | 1 seat, ≤ 2 rounds; travels as Review Packet v1 (L6 A2) |
| Consequential sealed run output | fresh verifier session | claim-blind | 1 dispatch + 1 retry (DEC-0007) |
| Final confirmatory statistic before reveal (Stage I) | fresh verifier, not a prior seat for this RQ | outcome-blind | 1 + 1; travels as Review Packet v1 (L6 Stage I) |
| MEASUREMENT with `MATERIALITY: MATERIAL` | fresh session, non-author | claim-blind | 1 round; Review Packet v1 (L6 material-measurement) |
| Producer and evidence conflict | fresh seat of a different family | claim-blind | 1 round |
| Change to a tier-B authorization gate or leakage-sensitive code | fresh `OWNER_DEFAULT_INDEPENDENT_REVIEWER` | claim-blind | 1 round |
| Promotion, `falsified`, public release, other QROS §7 triggers | Fable | as needed | 1 wave ≤ 3 workflows; +1 only for unresolved Critical/High |

Not dispatched by default: maintenance commits, ledger appends, refactors, document edits, enum questions, wording, a review of a review absent contamination. Every review outside the three L6-recognised ones is a one-page brief (`ops/templates/VERIFICATION_BRIEF_TEMPLATE.md`), not a packet.

### 2.1 `OWNER_DEFAULT_INDEPENDENT_REVIEWER` — the seat, resolved at dispatch

Four rows of the table above already name a *property* rather than a product —
"fresh verifier session", "fresh verifier, not a prior seat for this RQ", "fresh
session, non-author", "fresh seat of a different family". The two reviewer rows
named a product only because it happened to be the strongest independent model
available when they were written. They now name the property too, and the product
is resolved **at dispatch time** from Aaron's current routing:

| role | model | note |
|---|---|---|
| `OWNER_DEFAULT_INDEPENDENT_REVIEWER` | **GPT-6 Astra** | preferred/default strongest suitable independent reviewer, challenger, design and Owner-decision seat for **NEW** work (Aaron, 2026-09-10) |
| legacy / fallback / frozen-lineage reviewer | GPT-5.6 Sol | valid, and **remains** the seat wherever a lineage is already executed or otherwise frozen and changing the reviewer would break reproducibility or an existing authority |
| architecture-only | Fable 5.1 | genuine architecture-level blockers; the QROS §7 row above is unchanged by this resolution |
| builder / Main Agent | Claude Opus / Claude Code | never a reviewer of its own work, at any capability |

**Substituting the model does not relax anything else.** The seat is still a fresh
top-level session, still claim- or outcome-blind as its row says, still independent
of the producing session and never a subagent of it, still bound by the transport
and allowlist discipline, still inside its issue lineage's round budget, and a HOLD
still escalates to Aaron. `OWNER_DEFAULT_INDEPENDENT_REVIEWER` is a capability
pointer, not a licence.

**A dispatch must still name the actual model and session class it used**, because
reproducibility is about what happened, not about what the policy preferred. Rows
already dispatched, verdicts already returned, and attestations already written are
**never** retroactively re-attributed: a Sol verdict stays a Sol verdict.

**Resolution is prospective and applies at dispatch.** A round whose transport was
prepared but never dispatched has consumed nothing (see
`ops/ARTIFACTS_UNDER_REVIEW.json` `_withdrawn_before_dispatch`, whose entries record
`was_dispatched: false` and "NOT a review round"), so re-resolving its seat does not
reset its issue lineage or its round counter.

## 3. Two verification obligations, never confused

- **RUN-IDENTITY VERIFICATION** (claim-blind), per declared `VERIFICATION_SCOPE`, which may cover a dependency chain. Every consequential artifact must be recomputed inside some VERIFIED scope before a reveal reads it; a new external data source always gets its own custody verification. Pre-freeze set: the object under verification, sealed inputs, the code modules at the authorized governed-execution identity, and the brief with its matching rules hashed before dispatch. Post-freeze set: the producer's registry claims and any prior verifier outputs. Byte-identity checks (sha256, canonical bytes) carry no judgment; any judgment-bearing matching rule is fixed in the brief before dispatch or the check is not blind.
- **STAGE I** (outcome-blind): pre-freeze set additionally includes the sealed preregistration with its Lineage/Amendments and the A2 record. The verifier freezes its own recomputed statistic before opening the sealed output, then states independence per dimension and per target (context · authorship · model diversity · empirical), checks conclusion against evidence and propagation completeness. From the comparison onward the seat is outcome-exposed and is recorded so on the seat axis.

One dispatch may satisfy both when its brief covers both and its level is outcome-blind.

## 4. Contamination protocol (DEC-0007)

1. The dispatcher builds a clean external evidence directory with `scripts/build_verifier_dir.py` from an explicit spec: pre-freeze files first; post-freeze comparands only after the verifier has written `FREEZE_MARKER.json`. Nothing else: no registry, no `ops/`, no `tests/`, no prior verifier directories, no memory files.
2. The verifier works only inside that directory. Before freeze: no git, no repository listing, no search, no reads outside the pre-freeze set. Executing an allowlisted module may import its dependencies; that is execution, not inspection, and is recorded in the attestation.
3. Phase order is fixed: custody → blind recomputation → FREEZE (result written, hashed, marker written) → post-freeze comparands delivered → compare → attestation with the header in `ops/templates/ATTESTATION_HEADER_TEMPLATE.md`; the dispatch itself follows `ops/templates/DISPATCH_TEMPLATE.md`.
4. Exposure before freeze (anything outside the pre-freeze set): STOP, row on the seat axis (`ops/REVIEWER_EXPOSURE_LOG.md`), discard the post-exposure outputs. The builder may dispatch **exactly one** fresh retry with a rebuilt directory without asking Aaron. A second contamination on the same verification target goes to Aaron (checkpoint 6).
5. The result enters the registry as the family's verified/failed row citing the attestation hash and the frozen-result hash. The verifier commits nothing to the framework repository.

## 5. Dispatch record

Every dispatch is one row in `ops/DECISIONS.md` (kind REVIEW_DISPATCH) naming the brief's sha256, the spec's sha256, the seat, the blindness level, and the budget consumed; the verdict is a second row (kind REVIEW_VERDICT) citing the attestation's sha256. No per-review prompt, packet, ruling or seat-result document is created.
