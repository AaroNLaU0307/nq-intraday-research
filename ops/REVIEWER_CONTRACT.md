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
| FULL pre-seal design challenge (S2) | fresh Sol/Astra | outcome-blind (pre-reveal) | 1 seat, ≤ 2 rounds; travels as Review Packet v1 (L6 A2) |
| Consequential sealed run output | fresh verifier session | claim-blind | 1 dispatch + 1 retry (DEC-0007) |
| Final confirmatory statistic before reveal (Stage I) | fresh verifier, not a prior seat for this RQ | outcome-blind | 1 + 1; travels as Review Packet v1 (L6 Stage I) |
| MEASUREMENT with `MATERIALITY: MATERIAL` | fresh session, non-author | claim-blind | 1 round; Review Packet v1 (L6 material-measurement) |
| Producer and evidence conflict | fresh seat of a different family | claim-blind | 1 round |
| Change to a tier-B authorization gate or leakage-sensitive code | fresh Sol | claim-blind | 1 round |
| Promotion, `falsified`, public release, other QROS §7 triggers | Fable | as needed | 1 wave ≤ 3 workflows; +1 only for unresolved Critical/High |

Not dispatched by default: maintenance commits, ledger appends, refactors, document edits, enum questions, wording, a review of a review absent contamination. Every review outside the three L6-recognised ones is a one-page brief (template `VERIFICATION_BRIEF_TEMPLATE.md` under `ops/templates/`, landing at P3), not a packet.

## 3. Two verification obligations, never confused

- **RUN-IDENTITY VERIFICATION** (claim-blind), per declared `VERIFICATION_SCOPE`, which may cover a dependency chain. Every consequential artifact must be recomputed inside some VERIFIED scope before a reveal reads it; a new external data source always gets its own custody verification. Pre-freeze set: the object under verification, sealed inputs, the code modules at the authorized governed-execution identity, and the brief with its matching rules hashed before dispatch. Post-freeze set: the producer's registry claims and any prior verifier outputs. Byte-identity checks (sha256, canonical bytes) carry no judgment; any judgment-bearing matching rule is fixed in the brief before dispatch or the check is not blind.
- **STAGE I** (outcome-blind): pre-freeze set additionally includes the sealed preregistration with its Lineage/Amendments and the A2 record. The verifier freezes its own recomputed statistic before opening the sealed output, then states independence per dimension and per target (context · authorship · model diversity · empirical), checks conclusion against evidence and propagation completeness. From the comparison onward the seat is outcome-exposed and is recorded so on the seat axis.

One dispatch may satisfy both when its brief covers both and its level is outcome-blind.

## 4. Contamination protocol (DEC-0007)

1. The dispatcher builds a clean external evidence directory with the verifier-directory builder script (`build_verifier_dir.py` under `scripts/`, landing at P3) from an explicit spec: pre-freeze files first; post-freeze comparands only after the verifier has written `FREEZE_MARKER.json`. Nothing else: no registry, no `ops/`, no `tests/`, no prior verifier directories, no memory files.
2. The verifier works only inside that directory. Before freeze: no git, no repository listing, no search, no reads outside the pre-freeze set. Executing an allowlisted module may import its dependencies; that is execution, not inspection, and is recorded in the attestation.
3. Phase order is fixed: custody → blind recomputation → FREEZE (result written, hashed, marker written) → post-freeze comparands delivered → compare → attestation with the header template (`ATTESTATION_HEADER_TEMPLATE.md` under `ops/templates/`, landing at P3).
4. Exposure before freeze (anything outside the pre-freeze set): STOP, row on the seat axis (`ops/REVIEWER_EXPOSURE_LOG.md`), discard the post-exposure outputs. The builder may dispatch **exactly one** fresh retry with a rebuilt directory without asking Aaron. A second contamination on the same verification target goes to Aaron (checkpoint 6).
5. The result enters the registry as the family's verified/failed row citing the attestation hash and the frozen-result hash. The verifier commits nothing to the framework repository.

## 5. Dispatch record

Every dispatch is one row in `ops/DECISIONS.md` (kind REVIEW_DISPATCH) naming the brief's sha256, the spec's sha256, the seat, the blindness level, and the budget consumed; the verdict is a second row (kind REVIEW_VERDICT) citing the attestation's sha256. No per-review prompt, packet, ruling or seat-result document is created.
