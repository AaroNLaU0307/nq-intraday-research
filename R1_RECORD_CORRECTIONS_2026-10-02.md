# R1 — record corrections 2026-10-02 (CP-AUDIT-01)

```
RECORD_TYPE   = RECORD_CORRECTION (closed lineage; new dated file only)
LINEAGE       = R1 (nq-event-diffusion-research), lifecycle STOP since r1-final
CORRECTS      = records at commit 18639eea08ae89fa905866e8427caa48e4411d53 (tag r1-final)
AUTHORITY     = delegate decision D-R2-2026-10-02-01 (Fable 5.1 delegate), items R1-a..R1-g;
                logged verbatim in nq-letf-rebalancing-research/DECISION_LOG.md §2.8
FINDINGS      = CP-AUDIT-01 R1 report, sha256 d617e1da16d450e41a39420ad7c3071bc501e0ca22455c9aa3623684a9bd0ffc,
                persisted at audits/2026-10-01_CP-AUDIT-01_R1.md (this repository)
WRITER_LEASE  = record-correction lease held by the R2 builder session (Claude Opus 5.5 /
                Claude Code) as the only writer of R1 records for this repair, declared here
                on first write (2026-10-02). Lease check before writing: clean tree, no remote,
                no lock, no file modified since 2026-09-18, no live session holding R1.
VERDICT       = UNCHANGED. R1_FINAL_VERDICT = INSUFFICIENT_EVIDENCE; Axis 1
                PREDICTIVE_EFFECT_UNRESOLVED; Axis 2 MECHANISM_SPECIFICITY_NOT_ESTABLISHED;
                KB claim_status unresolved. No trial consumed; no re-bootstrap of the Primary.
```

## 0. How to read this file, and what it does not touch

Every correction below is carried in this new file. Nothing sealed, digest-bound or
attested is edited: not the sealed preregistration (sha256 `49267deb…`), not
`R1_SEALED_ERRATA.md` (sha256 `e89d8f4c…`, bound at `R1_S3B_RUN_IDENTITY.json:25` and
`R1_S2_BUILD_ATTESTATION.json:50`), not `runs/`, not `R1_EXECUTION_LEDGER.md` (sha256
`9d14fb33…`; no ledger row is added — `r1/ledger.py` has no correction event type), not
`R1_FINAL_CONTROLLER_SNAPSHOT.json` (sha256 `c15842f5…`), not `artifacts/R1_S4_VERDICT.json`
(sha256 `cf7511a3…`), not the KB proposal (sha256 `9ed6b2c8…`), not the run identity, not
`r1/*.py` (rollup `3f64307d…`), and no tag.

**`PROJECT_STATE.md` keeps its r1-final bytes** (sha256
`344de2afa9eb85ea7cc78311511d1dee5e554d61fbb24558dd5a4385fa110717`, pinned at ledger seq 13
and in the snapshot) — delegate decision R1-b. Where this file corrects a PROJECT_STATE line,
this file governs; nothing is added to PROJECT_STATE.

The one code change is the IMPLEMENTATION_FIX in the unsealed `tools/validate_state.py`
(§2.10). The one new tool is `tools/r1_analysis_extension_2026_10_02.py` (§3).

All eleven accepted findings were REPRODUCED by the audit; one-vote items are accepted as
record corrections (D-R2-2026-10-02-01). Line numbers are at 18639ee.

## 1. Accepted findings — index

