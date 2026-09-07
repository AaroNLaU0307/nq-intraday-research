# BACKLOG — the single blocker set and the non-blocking backlog (QROS-CF v2 §2.5)

```
RECORD_TYPE   = BACKLOG (one file; §1 is the ONLY blocker ledger of this project)
OUTCOME_CLEAN = YES
ROWS          = close, never delete; a closed row keeps its closing evidence
UPDATED       = 2026-09-07 (P1)
```

Admission test for §1 (QROS-CF v2 §2.5): a row enters `CURRENT_BLOCKERS` only if it names exactly one threat — T1 research correctness · T2 look-ahead/leakage · T3 data identity/provenance · T4 reproducibility · T5 real-run execution safety · T6 independent-verification validity — and a concrete failure path on the current or next stage. Not admissible: unreachable on the current path; governance format; cosmetic; guard-of-a-guard; a lifecycle edge that cannot occur at this stage; ops-document consistency.

Expiry rule (DEC-0001, converged §2.5): at expiry the only legal outcomes are clearing evidence, one extension with a written reason, or Aaron's decision. A builder may reclassify to §2 only a row it opened itself whose failure path was never REPRODUCED; reviewer-opened or REPRODUCED rows leave by evidence or by Aaron. An owner hold is a registry row and is independent of this table.

## 1. CURRENT_BLOCKERS

| id | issue | threat | stage affected | evidence required to clear | owner | opened at | expires | status |
|---|---|---|---|---|---|---|---|---|
| — | *no open rows* | | | | | | | |

Candidates examined at P1 and **not admitted**, with the reason (so the table is demonstrably exercised):

| candidate | why not a blocker |
|---|---|
| Registry sync failure model boundary (2) — conflict-copy detector `find_conflict_copies` written, never wired (`DEFERRED_AFTER_MIGRATION.md` §3 said real runs stay blocked until wired + reviewed) | The failure mode was OneDrive conflict copies of the registry; migration Route A (2026-08-31) moved the canonical registry to `C:\Users\Aaron\quant-data\itsf-registry`, a plain git repository outside the synced tree, and every append is witnessed (hash chain in `registry-witness/itsf`). Four real runs (S001–S004) were authorized by Aaron after that freeze text, which supersedes it in practice. Kept in §2 as B-07 with a T3 note; no failure path on the current stage. |
| Governed-execution identity not yet in the gate (until P2 lands, a live authorization could survive a change outside `src/`) | No live authorization exists; P2 of this window lands before the next one. Window task, not a blocker. |
| `archived_bytes_deleted` / ARCHIVE-CODE-6 amendment (STATUS=PROPOSED) | Fail-closed today; guard-of-a-guard class (prior plan §D1); no research consequence. §2 B-04. |
| `qros status` HOLDs (A2→B, I→J), `trial_accounting` STALE, 14 triggers UNASSESSED | Informational for ITSF (DEC-0003); the runner's gates do not read `qros`. §2 B-09..B-11. |
| Second physical volume / S8 backup (charter invariant 10) | T4 only in the sense of a disk loss; registry in git + witnesses, sealed evidence mirrored in `itsf-runs-archive`, data re-purchasable for $14.30. §2 B-05. |
| N08 scope unresolved | Blocks no downstream node (DAG has no dependant). §2 B-08. |

## 2. Backlog (non-blocking)

