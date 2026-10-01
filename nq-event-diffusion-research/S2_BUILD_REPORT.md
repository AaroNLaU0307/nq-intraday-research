# R1 — S2 BUILD REPORT (r2, after bounded repair)

```
STAGE          = S2 BUILD
DATE           = 2026-09-17
AUTHORIZATION  = Aaron: S2 BUILD ONLY — implementation, synthetic validation,
                 invariant testing, contract binding, run-readiness construction
REVIEW         = ChatGPT: S2_BUILD = HOLD / BOUNDED_REPAIR (r1), repaired here

S2_BUILD       = COMPLETE
S3_RUN         = NOT AUTHORIZED      OD3_POWER_GATE = NOT RUN
R1_OUTCOME     = NOT COMPUTED        R1_OUTCOME_REVEAL = NOT AUTHORIZED
TRIAL_CONSUMED = NO
```

**No real R1 result appears here, because none exists.** Every number below is a
structural count sealed at S1, a count of code and tests, or a fabricated
synthetic value.

---

## 1. Sealed-contract binding

```
CONTENT_COMMIT              = 46b8aef9d2471dd427db6a780435e743660a6f24  sealed
SEAL_ATTESTATION_COMMIT     = 595af1c9663eb868e9f2d72f44abfe2f426ca24d  sealed
S2_CODE_COMMIT              = 433e2cc035391ec73c5c94135ad9cf6afaca746e  code
S2_BUILD_ATTESTATION_COMMIT = tag r1-s2-built (metadata-only child)
```

Four identities, never interchangeable. The last two are read from
`R1_S2_BUILD_ATTESTATION.json` by `r1.build_identity` — never hard-coded, never
caller-supplied. At S3 preflight `assert_executable_identity` refuses if the
live runtime bytes are not the attested ones: a metadata-only ledger append does
**not** invalidate the identity, a runtime-source edit **does**.

`r1/contract.py` is the single source of every scientific constant, and it binds
rather than restates: operative design ← the attestation; anchor minutes ← the
PSMV artifact, each checked against its own label (`C_0829` must be minute 509);
structural n ← artifact **and** attestation **and** manifest; cost inputs,
bootstrap grammar, control and covariate parameters ← verified present in the
sealed prereg text; RTH structure ← the sealed `psmv_structural.py`; file
identity ← sha256 of all 12 sealed files at every load. Any mismatch raises
`SealIdentityError` and the engine refuses.

All eight required mutations refuse (k, event family, reaction anchors, entry,
exit, calendar digest, structural n, seal identity), plus a single appended byte
anywhere in the sealed set, an unsealed attestation, and a manifest that
disagrees with the seal. Each runs against a *copy*.

## 2. The sealed registry, and the operational ledger

The r1 blocker is resolved exactly as ruled: **the sealed registry stays sealed.**

```
R1_TRIAL_REGISTRY.md    SEALED, byte-for-byte, forever. The immutable lineage /
                        trial-registration snapshot. Never edited, never
                        appended to, no lifecycle event.

R1_EXECUTION_LEDGER.md  OPERATIONAL, outside the sealed digest set. An
                        append-only hash chain: every entry commits to its
                        parent, so an edit, deletion or reordering breaks every
                        descendant.
```

Genesis binds the ledger to lineage and seal: R1 identity ·
`SAMPLE_FORMAL_TRIAL_ORDINAL = 2` · sealed registry sha256 · `CONTENT_COMMIT` ·
`SEAL_ATTESTATION_COMMIT` · `PRIOR_LINEAGE = ITSF S0-T001` ·
`INHERITED_RESEARCHER_EXPOSURE_COUNT = 1575`. Future `RUN_STARTED` — the row
that consumes the trial — is appended **only** here.

Seal semantics were not changed to prefix matching, nothing was removed from the
sealed set, and the seal was not superseded. Two integrity models now coexist:
**exact immutable digest** for the sealed registry, **append-only chain** for the
ledger. Mutation tests prove all four required refusals.

## 3. The Development-data adapter — implemented, not deferred

