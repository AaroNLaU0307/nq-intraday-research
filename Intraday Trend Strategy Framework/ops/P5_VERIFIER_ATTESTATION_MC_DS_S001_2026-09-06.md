# P5 INDEPENDENT VERIFIER ATTESTATION — MC-DS-S001 (N09 supplement)

```
RECORD_TYPE=VERIFIER_ATTESTATION
SUPPLEMENT_ID=MC-DS-S001
VERIFIED_OBJECT=DAY_STRATA_SUPPLEMENT.json (sealed 2026-09-05T17:08:10Z run directory)
VERIFIER_SEAT=independent verifier, Claude Fable 5.1, FRESH TOP-LEVEL SESSION opened 2026-09-06
PRODUCING_SESSION=NOT this session (N09 production was an Opus 5 builder session on 2026-09-05)
CONTRACT=ops/DECISION_PACKET_N00_AND_ND1.md §D.3.2 P5 / F2v, as transcribed in src/itsf/mc/supplement_contract.py
FRAMEWORK_HEAD_AT_VERIFICATION=3df1656f105b9314235bd28957336a7dec4bde05 (worktree clean at start)
REGISTRY_READ_ORDER=BLIND_FIRST (registry opened only after the blind results were written and hashed)
CONCLUSION=FAIL — headline_replay_identity=FAIL; contract path is F2v (SUPPLEMENT_VERIFICATION_FAILED), failure_code=headline_replay_mismatch
NOTHING_APPENDED=YES (registry untouched; sealed and archive bytes untouched; no framework file edited)
```

## 1. Independence

- This is a fresh top-level session. It did not run, prepare, or seal the N09 supplement, did not consult the producing session, and did not use any number produced by that session as an input.
- Every digest, count, and replay below was recomputed here from bytes on disk and from the framework source at the HEAD named above.
- Order of work: all independent computations were completed and written to `ops/P5_VERIFY_BLIND_MC_DS_S001_2026-09-06.json` (sha256 `1e4e45cfe9d4ad222d2c87a470a3cec18d4fe888171aef7bcd2170d77299a052`) BEFORE the registry file was opened. The P4 row was then read and compared claim by claim.

## 2. Verification object and source inputs