| id | severity · votes | subject | section |
|---|---|---|---|
| R1-G01 | Medium · 3 | ledger utc column hand-entered and false | 2.1 |
| R1-G12 | Medium · 1 | sealed C1 guard vacuous by construction; misdescribed | 2.2 |
| R1-G14 | Medium · 1 | era / micro-era / event-type splits recorded as unreportable | 2.3 |
| R1-G04 | Low · 3 | PROJECT_STATE:110 and :121 false at HEAD | 2.4 |
| R1-G06 | Low · 3 | CURRENT_STATE_VALIDATION = PASS recorded while the validator failed | 2.5 |
| R1-G15 | Low · 1 | seq-12 reconciliation arithmetic does not close | 2.6 |
| R1-critic-4 | Low · 1 | spread-cost table called "digest-pinned"; no digest exists | 2.7 |
| R1-G17 | Low · 1 | run identity `trial_consumed = false`; snapshot path list | 2.8 |
| R1-G05 | Low · 1 | PROJECT_STATE says no KB card; cataloguing pending | 2.9 |
| R1-critic-1 | Low · 1 | closeout validator routes S3A to post-run checks | 2.10 |
| R1-critic-3 | Low · 1 | KB card calls R.2 tail figures unverifiable | 2.11 |

## 2. Corrections

### 2.1 R1-G01 — the ledger utc column records nominal labels, not observed times

Location: `R1_EXECUTION_LEDGER.md:22-36` (utc column, rows 1-13);
`R1_FINAL_CONTROLLER_SNAPSHOT.json:4` (written_utc); `r1/ledger.py:145`, `:156`
(caller-supplied utc). Contradicted wording: `artifacts/R1_S4_VERDICT.json:141`,
`artifacts/R1_S4_KB_FINDING_PROPOSAL.yaml:79-80`, KB card `:77-78`.

- All 13 ledger `utc` values and the snapshot's `written_utc` are **hand-supplied nominal
  labels, not observed times**. Every stamp ends in `:00`; `append_event` uses the machine
  clock only when the caller passes no utc (`r1/ledger.py:156`).
- No single clock or timezone fits them. Ledger time minus the first commit containing each
  row (committer UTC), rows 1-13: −15.82, −15.74, +7.68, +8.31, +8.86, +8.90, +9.21, +9.29,
  +9.71, +7.73, +7.82, +7.90, +8.40 h. Read as +08:00 local time, rows 1-2, 4-9 and 13 are still
  impossible. Each row's SHA-bounded write window runs from the newest commit it quotes to the
  commit that introduces it; rows 3 and 4 imply disjoint clock offsets (+7:40:32 to +7:40:52;
  +8:18:49 to +8:20:20).
- Row 8's stamp `2026-09-18T02:05:00Z` is inside digest `ed5d5ec5…`, which the run identity,
  committed 2026-09-17 16:47:28Z, binds: the string existed about 9.3 h before the instant it
  claims. GENESIS (00:00Z on 2026-09-17) predates the seal commits it names (14:20Z, 14:21Z)
  and equals the fixture literal at `tests/test_ledger.py:30`. The snapshot's written_utc
  (03:45Z on 2026-09-18) postdates its own commit (19:16:06Z on 2026-09-17).
- **The machine run time is the sealed bundle's `written_utc` 2026-09-17T16:46:12Z**
  (`runs/R1-S3B-001/sealed_r1_outcome.json`, stamped by `r1/outcome_seal.py:86`).
- **Orderings provable from bytes:** S3-A committed at 16:18:11Z, before the bundle; the verdict
  values stored in the bundle at 28ed268, before any reveal row; the row-8 digest bound in the
  run identity.
- **Orderings resting only on the seq order the builder asserted:** the OD-3 decision,
  RUN_STARTED and the bundle, all inside 28ed268; the reveal rows inside 18639ee.
- The times of Aaron's acts have no in-repository record.
- "The OD-3 decision was made before any outcome existed" rests on ledger sequence, not on
  time.

Not raised again (examined, not separately verified): the unkeyed hash chain could have been
computed at any time (rows 1-8 existed by 28ed268; rows 10-13 are bounded only by the
closeout commit); `run_study` never reads the ledger. Refusing caller-supplied utc belongs only
in a future lineage's code.

### 2.2 R1-G12 — the sealed C1 guard is vacuous by construction (narrowed)