`r1/dev_adapter.py`. S3 is a RUN stage, so the loader is finished here. It fails
closed, in order: **role** (IV and Lockbox refuse at the role, before any path
is built or any file opened) → **manifest identity** → **per-file digest** →
**schema** → **window** → **duplicates**. Prices are converted from Databento
fixed-point once, at the boundary.

Validated entirely on synthetic JSONL archives with fake manifests, tiny
deterministic fixtures, and a monkeypatched decoder for the DBN branch. **No
real R1 event price was read to test it.** The decoder is imported lazily, so a
machine without `databento` can still load, test and audit every other part of
R1.

Execution stays blocked: the adapter's role is `development_signal`, so
`apply_e4`, `run_primary` and `run_study` all refuse it without an S3 token, and
`DevelopmentBarSource` refuses before constructing it at all.

```
REAL_DATA_ADAPTER_IMPLEMENTED = YES
REAL_R1_DATA_EXECUTED         = NO
```

## 4. A1 — wired into the production path

`r1/auxiliary.py`, computed by `run_study` from its own objects. The caller
boolean is gone: `a1_sign_holds` is no longer a parameter of anything in the
production path.

```
metric_i   = |R_init_i| / ADR14_i                causal, scale-free
boundary_i = median(metric_1 .. metric_{i-1})    STRICTLY PRIOR events
member_i   = metric_i <= boundary_i
A1 holds   <=> sign(mean(Y_net | members)) == sign(mean(Y_net | all))
```

Fixed before any real outcome · no outcome-dependent threshold · no event-type
rescue (an AST test asserts A1 never sees `event_type` or `d_event`) · no new
parameter (a test asserts every A1 function has zero defaults) · no alternate
split · future data cannot move a historical membership (the mutation test
appends later events and asserts every earlier row is identical) ·
non-confirmatory (A1 = True with an interval spanning M is still `UNRESOLVED`).
An unevaluable A1 does not silently pass.

## 5. Sealed errata

`R1_SEALED_ERRATA.md` — a post-seal interpretation artifact, outside the sealed
digest set, bound in run identity as `SEALED_ERRATA_SHA256`.

```
SEALED_TEXT                    = structural span starts 2010-06-17
CORRECT_STRUCTURAL_DESCRIPTION = first E3-eligible event is 2010-07-02
CAUSE                          = 2010-06-17 is excluded at E3, ADR14 warm-up
                                 unavailable (8 prior complete-390 days of 14)
MATERIALITY                    = DESCRIPTIVE_ONLY
CHANGES_EVENT_MEMBERSHIP       = NO      CHANGES_PRE_SEAL_STRUCTURAL_N = NO
CHANGES_PRIMARY_DESIGN         = NO      CHANGES_SEAL                  = NO
```

`R1_S1_PREREGISTRATION_SEALED.md` was **not** modified. Future reports use the
corrected span.

## 6. n semantics

No numerical threshold for "materially shrank n" was invented, and none exists
anywhere in the code — a test greps for one.

```
PRE_SEAL_STRUCTURAL_N = 252   fixed by PSMV. Execution must reproduce it
                              EXACTLY; failing to is RUN_INTEGRITY_FAILURE
                              (r1.errors.RunIntegrityError) — a broken run,
                              never a smaller sample and never an UNRESOLVED
                              verdict at a reduced n.

POST_SEAL_SIGNAL_DEFINED_N    = 252 - E4_COUNT. E4 removes exact-zero
                              reactions: prespecified, applied AFTER structural
                              eligibility, emitted separately. Not shrinkage.
```

The verdict engine keeps sealed M.1's condition as an explicit input with the
non-excusing default; the pipeline always passes `False` and relies on the
integrity failure instead.

## 7. Validation, separated

```
SEAL_SNAPSHOT_VALIDATION   PASS   tools/validate_seal_snapshot.py
                                  CONTENT_COMMIT   46b8aef -> 161 passed, 0 failed
                                  SEAL_ATTESTATION 595af1c -> 185 passed, 0 failed
CURRENT_STATE_VALIDATION   PASS   tools/validate_state.py  ->  50 passed, 0 failed
S2_TEST_SUITE              PASS   pytest tests/            -> 285 passed, 0 failed
```