| id | item | class | source | disposition | notes |
|---|---|---|---|---|---|
| B-01 | Tier-C test retirement by behaviour (subject archived / property moved / replacement proven), one at a time | governance | converged §6 (F12), Aaron boundary "no bulk retirement" | post-roadmap, owner window | list in proposal v1 §6.3 is a starting inventory, not a verdict |
| B-02 | Physical test-directory moves (`tests/validity`, `tests/safety`, `tests/governance`) | governance | converged RM6 | post-roadmap | markers carry the tiers until then (`tests/tiers.py`; populated at P4) |
| B-03 | `ops/` archive with a generated index, delete nothing | governance | converged RM7 | post-roadmap | freeze on new instances of retired kinds is in force now (DEC-0006 I7) |
| B-04 | ARCHIVE-CODE-6 amendment (`archived_bytes_deleted`) — decide or drop | guard-of-a-guard | `AMENDMENT_ARCHIVE_CODE_6_2026-09-05.md` (STATUS=PROPOSED), `SEAT_RESULT_ARCHIVE_CODE_6_FABLE_2026-09-05.md` | owner decision when convenient; fail-closed meanwhile | first-run unreachable; S002–S004 ran with a non-empty archive without needing it |
| B-05 | Second physical volume / offline bundle for the registry and sealed evidence (charter invariant 10; former WAITING_ON_AARON A4, plan C1/C6) | T4 (disk loss) | `WAITING_ON_AARON.md` A4 | when a second volume exists | registry in git + witnesses; archive mirror; data re-purchasable |
| B-06 | `authorized_commit_matches_head` ordering: the identity check runs after the full Development read (perf only) | perf | plan C7, Aaron 2026-09-05 | backlog | correctness unaffected; gate still refuses before any write |
| B-07 | Wire `registry_witness.find_conflict_copies` into the start path and review it | T3 note, no current failure path | `DEFERRED_AFTER_MIGRATION.md` §3, `REGISTRY_SYNC_FAILURE_MODEL.md` | next time the registry boundary is touched | see §1 candidate table |
| B-08 | N08 scope ("9/12 簇") has no source in the tree | scope | `N08_SCOPE_UNRESOLVED.md` | Aaron supplies the source or redefines; no dependant | |
| B-09 | `qros-state.yaml` `trial_accounting.canonical_ref` points at the in-repo tombstone; the registry moved | runtime config | `qros status` STALE | when a runtime window opens | informational (DEC-0003) |
| B-10 | `qros` A2→B and I→J HOLDs are structurally unsatisfiable for ITSF | runtime | `qros status` | informational (DEC-0003) | future Stage I travels as a packet so I→J can be satisfied |
| B-11 | `qros` trigger path map not configured (14 UNASSESSED) | runtime config | `qros check` | when a runtime window opens | the §7 trigger list is applied by hand in `REVIEWER_CONTRACT.md` §2 |
| B-12 | Supplement family has no in-gate pytest (only the S0 runner runs the suite inside its gate); the suite was run by hand before each P2 | T5 note | this window's read of `GATE_TABLE` | decide with N10's run family | the governed-execution identity now covers `tests/` A+B files, so a deleted test voids an authorization; the in-gate run itself is the S0 gate's |
| B-13 | `MATERIALITY: ORDINARY|MATERIAL` line absent (only holds F→L for a MEASUREMENT; ITSF is FULL) | runtime | `WAITING_ON_AARON.md` B1 | only if a MEASUREMENT sub-study is ever run | |
| B-14 | UNMAPPED_SEAL_CODES (seven) | fail-closed edge | plan C2 | backlog | none can silently acquire a gate name |
| B-15 | Public export set (README/RESULTS/METHOD/REPRODUCE, sealed prereg, data manifest, lockfile, `src/`, tier-A tests, one-page governance summary) with clean-room replay | reproducibility at release | converged F16 | release time | `PUBLIC_RELEASE_INVENTORY_2026-09-05.md` is the inventory |
| B-16 | Nine-event run grammar (converged §2.4) for the first run family without a ratified grammar — **N13, the full MC runner**, whose MC_RUN_* events are the deferred ND-3 tokens (P5 determination; N10 is not a run, N11 is wiring) | grammar | converged §2.4, F11 | inside N13's S3, with T-F02 (exhaustive pair test) and T-F11 (success / archive-failure / verification-failure chains on fixtures) before N13's PROPOSED row | never a standing migration |
| B-21 | ~~N10 closure~~ **CLOSED 2026-09-07** (DEC-N10-CLOSE-1). All three requirements were reconciled mechanically: independent verification = registry seq 33 by a non-builder seat; attestation = `0b5d9382…`, bytes located and restating the supplement id, sealed artifact sha and rows digest; pin = the I3 binding returning ok with zero problems live. The definition's two-commit sequence was the retired after-the-fact registration pattern; the surviving sequence is registry `729daa8` then framework `56cf038`, correctly ordered. No new evidence, no registry mutation, no new reviewer round. | owner decision | P5 read (DEC-0005) | P6 | **CLOSED** |
| B-17 | L6 runtime re-tabling to five stages; GRAD-* pilots | runtime product | converged RM1/RM2 | out of research backlogs; owner window only | |
| B-18 | Historical per-event ops documents (prompts, packets, rulings, seat results, findings, corrections, checkpoints, prep items, off-limits companions, incident documents) | archive | converged §4 | post-roadmap with B-03 | no new instances (I7) |
| B-19 | `test_exposure_ledger_migration` row-identity and "exactly one reveal" assertions become prefix-identity and non-decreasing invariants when the first forward row lands | test conversion | DEC-0004 | P5 of this window | |
| B-20 | Witness filing defect found by the new history-health check (P4): `WITNESS_T1_APPENDED_2026-09-05.json` names `WITNESS_P4_APPENDED_2026-09-05.json` as its predecessor while its `previous_sha256` is the post-F3 registry hash certified by `WITNESS_F3_APPENDED_2026-09-05.json`. Hash chain intact (every `previous_sha256` resolves to a witness); only the name pointer is wrong | T3 note, no integrity gap | `tests/test_registry_integrity.py` (strict xfail on the exact condition) | a correcting witness appended by the registry owner when convenient; then the xfail marker is removed | witnesses are append-only evidence; the builder does not edit them |