| Item | Path | Fact recomputed here |
|---|---|---|
| Production copy | `C:\Users\Aaron\quant-data\itsf-runs\supplements\MC-DS-S001_20260905T170810Z\DAY_STRATA_SUPPLEMENT.json` | sha256 `f2ecbb9c77d3f2d7d2b555f50cadb6bcafdc979bdcfa4ac5a985e3cf33b9a911`, 233387 bytes |
| Archive copy | `C:\Users\Aaron\quant-data\itsf-runs-archive\supplements\MC-DS-S001_20260905T170810Z\DAY_STRATA_SUPPLEMENT.json` | sha256 identical, bytes identical (`==` on full contents) |
| Source authority | sealed S0-T001 bundle, `C:\Users\Aaron\quant-data\itsf-runs\runs\S0-T001_20260813T170432Z\` (14 files) and its archive mirror | every file re-hashed in both roots; both equal the code-pinned blind custody table (`ops/S0_T001_POST_RUN_ATTESTATION.md`, pinned sha `d839b965…`) |
| Frozen event table | `gate1/f10_event_calendar/f10_events.csv` | sha256 `5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c` (equals the S0-time preflight hash) |
| Framework code | `src/itsf/s0/gridmix.py`, `dataset.py`, `context.py`, `study.py` | byte-identical between the S0 commit `876c1b74…` and HEAD (git diff empty); numpy 2.5.0 both then and now |

NOT read: any Development DBN payload (forbidden for this seat); any path on `ops/OUTCOME_CARRYING_ARTIFACTS.json`; `ops/outcome_quarantine/**`; either exposure ledger.

## 3. Method

1. Bytes: sha256 of both copies; byte equality; directory contents.
2. Schema: the sealed object re-validated with the framework's own seal-side validator; the sealed bytes shown to equal the canonical serialisation of the parsed object.
3. Rows digest: recomputed with an independent canonical-JSON implementation (sorted keys, compact separators, ASCII) over the 2842 rows.
4. Source authority: the sealed S0-T001 bundle prepared through the project's gate-first entry (`real_input.prepare_supplement_mc_input`, ten-check custody battery), a `SupplementAuthority` derived from it, and the builder inputs (`expected_day_set`, `binding`) obtained through `supplement_build_inputs`. Day-universe digest, bundle-table digest and source-input identity were also recomputed by hand from their documented preimages.
5. Event column: re-derived from the frozen F10 CSV through `EventCalendar.encode_f10` and the ruled `F1_five_stratum_ir12_18_vocab` mapping, exactly as the N09 producer constructs its calendar.
6. Headline replay identity: the S0 sealed report stores, for each of 16 (θ × engine × scenario) feasibility grids, 63 (q, r) cells, each with the headline (k = 0) draw per master seed — selected TP/FP dates, per-stratum allocations, day markers — plus the digest of every one of the 200 repeats. Using the supplement's (year, vol_stratum, event_stratum) per day as the stratification, the sealed TP/FP day sets per θ, and the frozen gridmix primitives (unchanged since the S0 commit), each headline draw was regenerated and compared field-by-field; the same was done end-to-end through `gridmix.build_grid`. A cell counts as reproduced only if all three seeds match on every field and the repeat digest equals the sealed one.
7. Only structural keys of `S0_REPORT.json` were accessed (day universes, selected dates, allocations, markers, digests, method strings). No P&L, precision, F-expected, verdict, spread or exposure value was read, printed or stored.

## 4. Results (all recomputed here)

| Check | Outcome |
|---|---|
| production/archive byte identity | IDENTICAL |
| sealed object schema, binding schema, row vocabulary, n_rows == 2842 | PASS |
| sealed bytes == canonical serialisation | PASS |
| rows_digest recomputed independently | `12ceea50a5ad7224acde517a432eac8f7fc6636c69a2898055cf6a5725ec08a5` — reproduced |
| binding == binding re-derived from the sealed S0-T001 bundle | PASS (trial_id S0-T001, authorized_commit `876c1b74131b4ab1a89dce433ecce646ba481f8c`, method_version `mc-freeze-v1`) |
| day universe identity | rows cover the re-derived sealed universe exactly (0 missing, 0 extra); digest `5ddff4fb029df6527daaf17b29bdcffe08241fa93ffe7b8e4aec2c9401f98230` reproduced by hand |
| source input identity | `2fac9000dbf3806c7743a8207b79373d8c5ba7cad3796052803b0e272516184d` reproduced from the pinned prepared-identity bytes |
| bundle table digest | `eba3bf056897323cb663a9c5707d968859f328d2c1814f6ae7b9e3da776315c9` reproduced from my own file hashes |
| S0-T001 sealed bytes in place | run dir and archive mirror: 14/14 files, all digests equal the custody table (no `s0_sealed_bytes_moved`) |
| event_stratum column vs frozen F10 calendar as the N09 producer builds it | 0 mismatches over 2842 days |
| year column | PASS |
| **headline replay identity** | **FAIL — 0 of 1008 cells reproduced (16 grids × 63 cells, all feasible); 0 of 3024 (cell, seed) headline rows identical; end-to-end `build_grid` over the supplement's strata: 0 of 189 rows identical per grid** |
| supplementary full K = 200 repeat digests | 0 of 3024 seed-sets identical (same cause) |

```
rederivation_reproduced   = YES   (scope: rows digest, binding, day universe, source-input identity,
                                   custody, event column — every re-derivation this seat was permitted to run;
                                   a from-bars re-derivation of the vol column was NOT performed, DBN reads being forbidden)
headline_replay_identity  = FAIL
n_cells                   = 0     (headline cells reproduced; 1008 attempted)
```

## 5. The finding, isolated and confirmed

The replay mechanism is not the cause: per-stratum TP availability under the supplement's strata gives the identical RNG-free `allocation_tp` to the sealed one in 81 of 189 rows, the stratum-key sets agree, and draws overlap in most days but not all — the signature of a few days carrying a different label. From the sealed selections I inferred exactly which days, then applied those labels to the supplement's strata and replayed everything again:

```
with 8 labels restored to what the S0 run used:
  headline rows identical         3024 of 3024   (16 grids x 63 cells x 3 seeds)
  full K=200 repeat digests       3024 of 3024 seed-sets  (604,800 draws, byte-identical digests)
recorded in ops/P5_VERIFY_DIAG_MC_DS_S001_2026-09-06.json  sha256 507c7ffdf62d55f1f937d380fd976aca4ed46acd786b9bf52ac271d23cf6b74f
```

The eight days whose stratum in the sealed supplement differs from the stratum the S0-T001 run actually stratified on:

| trade_date | supplement (year, vol, event) | S0 run used | axis |
|---|---|---|---|
| 2012-11-26 | 2012, T2, none | 2012, T3, none | vol |
| 2012-11-27 | 2012, T2, none | 2012, T3, none | vol |
| 2013-05-06 | 2013, T2, none | 2013, T3, none | vol |
| 2014-10-20 | 2014, T2, none | 2014, T3, none | vol |
| 2015-12-10 | 2015, T2, none | 2015, T3, none | vol |
| 2019-10-11 | 2019, T2, FOMC | 2019, T2, none | event |
| 2020-03-03 | 2020, T3, FOMC | 2020, T3, none | event |
| 2020-03-23 | 2020, T3, FOMC | 2020, T3, none | event |

Facts on the record about the two axes (cause trail, not adjudication — this seat rules on identity only):

- Event axis: the three dates are on the S0 run's frozen IR-13 list `UNSCHEDULED_FOMC = ("2019-10-11", "2020-03-03", "2020-03-15", "2020-03-23")` (`scripts/s0_real_run.py`), which S0 passed into its `EventCalendar` so those days encode as `none`. The N09 producer's `production_inputs.build_event_calendar` deliberately leaves `unscheduled_fomc_dates` empty, so the same F10 rows (flagged `is_fomc_statement_day=true`) encode as `FOMC`. The supplement therefore matches the producer's own calendar (my check 5) but not the calendar S0 stratified on.
- Vol axis: all five differences are T2 in the supplement where S0 had T3, consistent with a shifted T2/T3 tercile cut; the cause (session-close handling, roll handling, or input differences in the vol20 series) was not determined by this seat and cannot be without the forbidden Development reads.
- Completeness: after restoring these eight labels every draw-relevant stratum reproduces exactly. A further label difference could only hide in a stratum that never receives an allocation at any (q, r, seed, k); none was needed to explain the sealed bytes.

## 6. Comparison with the P4 claims (read AFTER the blind results were fixed)

Registry: `C:\Users\Aaron\quant-data\itsf-registry\ops\TRIAL_REGISTRY.md`, sha256 `a56d15ab171b3c7c4c10f60caffa687a205b83ec0e6039191dd9243aa0754f9e`, 10273 bytes, 47 lines, repo HEAD `7e92be6c…`, working tree clean; equals `WITNESS_P4_APPENDED_2026-09-05.json`. Chain for MC-DS-S001 resolves with `problem == ""`: `P1, P2, P2S, P2, P2S, P2, P2S, P2, P3, P4`; started=True, live authorizations 0, retired=False, terminal="", state AWAITING_INDEPENDENT_VERIFICATION. Highest global sequence 21.

| P4 field (claim) | claimed | recomputed here | match |
|---|---|---|---|
| sealed_sha256 | f2ecbb9c… | f2ecbb9c… | YES |
| rows_digest | 12ceea50… | 12ceea50… | YES |
| day_universe_digest | 5ddff4fb… | 5ddff4fb… | YES |
| source_input_sha256 | 2fac9000… | 2fac9000… | YES |
| method_version | mc-freeze-v1 | mc-freeze-v1 | YES |
| n_rows | 2842 | 2842 | YES |
| archive | archive_ok | archive byte-identical | YES |
| commit cell | 3df1656 | binding commit is the S0 commit 876c1b74… (source-side custody, as the runner documents); row commit is the run HEAD | consistent |

Every P4 claim is true. P4 never claimed replay identity; that is exactly what P5 exists to establish, and it does not hold.

## 7. Conclusion and contract path

- `headline_replay_identity = FAIL`, therefore no P5 row may be emitted (`p5_claims_failed_verification` would refuse it, and the seat will not manufacture a PASS).
- The ratified path after P4 on a failed independent verification is **F2v `SUPPLEMENT_VERIFICATION_FAILED`** (NUMBERED, verifier actor, 40-hex commit, `failure_code: headline_replay_mismatch`, `sealed_artifact_deleted: NO`, `supersession_required: YES`), whose only successor is F3 and then T1 with a new supplement id. The candidate row and its memory-only parser preflight are in `ops/F2V_CANDIDATE_MC_DS_S001_2026-09-06.md` and `ops/P5_VERIFY_REGISTRY_MC_DS_S001_2026-09-06.json`; the row's `detail` cites this file's sha256.
- The sealed artifact was NOT deleted, moved or modified. The registry was NOT appended. No Development data was read. N10/N11 were not started.

## 8. Seat exposure self-report

This seat opened no quarantined path and saw no verdict token, cumulative exposure count, endpoint spread value, zero-direction cell count or feasibility assertion. It loaded `S0_REPORT.json` into memory and accessed structural keys only, parsed the eight `MC_HANDOFF_*` files through the consumer battery (record KEYS; values never inspected), and read the frozen F10 table. The seat-axis ledger entry for this dispatch (`ops/REVIEWER_EXPOSURE_LOG.md`) is owed by the dispatching side and was not written by this seat.

## 9. Files produced by this seat (all under `ops/`, none committed)

```
P5_VERIFY_BLIND_MC_DS_S001_2026-09-06.py     the blind verifier (script)
P5_VERIFY_BLIND_MC_DS_S001_2026-09-06.json   its results, sha256 1e4e45cfe9d4ad222d2c87a470a3cec18d4fe888171aef7bcd2170d77299a052
P5_VERIFY_DIAG_MC_DS_S001_2026-09-06.json    the eight-label confirmation replay, sha256 507c7ffdf62d55f1f937d380fd976aca4ed46acd786b9bf52ac271d23cf6b74f
P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md   this file
P5_VERIFY_REGISTRY_MC_DS_S001_2026-09-06.py / .json   registry comparison + F2v memory-only preflight
F2V_CANDIDATE_MC_DS_S001_2026-09-06.md       the candidate row, verbatim, awaiting Aaron
```