The sealed validator asserts **seal-time** state, including
`state: S2 NOT AUTHORIZED`, which was true when Aaron sealed S1. It is now run
against the state it was sealed with — extracted by `git archive` into a
temporary directory, touching nothing — where it passes cleanly. It is not
edited, and `PROJECT_STATE.md` is not made to lie to satisfy it.

## 8. Implementation inventory

23 modules in `r1/` plus two tools. New since r1: `ledger.py` (the operational
chain), `dev_adapter.py` (the real loader), `auxiliary.py` (A1),
`build_identity.py` (the attested executable identity), and
`tools/validate_seal_snapshot.py`.

Leakage safety remains structural: nothing reads a bar except through a window
that refuses out-of-window minutes — `SignalWindow` (≥ 08:32), `TradeWindow`
(< 08:33), `TrailingHistory` (≥ the current date).

## 9. Tests

```
285 tests, 21 files            285 passed, 0 failed
```

Guards demonstrated able to fail against fabricated poisoned fixtures: the
sealed contract (12 mutations) · L-3 · L-8 (parameter scan and constants home) ·
L-10 · the OD-3 independence proof · C1 invariance · ledger edit, deletion,
reordering and forged parent · every adapter fail-closed branch · A1 future
leakage.

Forbidden categories did not run: no real Primary, no real event P&L, no real E4
over the 252, no real C2 dispersion, no OD-3 gate, no bootstrap of real
outcomes, no real verdict, no IV, no Lockbox.

## 10. Known limitations

1. Synthetic fixtures test the engine's logic, never market realism.
2. `vol_state` terciles use an order-statistic cut where the seal says only
   "tercile".
3. The DBN decode branch is exercised through a mocked decoder; its first
   contact with a real `.dbn.zst` file will be the S3 run, by design and by
   authorization.

## 11. Implementation-level resolutions of sealed ambiguities

Unchanged from r1, and none changes a sealed rule: (1) C1 is held to the
Primary's own bar; (2) the interval is two-sided percentile 95 %, because sealed
C.2 speaks of a half-width; (3) the three sealed seeds run as a stability set
with the primary interval pooled over them; (4) no invented threshold for
"materially shrank n" — now superseded by the RUN_INTEGRITY_FAILURE rule in §6.

## 12. S3 pre-run input preflight — recorded, not executed

The first real Development archive access happens **only** under S3 PRE-RUN
INPUT PREFLIGHT, before `RUN_STARTED`. It may verify exactly: the authorized
data role · vendor manifest identity · per-file sha256 · DBN/schema
compatibility · timestamp retrieval · structural event universe reproduction
= 252. It may **not** compute real `R_init`, E4, C2 dispersion, event P&L or the
Primary outcome. If the adapter cannot read the authoritative archive exactly:
`RUN_INTEGRITY_FAILURE`, and **STOP before trial consumption**. This preflight
was not performed.

## 13. Remaining items for S3

Nothing blocks S3 authorization.

1. Point the adapter at the real archive and pin its manifest sha256 into the
   run identity.
2. Publish `POST_SEAL_SIGNAL_DEFINED_N` and the E4 count as the first
   outcome-adjacent act (sealed S.3).
3. Run the OD-3 gate on real C2 dispersion; the packet decides nothing — Aaron
   does.
4. Issue the run token, append `RUN_STARTED` to the operational ledger (that row
   consumes the trial), and separately issue the reveal token.

---

```
SEALED_REGISTRY_MODIFIED    = NO
REAL_E4_EVALUATED           = NO
REAL_C2_DISPERSION_COMPUTED = NO
OD3_POWER_GATE_RUN          = NO
R1_PRIMARY_OUTCOME_COMPUTED = NO
R1_OUTCOME_INSPECTED        = NO
INTERNAL_VALIDATION_ACCESSED= NO
LOCKBOX_ACCESSED            = NO
TRIAL_CONSUMED              = NO
S2_BUILD_COMPLETE           = YES
S3_STARTED                  = NO
```