| B-22 | F07 — an ops-only committed change can still false-refuse at the P3 append: `append_run_started` compares the live P2's `authorized_commit` with `head_commit` by exact 40-hex equality, so a documentation commit made after the signature refuses the start even though the governed-execution identity is unchanged | usability of the authorization; never a safety hole | GPT-6 Astra QROS-CF P2 gate review 2026-09-07 (F07, NON-BLOCKING) | next time the append seam is touched; `execution_identity.compare` already exists and is the substitute comparison | it refuses a LEGAL start and cannot admit an illegal one, so it holds nothing. Excluded from the 2026-09-07 repair window by Aaron's instruction |
| B-23 | F08 — a main-agent `OWNER_REVOCATION` on the F1 path may close an authorization: `_is_owner_revocation` admits the owner-actor P2S, and the F1 branch reaches P2S without the owner-actor requirement the direct branch enforces | owner-authority precision | GPT-6 Astra QROS-CF P2 gate review 2026-09-07 (F08, NON-BLOCKING) | with the next owner-control change | it CLOSES authorization rather than granting it, so it cannot produce an unauthorized STARTED. Excluded from the same window by the same instruction |
## 3. Closed since the last pending lists (evidence)

| former item | closed by |
|---|---|
| WAITING_ON_AARON A1 (directory grants) | given and used 2026-08-29; `DIRECTORY_CREATION_GRANTS.md` §4 |
| WAITING_ON_AARON A1b (P1 append) | registry seq 14, 2026-08-30 |
| WAITING_ON_AARON A2/A3 (migration ①②) | `MIGRATION_ROUTE_A_COMPLETED_2026-08-31.md` |
| WAITING_ON_AARON B2 (first real-data authorization) | registry seq 15–21 (S001), 25 (S002), 28 (S003), 32 (S004) |
| PENDING_ANCHOR_UPDATES (five items) | merged into the master plan §15.1 on 2026-08-25 (its own banner) |
| DEFERRED_AFTER_MIGRATION §1 (CR1 freeze until R4) and §2 (R4 draft) | `APPROVAL_R4_CR1_GRAMMAR_2026-08-31.md` |
| NEXT_HANDOFF: ARCHIVE-CODE-6 review dispatch | returned: `SEAT_RESULT_ARCHIVE_CODE_6_FABLE_2026-09-05.md`; register empty |
| COMPLETION plan A1–A3 | N09 executed (S001–S004) |
| COMPLETION plan C4 (R1 fix unreviewed) | reviewed by the Fable engineering-safety seat (H1/M1), `REVIEW_RESULT_ENG_SAFETY_2026-09-02.md` |

Off-limits reminder: the master plan under `ops/outcome_quarantine/` is **OFF-LIMITS** to blind seats; the builder's bounded read of its N10/N11/N13 definitions is authorized by DEC-0005 only.
