＃ GPT-6 Astra — QROS-CF P2 gate review — HOLD — F01–F08 — TRANSCRIPTION

```ini
RECORD_TYPE        = TRANSCRIPTION of a chat-carried review result (precedent: ops/RULING_SOL_D3_HOLD_2026-08-26.md, and qros-cf-redesign/ASTRA_CHALLENGE_REPORT_2026-09-07_TRANSCRIPTION.md for the same reviewer)
TRANSCRIBED_BY     = Claude Opus 5, the repair-builder seat, 2026-09-07
SOURCE             = Aaron's chat message dispatching the repair task, received 2026-09-07
REVIEWED_TREE      = the QROS-CF I1–I7 implementation window (window log: ops/QROS_CF_WINDOW_LOG_2026-09-07.md)
RESULT             = HOLD — six BLOCKING findings (F01–F06), two NON-BLOCKING (F07, F08)
WHAT_THE_HASH_CERTIFIES = the finding text below, as Aaron stated it; NOT Astra's original report bytes, which never existed as a file in this repository
EDITS              = none to the finding statements. The "reproduced locally" column and the repair pointers are the builder's own additions and are marked as such.
```

## 0. Provenance, stated exactly

This record exists because the standing artifact-transport rule requires it:
an artifact handed between sessions must exist on disk with a recorded
SHA256, and chat-carried bytes are never a source of truth. The six findings
reached the repair seat only through Aaron's dispatch message, so **this file
is the durable definition of F01–F06 and nothing else in the repository was.**

Two limits, so no later reader over-reads it:

1. **This is not Astra's full report.** Aaron's message stated each finding in
   one or two sentences plus its threat class. The reviewer's own prose,
   measurements and reasoning were not transmitted and are not reconstructed
   here. Where a longer original exists in Astra's own session, that original
   governs and this is a summary of it.
2. **It is not the proposal-v1 review.** `qros-cf-redesign/ASTRA_CHALLENGE_REPORT_2026-09-07_TRANSCRIPTION.md`
   is a different review, of the design proposal, with a different and
   unrelated F01–F08 numbering (its F01 is "authorization should bind actual
   execution dependencies", its F06 "owner revocation"). Confusing the two
   would send a reviewer to test the wrong lineage. They share a reviewer and
   a date and nothing else.

## 1. The six BLOCKING findings, as dispatched

`Astra independently reproduced` is Aaron's wording. The threat classes are
his; the vocabulary is `ops/REVIEWER_CONTRACT.md` (T1 research correctness ·
T2 look-ahead/leakage · T3 data identity/provenance · T4 reproducibility ·
T5 real-run execution safety · T6 independent-verification validity).

| id | threat | finding, as stated |
|---|---|---|
| **F01** | T1 | Governed source identity can remain unchanged while Python executes a modified timestamp-valid bytecode cache. |
| **F02** | T1 | A startup `.pth`/import hook can alter runtime/calendar semantics while all locked package versions and the existing environment pins still match. |
| **F03** | T3 | Production can prefer `_local_manifest.json` over the authorized manifest, allowing `condition.json` replacement while the authorized manifest remains unchanged. |
| **F04** | T3 | `condition.json` is verified by pathname and then read again from pathname; replacement between verification and consumption changes consumed bytes. |
| **F05** | T5 | Malformed `OWNER_HOLD` rows can be silently dropped by the shared parser and P3 can still append. |
| **F06** | T5 | `OWNER_HOLD` can be appended after the hold check but before P3 append, leaving `started=True` with an active hold. |

## 2. The two NON-BLOCKING findings, as dispatched

Recorded here for lineage only. Aaron's instruction placed both outside the
repair window and outside the re-review exit criteria.

| id | finding, as stated | why it blocks nothing (Aaron's wording) |
|---|---|---|
| **F07** | ops-only committed changes may still false-refuse at append due to an old exact commit check. | Neither permits unauthorized STARTED. |
| **F08** | a main-agent `OWNER_REVOCATION` on the F1 path may close authorization. | Neither permits unauthorized STARTED. |

Both are now carried as backlog rows **B-22** (F07) and **B-23** (F08) in
`ops/BACKLOG.md`.

## 3. What the repair seat measured — BUILDER'S ADDITION, not the reviewer's

Every finding was reproduced on the tree before any repair was written. These
are the builder's own measurements, offered so the re-review can test the same
lineage rather than take the repair's word for what the defect was.

| id | reproduced how | measured result before repair |
|---|---|---|
| F01 | 450 governed blobs are git-tracked; `__pycache__/` is `.gitignore` line 1; a cache whose 16-byte header still matched its untouched source was rewritten with different bytecode | the process printed `1` where the source says `960`; `covering_mechanism()` nonetheless answered `GOVERNED_IDENTITY` for a `.pyc` path |
| F02 | a `.pth` line beginning `import ` in an isolated site dir | the hook executed at startup; `measure_environment()` reported `pinned=True` with 49/49 versions matching; the module mentioned neither `.pth`, `sitecustomize` nor `usercustomize` |
| F03 | authorized `manifest.json` naming one `condition.json` digest, a conflicting `_local_manifest.json`, a replacement `condition.json` | the replacement verified clean; the loader returned the local manifest |
| F04 | verify by pathname, swap, then re-read the pathname | verified `available`, consumed `degraded` |
| F05 | a hold line with a missing final pipe / an extra pipe inside the reason / too few cells | `active_holds()` returned no holds and no refusal, three times |
| F06 | character offsets inside `append_run_started`: decision read 1972, hold check 2858, **second independent read 3719**, write 3919; no lock, no compare-and-swap | a hold committed between the two reads is invisible to the check and preserved by the second read, so P3 lands after it on pre-hold state |

## 4. Where the repair landed — BUILDER'S ADDITION

Repair commit `f461f098a407ffc87dd0e2187c14ee4f4f00d1fd`. The re-review
packet `ops/REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md` carries the
per-artifact SHA256 declarations; this table is only the finding→file map.

| id | repaired in | refusal code introduced |
|---|---|---|
| F01 | `src/itsf/execution_identity.py` (`bytecode_report`) | `seam_bytecode_cache_readable` |
| F02 | `src/itsf/execution_identity.py` (`startup_report`) | `seam_startup_surface_unpinned` |
| F03 | `src/itsf/data/manifests.py` (`load_authorized_manifest`), `src/itsf/mc/production_inputs.py` | `ManifestError` (no new code) |
| F04 | `src/itsf/data/manifests.py` (`read_verified_bytes`), `src/itsf/mc/production_inputs.py` | `ManifestError` (no new code) |
| F05 | `src/itsf/mc/owner_control.py` (`owner_intent_lines`) | `owner_control_row_unreadable`, `p3_owner_control_row_unreadable` |
| F06 | `src/itsf/mc/registry_boundary.py` (`_compare_and_append`, `_AppendLock`) | `p3_registry_changed_under_decision`, `p3_append_lock_unavailable` |

One repair direction was **implemented and then rejected on measurement**, and
the re-review should know it was tried: for F01, validating cache *content*
against a fresh compilation does not hold — `marshal.dumps` of an equal code
object is not byte-stable, a structural digest needs the deprecated
`co_lnotab`, and both produced mismatches on files nobody had touched (3 and
7 of 68 trusted caches). The launch-condition mechanism replaced it because it
is decidable.

## 5. What this record does not do

It does not accept, adjudicate or close any finding. F01–F06 are BLOCKING
until a fresh independent seat says otherwise, and that verdict is Aaron's to
dispatch and record — not this seat's, which authored the repair.