Location: `R1_S1_PREREGISTRATION_SEALED.md:948-955` (K.1), `:1047` (M.1 guard);
`r1/pipeline.py:19-24`, `:129-135`; `S2_BUILD_REPORT.md:214-215`;
`tests/test_pipeline_synthetic.py:108-121`; `artifacts/R1_S4_VERDICT.json:91-95`;
`artifacts/R1_S4_KB_FINDING_PROPOSAL.yaml:58`, `:93-94`; KB card `:46`, `:94`.

- With fair-coin signs E[s] = 0, so **E[C1 draw mean] = −C_base = −$3.99 by construction**, on
  any data. The sealed guard therefore clears M only with negligible probability (about 252
  sigma on R1's data) and **cannot detect the drift confound K.1 assigns it**.
- The S2 wording "held to the Primary's own bar" (`S2_BUILD_REPORT.md:214-215`;
  `r1/pipeline.py:19-24`) actually describes a Monte-Carlo interval over 10,000 draw-means
  (half-width about $0.06, against the Primary's $4.91).
- S4's and the KB's "NOT_RECOVERABLE" / "not reportable" should read: **not persisted;
  recoverable by deterministic replay from the sealed records — `c1_clears_m = False` under
  seeds 7, 13 and 31; verdict invariant.** The replay values are in §3.2.
- The C1 seed and draw arguments actually used at S3-B were not recorded. The draw statistics
  rest on the default seed 7 (`contract.bootstrap_seeds[0]`) and draws = 10,000; the boolean
  does not depend on the seed.
- Descriptive only: no verdict changes and no trial is consumed. C1 enters only the SUPPORTED
  branch, which R1's interval cannot reach; Axis 1 is UNRESOLVED either way.
- Not raised again: "cannot clear M on any data" (narrowed to "E[C1] = −C by construction;
  clearing needs a negligible-probability deviation"); the "same bar" misdescription alone is
  immaterial.
- Note for future lineages only: a drift guard needs a direction-preserving null (for example
  permuting d across events, or an always-long arm).

### 2.3 R1-G14 — era, micro-era and event-type splits are reportable (narrowed)

Location: `artifacts/R1_S4_KB_FINDING_PROPOSAL.yaml:93-94`; KB card `:93-96`;
`artifacts/R1_S4_VERDICT.json:155-163` ("not persisted" is literally true);
`R1_S1_PREREGISTRATION_SEALED.md:444-447` (D.3), `:756` (H.2), `:816-817` (I.2), `:935-936` (J);
`r1/pipeline.py:167-186`; `r1/covariates.py:126`.

- Era and micro-era follow from `date_et` alone (era by calendar year, `r1/contract.py:425-426`;
  micro-era by date ≥ 2019-05-06, sealed D.3). Event type follows from `date_et` plus the
  L-11-pinned F10 calendar (sha256 `5e92ad00…`); all 246 dates map uniquely (CPI 113, NFP 133).
  **The "cannot be reported" statements are false for these three splits.**
- The sealed H.2 / I.2 / D.3 / J descriptive reporting was not done at S4. It is now done,
  descriptively, under the ANALYSIS_EXTENSION in §3.1.
- Vol tercile, A1 per-event membership and C2/D remain genuinely unrecoverable.
- Not raised again: era as "the one that explains the precision failure" is overstated — the
  dispersion sits in a few 2020-21 events (2021-03-05 alone is 25.6% of the sum of squares);
  the C1 clause is decided under R1-G12.

### 2.4 R1-G04 — PROJECT_STATE.md:110 and :121 are false at HEAD (narrowed)

`PROJECT_STATE.md@344de2af`:

- `:110` "r1/ (22 modules) + tests/ (264 tests, all passing)" — true values: **23 `r1/*.py`
  files (counting `__init__.py`) and 285 tests** since S2_CODE_COMMIT 433e2cc (pytest collects
  285 at 433e2cc and every later commit).
- `:121` "REAL_DATA_ADAPTER = IMPLEMENTED (r1/dev_adapter.py); NOT EXECUTED on R1" — false:
  `r1/dev_adapter.py` **was executed on real Development data at S3-A**
  (`artifacts/R1_S3A_POWER_GATE.json:35`, `:136`: decoder "lazily imported by r1.dev_adapter",
  REAL_MARKET_DATA_READ = YES) and, by the L-10 single-decoder rule (`r1/invariants.py:31-32`,
  `r1/bars.py:108-110`), at S3-B. No S3-B record names the loader.
- `R1_FINAL_CONTROLLER_SNAPSHOT.json:21` lists the path `ROJECT_STATE.md`; it should read
  `PROJECT_STATE.md` (the digest map at `:163` names the file correctly).
- Not raised again: `:66` "IS_SEALED_COMMIT = NO" is true (it qualifies pre-seal commit
  8656701); lookahead-3's DST-provenance path is overstated (`_et_parts` maps 08:29 ET to
  minute 509 in both EST and EDT).

### 2.5 R1-G06 — CURRENT_STATE_VALIDATION = PASS was recorded while the validator failed

- At 7426a2f (S3-A) and 28ed268 (S3-B) the then-committed `tools/validate_state.py` (blob
  7dc4bce, identical at 433e2cc, b99e10e, 7426a2f, 28ed268) gave **48/2** (STAGE,
  OD3_POWER_GATE) and **43/7** (five stage strings, "no sealed R1 outcome file", "RUN_STARTED has
  NOT been appended"): all stale S2-era stage assertions.
- Every integrity and outcome-access check passed at both commits: 12/12 sealed digests, the
  ledger chain, executable identity 433e2cc, and at 7426a2f no outcome file and an unconsumed
  trial.
- The PASS lines at `PROJECT_STATE.md@7426a2f:87-88` and `@28ed268:96-97` were carried over
  from b99e10e without a rerun and were inaccurate. They were never the S3 gate record; the
  gates' checked substance reproduces (identity gate 14/14 at ledger seq 5, 19/19 in the 28ed268
  message, 18/18 pre-reveal at seq 10).
- **The failure began at S3-A, not at S3-B** as `tools/validate_state.py:26-30` (closeout
  version), `artifacts/R1_S4_VERDICT.json:204` and the 18639ee commit message imply.
- This note does not claim that the repaired validator re-validates S3-A at closeout; see §2.10.

### 2.6 R1-G15 — the seq-12 reconciliation does not close arithmetically (narrowed)

Location: `R1_EXECUTION_LEDGER.md:35` (seq 12); `artifacts/R1_S4_VERDICT.json:135-142`;
`artifacts/R1_S4_KB_FINDING_PROPOSAL.yaml:76-81`, `:53-54`; KB card `:73-78`.

- At sd 49.4801 and n = 246 the sealed gate formula (prereg I.3; `r1/power_gate.py:88`, `:96`)
  gives a half-width of **6.18** (1.96 × 3.1547 = 6.183), not 4.91.
- The sealed block-bootstrap SE is 2.4998 (half-width 4.9066), narrower because of the realized
  **event order**: lag-1 autocorrelation about −0.29, of which −0.161 comes from one adjacent
  pair, 2021-03-05 (−400.49) and 2021-03-10 (+237.51). Breaking that adjacency alone gives
  about 5.9-6.1; only 2 of 300 random orderings give ≤ 4.9066 (mean 6.05).
- The verdict, the observed direction and the event-day-dispersion lesson are unchanged.
- **R1's realized half-width 4.91 must not be used to calibrate future power**; plan on
  event-day sd with the iid formula.
- Not raised again: that the lesson is quantitatively wrong (dispersion is the cause; the
  ordering was a favourable fluke); that following the lesson misjudges power;
  `R1_S4_VERDICT.json:135-142` and the KB proposal are true as worded. The finder's "combine
  with era heteroskedasticity" clause is dropped (a post-result subgroup analysis).

### 2.7 R1-critic-4 — the spread-cost table was never digest-pinned (narrowed)

Location: `PROJECT_STATE.md:210-216`; `R1_DELEGATED_OWNER_DECISIONS.md:31-33`, `:123-124` (OD-5);
`R1_PREREG_MANIFEST.json:76-91`; `R1_TRIAL_REGISTRY.md:85-92`; `r1/itsf_pin.py:29-36`;
`r1/contract.py:285-306`.

- The derived per-minute spread-cost table (`spread_cost_table.csv`) was **never
  digest-pinned** in any R1 record; the OHLCV manifest (`d8d1edc7…`), the F10 calendar
  (`5e92ad00…`) and the symbology map (`85a32d44…`) were. No 64-hex digest appears within 120
  characters of "spread cost" in any of the 13 commits.
- "all … digest-pinned" at `PROJECT_STATE.md:211-216` is inaccurate for that table, and OD-5's
  digest-pinned reuse was not carried out for it.
- The operative spreads are the E.3 / G.2 transcriptions, byte-pinned through the sealed
  prereg digest `49267deb…`. M = $3.99 binds as sealed; the verdict is unaffected (EXCLUDED
  would need M above 4.9066, a spread transcription error of about 3.7 ticks or more).
- Not raised again: "the provenance of the inputs behind M cannot be checked" — the E.3 values
  can still be compared with ITSF's table; only byte identity inside R1 is missing.

### 2.8 R1-G17 — run identity `trial_consumed`; snapshot path list (narrowed)

1. `artifacts/R1_S3B_RUN_IDENTITY.json:79` `trial_consumed = false` is a **constant False by
   construction** (`r1/run_identity.py:197`; meaning stated only in
   `tests/test_roles_and_identity.py:109`). Consumption is ledger seq 8 (`ed5d5ec5…`, "THE
   FORMAL R1 TRIAL IS CONSUMED AT THIS ROW"), which the same identity binds (`:26`). The file
   stays byte-identical: the field is inside run-identity digest `bb8655821ecd…`.
2. `R1_FINAL_CONTROLLER_SNAPSHOT.json:19-25`: `:21` should read `PROJECT_STATE.md`, and the
   closeout path list omits the snapshot file itself.
3. `PROJECT_STATE.md:110` should read 23 modules / 285 tests (shared with §2.4).

Not raised again: the r1-final tag body is **accurate** — it contains none of the "No real
research has run / No R1 outcome exists" lines (those belong to the r1-s1-sealed and
r1-s2-built tag messages) and states TRIAL_CONSUMED = YES; no errata tag is added. Also
refuted: c1_seed_set [7, 13, 31] (defensible); the three keys outside the digest (bound
transitively through the ledger); pandas not recorded (no effect); "PERMANENT_RESIDUALS =
two" (matches the verdict's taxonomy).

### 2.9 R1-G05 — PROJECT_STATE still says no KB card exists (narrowed)

- `PROJECT_STATE.md:108-109` ("no KB registry card created — that is an Owner act") and `:134`
  ("NEXT_OWNER_DECISION = whether to catalogue the KB Finding proposal"): the card **was
  catalogued** at quant-research-knowledge-base commit `cdc99e1` (2026-09-18 03:35:39 +0800, 19
  minutes after r1-final); the decision is no longer pending.
- `:69` "P-6 is not applicable yet": P-6 (KB cataloguing, sealed prereg `:1181`) was discharged
  by that cataloguing.
- `:110` and `:121`: as §2.4.
- This records that the ingestion happened; it does **not** assert who authorized it — see §4.
- Not raised again: `:58` (trial-accounting pointer), `:43` (planning power table), `:66`,
  `:204` (validate_prereg's seal-time scope is disclosed) and validate_state's verdict keys are
  true as written.

### 2.10 R1-critic-1 — the closeout validator mis-routed S3A (narrowed) — IMPLEMENTATION_FIX applied

- The closeout `tools/validate_state.py` (sha256 `ec52a9f1…`, pinned at ledger seq 13 and
  snapshot `:165`) derives stage S3A (`:92-93`) but tested only `stage == "S2"` at its three
  stage-dependent sites, so S3A took the post-run branches. "Each stage asserts its own
  invariants" (`R1_S4_VERDICT.json:205`, `PROJECT_STATE.md:160-161`, `validate_state.py:32`,
  `:159`) **did not hold for S3A**: replayed on 7426a2f it gave 5 false FAILs (43/5).
- **Fix applied 2026-10-02** in the unsealed `tools/validate_state.py` (outside the sealed set
  and outside the `r1/*.py` rollup): S3A now takes the pre-run branches
  (`PRE_RUN_STAGES = ("S2", "S3A")`), and the docstring table lists S3A. Replayed on
  `git archive` snapshots with the fixed file: **b99e10e 48/0, 7426a2f 48/0, 28ed268 51/0**;
  HEAD 60/0.
- **The `ec52a9f1…` pin (ledger seq 13, snapshot `:165`) refers to the closeout bytes** of this
  file, not to the fixed version; the pin is not changed.
- No verdict, gate or decision depends on this. Not raised again: the S2-weakening half (the
  four dropped S2 literals held at every S2-era commit).

### 2.11 R1-critic-3 — the R.2 tail figures are not unverifiable

- The KB card (`:143-145`) and its commit message (`cdc99e1`) say the p90 / p99 excursion
  figures and the worst-event date "are not persisted … so they are deliberately omitted here
  rather than carried forward unverifiable". The sealed bundle (sha256 `f6ca60e2…`, one of the
  card's own source files) persists per-record `date_et` and `mae_usd`; recomputing gives
  **p10 −81.25 and p1 −199.45** (numpy/pandas default linear quantile — the 90th / 99th
  percentile of loss) and the **worst −485.75 on 2021-03-05**, exactly the S4 proposal's figures
  (`artifacts/R1_S4_KB_FINDING_PROPOSAL.yaml:111-113`).
- Only the `R1_S4_VERDICT.json` clause of the card's sentence is true. The correction is
  KB-side (§5).
- Not raised again: "omits part of a sealed-mandated disclosure" (R.2 binds R1's own report,
  which carries the figures); the R.2 text is at prereg `:1298-1302`.

## 3. ANALYSIS_EXTENSION (descriptive) — D-R2-2026-10-02-01 R1-c

```
TYPE        = ANALYSIS_EXTENSION, bounded, prespecified, descriptive, post-STOP
AUTHORIZED  = delegate decision D-R2-2026-10-02-01 (R1-c)
INPUTS      = runs/R1-S3B-001/sealed_r1_outcome.json (sha256 f6ca60e2…; date_et, direction,
              y_net_usd), the sealed contract, and the L-11-pinned F10 calendar
              (sha256 5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c,
              digest-checked by r1.events.load_calendar). No market data.
COMMAND     = python tools/r1_analysis_extension_2026_10_02.py
GUARDRAILS  = D.2 kept: CPI / NFP are reported side by side; neither is promoted or
              a second primary. D.3 kept: micro-era is its own axis; the pre-2019-05-06
              rows are counterfactual micro execution, never historical micro performance.
NOT DONE    = no verdict change; no trial consumed; no re-bootstrap of the Primary; NOT the
              block-10 sensitivity interval; no vol-tercile, A1 or C2/D value (unrecoverable).
POST_RESULT_RESEARCH = this descriptive extension only; R1 lifecycle stays STOP.
```

### 3.1 Sealed descriptive splits (Base arm, y_net USD per event per 1 MNQ; sd with ddof = 1)

| split | n | mean | sd |
|---|---:|---:|---:|
| pooled | 246 | −8.7685 | 49.4801 |
| era 2010-2013 | 74 | −5.1859 | 13.2977 |
| era 2014-2017 | 82 | −3.1241 | 18.8672 |
| era 2018-2021 | 90 | −16.8567 | 78.5141 |
| micro-era counterfactual (< 2019-05-06) | 188 | −5.7772 | 20.8853 |
| micro-era actual (≥ 2019-05-06) | 58 | −18.4641 | 94.6949 |
| event type CPI | 113 | −1.3174 | 48.3868 |
| event type NFP | 133 | −15.0990 | 49.6961 |

Descriptive only. Every era mean is negative. The dispersion is concentrated in a few
2020-21 events, so era is a coarse proxy for it. S4's per-1-MNQ statements pool both
micro-eras.

### 3.2 C1 replay (R1-G12), with seed disclosure

Replay: the sealed `run_c1` sign draws (`random.Random(seed)`, `rng.choice((1, -1))` per event
per draw, 10,000 draws), evaluated arithmetically from the records (no stop, symmetric frictions:
y(s) = s·G − C with G = d·(y + C), C = $3.99; reproduces every sealed y_net_usd, max error
3.6e-15), then the sealed `bootstrap_interval` over the draw means and `clears(M = 3.99)`.

| seed | mean of draw means | interval | half-width | clears M |
|---|---:|---|---:|---|
| 7 (default; used at S3-B if the default applied — not recorded) | −3.9265 | [−3.9888, −3.8650] | 0.0619 | False |
| 13 | −4.0038 | [−4.0663, −3.9397] | 0.0633 | False |
| 31 | −4.0105 | [−4.0714, −3.9495] | 0.0610 | False |

Signal directions: 140 long, 106 short (the audit's "140 up / 106 down"). Undirected
ref-to-ref moves G: 132 up, 4 zero, 110 down; mean +$2.8679.

## 4. UNKNOWN (critic gaps 3 and 6) — D-R2-2026-10-02-01 R1-d

```
S4_FINAL_VERDICT_GIVEN_BY       = UNKNOWN  (whether Aaron personally gave the S4 final verdict,
                                            or authorized only its construction; only
                                            builder-written records exist)
KB_INGESTION_cdc99e1_AUTHORIZED_BY = UNKNOWN (no authorization record in either repository)
```

Not reconstructed.

## 5. KB card annotations (R1-g) — exact text

Card: `quant-research-knowledge-base/registry/findings/finding.nq-event-diffusion.r1-cpi-nfp-continuation-unresolved.yaml`
(as ingested at KB `cdc99e1`). Applied as one dated annotation appended to the card's `notes`,
in a separate local KB commit (recorded in §7), without editing the existing text:

```
CORRECTION 2026-10-02 (nq-event-diffusion-research/R1_RECORD_CORRECTIONS_2026-10-02.md;
CP-AUDIT-01; delegate decision D-R2-2026-10-02-01). Verdict and claim_status unchanged.
(1) test_statistic "C1_GUARD NOT_RECOVERABLE" and limitations "c1_clears_m and the C1 draw
statistics ... not reportable": c1_clears_m was not persisted, but it replays deterministically
from the sealed records to False under seeds 7, 13 and 31 (seed 7: mean of draw means -3.9265,
interval [-3.9888, -3.8650]). The sealed C1 guard has E[draw mean] = -$3.99 by construction, so
it clears M only with negligible probability and cannot detect the drift confound it was meant
to (R1 corrections §2.2, §3.2).
(2) limitations "vol-tercile / era / micro-era disclosures, CPI-versus-NFP event-type labels ...
not reportable from the bundle": false for era, micro-era and event type, which follow from
date_et and the L-11-pinned calendar. Descriptive values (n, mean): era 2010-13 74, -5.19;
2014-17 82, -3.12; 2018-21 90, -16.86; micro-era actual (>= 2019-05-06) 58, -18.46 and
counterfactual 188, -5.78; CPI 113, -1.32; NFP 133, -15.10 -- reported side by side, no
promotion (D.2), micro-era on its own axis (D.3). Vol tercile, A1 membership and C2/D remain
unrecoverable (R1 corrections §2.3, §3.1).
(3) notes "(The R1 S4 KB proposal also quotes p90 and p99 excursion figures and a date for the
worst event; ... omitted here rather than carried forward unverifiable.)": these are not stored
as summary values but are deterministic from the sealed bundle's per-record mae_usd and
date_et: p10 -81.25, p1 -199.45 (linear quantile; the 90th / 99th percentile of loss), worst
-485.75 on 2021-03-05 -- matching the S4 proposal. This supersedes the statement in the cdc99e1
commit message (R1 corrections §2.11).
(4) limitations "the OD-3 decision was made before any outcome existed": this rests on ledger
sequence, not on time; the ledger utc stamps are hand-supplied nominal labels (R1 corrections
§2.1).
```

## 6. NON-BLOCKING BACKLOG (refuted-but-factual) — D-R2-2026-10-02-01 R1-e

None holds the lineage; each is record hygiene or future-lineage work. They were refuted as
findings and are recorded so nobody re-raises them as defects.

| id | item | why it is not a finding |
|---|---|---|
| R1-BL-01 (G02/G03) | The S3-A / S3-B driver was never committed; the `run_study` arguments used at S3-B are unrecorded; code docstrings overstate L-5/L-6 enforcement (`r1/invariants.py:184-187`) | L-6 verified after the fact (universe digest `f0f08a62…` before the outcome; bundle dates = universe minus E4); inputs pinned; the verdict is identical across all 48 argument combinations tried; v1 called run tooling a capability, not an obligation |
| R1-BL-02 (G07) | The L-7 outcome-permutation test is a determinism / pin check, its helper an uncalled tautology; `r1/invariants.py:7-8` and `tests/test_invariants.py:1` claim a mutation test for every invariant | the inclusion set is pinned before any outcome; any r1 edit trips executable identity; no governance record cites the test |
| R1-BL-03 (G10) | The sealed I.1 block-10 sensitivity interval was never computed or reported | no record claims it ran; S4 scope excluded re-bootstrapping. Not computed under this extension (D-R2-2026-10-02-01 R1-c) |
| R1-BL-04 (G13) | The sealed I.3 z-constants (1.645 / 2.486) are calibrated for a one-sided 5% test while the sealed interval rule is effectively one-sided 2.5% | the inconsistency is inside the seal; S2 implemented both passages verbatim; UNRESOLVED under every reading |
| R1-BL-05 (G18) | Nine verdict-relevant mutations survive the 285-test suite (no test of outcome-bearing values, bootstrap or verdict numerics) | executed bytes are the attested ones and correct; relevant only to any reuse of the engine |
| R1-BL-06 (G08) | The integrity validators take reference digests from mutable HEAD records; a coordinated file-plus-digest forgery passes them | no binding text claims they resist one; T.3 anchors the seal in commits and the tag; `git diff --quiet r1-final` exposes such edits |

Also refuted, not backlogged: R1-G09 (E1 FOMC exclusion applied exactly as sealed), R1-G11
(the S4 bootstrap replay was the sealed S4 recomputation, not a re-bootstrap), R1-G16 (seat
attribution consistent and hash-bound), R1-critic-2 (the R.2 per-event excursion test is on its
declared basis; the account path is sealed out of scope).

## 7. Mechanical checks after this repair

Recorded at the commit that adds this file (expected per R1-f; actual results are in the
CP-REPAIR-01 checkpoint message and in §8 when appended):

```
pytest tests                      285 passed
tools/validate_state.py           60 passed, 0 failed
tools/validate_seal_snapshot.py   PASS
psmv/validate_prereg.py           183 passed, 2 FAILED (the same two standing seal-time
                                  state assertions: "S2 NOT AUTHORIZED", "outcome reveal not
                                  granted")
git diff --stat r1-final          this file, tools/validate_state.py,
                                  tools/r1_analysis_extension_2026_10_02.py,
                                  audits/2026-10-01_CP-AUDIT-01_R1.md
```
