# PROJECT_STATE — nq-letf-rebalancing-research (R2)

**This file records STATE, never workflow authority.** Workflow authority is
`../QUANT_WORKFLOW_VNEXT.md`.

Last updated: 2026-09-22 (Morningstar routing request sent and official free-trial form
successfully submitted; access activation remains unverified. B-3 unchanged and still
open).

```
PROJECT             = nq-letf-rebalancing-research
LINEAGE             = R2
RESEARCH_QUESTION   = Does the aggregate daily-reset rebalancing demand of Nasdaq-100
                      leveraged and inverse ETFs leave a mechanically predictable
                      late-day footprint that transmits into Nasdaq-100 index futures?
STAGE               = S0 (DATA FEASIBILITY = PASS / CLOSED) — PRE-S1, but with an
                      OPEN pre-S1 timing blocker (B-3). S1 design is NOT authorized
                      and R2 is NOT ready for S1 design while B-3 stands.
ACTIVE_HYPOTHESIS   = NONE — no hypothesis is stated, and none may be stated before S1
LANE                = n/a  (no claim is emitted at this stage)
SCOPE               = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY
                      universe: QLD, QID, PSQ, TQQQ, SQQQ
                      generic momentum substitute: FORBIDDEN. R2 distinctness must
                      come from K_t / L_t or an equivalent magnitude/composition
                      channel beyond return; if that cannot be established
                      prospectively, PARK R2.
DATA_GRANT          = R2 lineage-specific grant over the existing local NQ Development
                      archive (GLBX-20260727-DL3BEBCHJA, NQ.v.0 ohlcv-1m,
                      2010-06-06 -> 2022-01-01 exclusive). GRANTED, NOT YET EXERCISED —
                      no file in that archive has been decoded or inspected by R2.
                      Public ProShares/SEC sources used in feasibility are recorded in
                      R2_DATA_SOURCE_AUDIT.md and R2_G3_PUBLICATION_TIMING_REPORT.md.
TRIAL_ACCOUNTING    = MORNINGSTAR_DIRECT_FREE_TRIAL_APPLIED. Official form confirmation
                      received 2026-09-22; login credentials / usable access are not yet
                      verified. No trial has been consumed.
OUTCOME_EXPOSURE    = NONE. No NQ future-outcome relationship has been inspected,
                      computed, plotted or estimated in this lineage.
CAUSAL_TIMING       = G3_HISTORICAL_STATUS        = PARTIAL
                      HISTORICAL_PIT_SAFE_START    = 2014-03-26
                      PRE_SAFE_PERIOD              = UNRESOLVED
                                                     (2010-06-06 -> 2014-03-25)
                      FULL_SAMPLE_AUM_AVAILABLE_BY = UNKNOWN
                      SAFE_PERIOD_AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN
                                       (09:30 ET on t) — TYPICAL, NOT GUARANTEED,
                                       see G-11
                      EVIDENCE_LEVEL               = B
                      S1_TAU_CONSTRAINT = tau > 09:30 ET on trading day t,
                                       applicable only inside the PIT-safe period
                      (a mechanical constraint only — tau is NOT chosen)
                      SAMPLE WINDOW UNCHANGED: 2010-06-06 -> 2022-01-01 exclusive.
                      OD-5 fixes the KIND of fund-size representation required, not the
                      sample boundary. If source verification yields only partial PIT
                      coverage, an ADDITIONAL explicit S1 sample-eligibility /
                      sample-boundary rule is required UNDER OD-5 — made under the
                      decision, never a reopening of it. Not taken here.
SOURCE_VERIFICATION = SV1_RESULT = NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED
                      (public evidence insufficient to verify a source — NOT a
                      finding that none exists)
                      SV1_VERIFIED_SOURCE = NONE
                      STRONGEST_PUBLICLY_DOCUMENTED_PIT_METADATA_CANDIDATE =
                                    ETF Global (effective_date + processed_date)
                                    — strongest PUBLIC DOCUMENTATION of PIT
                                    metadata, NOT a finding of ultimate
                                    superiority over Bloomberg / LSEG /
                                    Morningstar / FactSet, all of which remain
                                    PLAUSIBLE_UNVERIFIED; vendor evidence remains pending.
                      CANDIDATE_CLASSIFICATION       = PLAUSIBLE_UNVERIFIED
                      2016_ACID_TEST_PASS_COUNT      = 0  (of 20 candidates)
                      R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
                      PAID_PURCHASE_REQUIRED         = UNKNOWN / CONDITIONAL
                      R2_VENDOR_ENQUIRY_REQUIRED     = YES  (all 6 Wave-1 enquiries
                                                       dispatched; responses pending)
                      R2_PATH_C_PARK_TRIGGER         = NO — the trigger is
                                    EVIDENTIARY: it fires only if the bounded
                                    enquiry process CLOSES with no qualifying
                                    source and no material candidate remaining.
                                    A calendar deadline is not scientific evidence.
                      FORWARD_PIT_COLLECTION = AUTHORIZED, BUILT AND SCHEDULED
                                               (see FORWARD_PIT below)
                      See R2_SV1_SOURCE_VERIFICATION_REPORT.md.
OPEN_MATERIAL_BLOCKERS =
                      B-3   R2_PRE_S1_TIMING_BLOCKER = YES. Pre-2014-03-26 AUM
                            publication not established: the field was absent from
                            the published file in its 2011 and 2012 vintages, and
                            there is no archival evidence at all for
                            2012-09-26 -> 2014-03-25.
                            SV-1 did NOT close this. No obtainable source has been
                            verified to carry historical availability evidence for
                            the five funds over 2010-2021.
                      G-11  The publication batch can miss a trading day (observed
                            2016-04-01). S1 must carry a per-date staleness rule.
OWNER_AUTHORITY     = R2_DELEGATED_OWNER_DECISIONS.md is the authority record.
                      OD-1 = GRANT_EXISTING_NQ_DEVELOPMENT
                      OD-2 = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY
                      OD-5 = PATH_A_TRUE_PIT_DAILY
                             OD5_STATUS = ACCEPTED_DELEGATED_OWNER_DECISION
                      OD-6 = PROVEN_PUBLICATION_ONLY_ZERO_CARRY
                             OD6_STATUS = ACCEPTED_DELEGATED_OWNER_DECISION
                      OD-5 and OD-6 are DECIDED and are NOT to be reopened.
DATA_ACQUISITION    = R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
                      PAID_PURCHASE_REQUIRED = UNKNOWN / CONDITIONAL
FORWARD_PIT         = RECURRING_FORWARD_COLLECTION = ENABLED
                      FORWARD_TASK_NAME = QuantTrade-R2-ForwardPIT
                      FORWARD_TASK_INSTALLED = YES   FORWARD_TASK_ENABLED = YES
                      SCHEDULE = daily, every CALENDAR day, 11:00
                                 Asia/Kuala_Lumpur (machine TZ UTC+08:00, no DST)
                      FIRST_SCHEDULED_RUN = 2026-09-20 11:00 +08:00
                      FORWARD_TASK_LOGON_TYPE = INTERACTIVE_TOKEN
                      MICROSOFT_ACCOUNT_PRINCIPAL_MODE = YES
                             (Get-LocalUser PrincipalSource = MicrosoftAccount.
                              Password-backed registration must authenticate as
                              MicrosoftAccount\<account email>, NOT the NTAccount
                              form DESKTOP-B7VTGF0\Aaron. That mismatch — not a
                              wrong password — caused the earlier failure. The
                              password itself was validated externally by Aaron.)
                      MICROSOFT_ACCOUNT_EMAIL = NOT_PERSISTED
                      FIRST_NATURAL_SCHEDULED_RUN = OBSERVED_FAIL_2026_09_21
                             (11:00:01 fired, LastTaskResult=1, no stdout line, no
                              log record, no snapshot — the action never launched.
                              That day is MISSING_FORWARD_CAPTURE, NOT backfilled.
                              ATTRIBUTION CORRECTED: this is the signature of the
                              CMD QUOTING defect, not of the principal mismatch.
                              Both faults were present at that firing, so the
                              evidence does not separate their contributions.)
                      NEXT_NATURAL_SCHEDULED_RUN = 2026-09-22 11:00 Asia/Kuala_Lumpur
                      NATURAL_SCHEDULED_CAPTURES_TO_DATE = 0
                      CAPTURES_TO_DATE = 5, ALL manual:
                             2026-09-19/125150_ET  MANUAL_COLLECTOR_VALIDATION
                             2026-09-19/131606_ET  MANUAL_WRAPPER_CHAIN_VALIDATION
                             2026-09-21/063831_ET  MANUAL_MSA_CONTEXT_DIAGNOSTIC
                             2026-09-21/063916_ET  MANUAL_MSA_CONTEXT_DIAGNOSTIC
                             2026-09-21/064554_ET  MANUAL_MSA_CONTEXT_DIAGNOSTIC
                             (the last three are labelled ROUTINE_FORWARD_COLLECTION
                              in their immutable manifests because the wrapper was
                              invoked directly; manifests NOT modified. They must
                              never be represented as NATURAL_SCHEDULED_CAPTURE.)
                      FORWARD_COLLECTION_AUTONOMY = PASSWORD_BACKED_UNATTENDED
                             (by configuration: LogonType Password is registered
                              live. Collection still cannot succeed until the
                              action is re-registered with the corrected quoting.)
                      RUN_WHILE_USER_LOGGED_OUT       = YES (by configuration)
                      PASSWORD_BACKED_TASK_CONTEXT_VALIDATED = NO
                             (Start-ScheduledTask validation blocked by the
                              un-repaired action; see CMD_QUOTING_DEFECT)
                      NETWORK_ACCESS_IN_TASK_CONTEXT       = UNTESTED
                      LOCAL_PROJECT_ACCESS_IN_TASK_CONTEXT = UNTESTED
                      TRUE_NO_INTERACTIVE_SESSION_VALIDATED = NO
                      S4U_UPGRADE_FOR_FORWARD_COLLECTOR = FORBIDDEN_WRONG_FIT
                             (S4U issues a token with NO network credentials;
                              this collector needs outbound HTTPS. The earlier
                              S4U upgrade suggestion is WITHDRAWN.)
                      TARGET = LogonType Password, least privilege, Aaron's own
                              user identity. Installer supports two explicit
                              modes and never silently downgrades.
                      MANUAL_SECURE_CREDENTIAL_STEP_REQUIRED = YES
                             (re-registering the corrected action needs the account
                              password in a LOCAL prompt; Set-ScheduledTask cannot
                              rewrite a password-backed action without it. Attempted
                              2026-09-21: failed and correctly changed NOTHING.)
                      StartWhenAvailable covers a missed slot either way.
                      Captures to date: 2026-09-19/125150_ET (INFRASTRUCTURE_
                      VALIDATION) and 2026-09-19/131606_ET (SCHEDULER_VALIDATION).
                      Neither is a research observation. Collects FORWARD dates
                      only — it does NOT repair 2010-2021 and assigns no sample
                      tier. See R2_FORWARD_PIT_COLLECTION.md.
VENDOR_WAVE1_AUTHORIZED = YES
VENDOR_WAVE1_SENT_COUNT = 6
VENDOR_WAVE1_TOTAL      = 6
VENDOR_WAVE1_STATUS     = ALL_SENT
ETF_GLOBAL              = CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE
LSEG_LIPPER             = SENT_AWAITING_RESPONSE
BLOOMBERG               = SENT_AWAITING_RESPONSE
MORNINGSTAR             = SENT_AWAITING_RESPONSE
MORNINGSTAR_SUPPORT     = ROUTING_REQUEST_SENT
MORNINGSTAR_SUPPORT_SENT_AT = 2026-09-22T14:30:19+08:00 (06:30:19Z)
MORNINGSTAR_FREE_TRIAL  = APPLIED
MORNINGSTAR_FREE_TRIAL_APPLIED_AT = 2026-09-22T14:37:41+08:00 (06:37:41Z)
MORNINGSTAR_FREE_TRIAL_REFERENCE = MORNINGSTAR_DIRECT_TRIAL/THANK_YOU
MORNINGSTAR_SOURCE_VERIFICATION = UNCHANGED_PENDING_EVIDENCE
PROSHARES_PROFUNDS      = SENT_AWAITING_RESPONSE
FACTSET                 = SENT_AWAITING_RESPONSE
VENDOR_WAVE1        = ETF Global is
                      CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE. Morningstar,
                      ProShares / ProFunds and FactSet are SENT_AWAITING_RESPONSE.
                      LSEG / Lipper and Bloomberg are SENT_AWAITING_RESPONSE. Their
                      official contact forms were submitted on 2026-09-21 and returned
                      explicit confirmation pages. No provider reference number was shown.
                      Contact details are not persisted in project records.
                      See R2_VENDOR_WAVE1_DISPATCH.md and R2_VENDOR_RESPONSE_TRACKER.md.
NEXT_OWNER_DECISION = Review vendor responses and any Morningstar access message when
                      received. No additional follow-up, purchase, paid trial,
                      subscription, contract or sales meeting is authorized.
                      Recurring forward collection is AUTHORIZED and INSTALLED. A separate
                      S1 DESIGN authorization remains NOT issued.
DATA_PURCHASE_AUTHORIZED = NO
FREE_TRIAL_AUTHORIZED    = YES
PAID_TRIAL_AUTHORIZED    = NO
CONTRACT_AUTHORIZED      = NO
PAID_SUBSCRIPTION_AUTHORIZED = NO
FOLLOWUP_AUTHORIZED      = NO  (no additional follow-up beyond completed routing request)
POST_2022_SAMPLE_TIER    = UNASSIGNED
NQ_DATA_DECODED          = NO
NQ_RETURN_COMPUTED       = NO
R2_PNL_COMPUTED          = NO
TRIAL_CONSUMED           = NO
R2_S1_AUTHORIZED         = NO
```

## Superseding amendment — OD-5 / OD-6 authority (2026-09-20)

**Supersedes the `NEXT_OWNER_DECISION` line as it stood on 2026-09-19**, which listed
"OD-5 sample boundary · OD-6 staleness rule" as pending and recorded that no accepted
record existed on disk.

That entry was a **bookkeeping defect, not an open decision**. OD-5 and OD-6 had been
decided and accepted through the delegated chain (`DELEGATED_BY = Aaron`,
`DECIDED_BY = Fable`, `ACCEPTED_BY = ChatGPT`) before SV-1 ran; what was missing was the
persisted record. That record now exists at `R2_DELEGATED_OWNER_DECISIONS.md`.

```
PROJECT_STATE_OD5_OD6_PENDING = NO
```

The earlier pending text is retained above in amended form rather than deleted, per
append-only correction convention. Nothing else in the prior record is altered.

**One consequence to carry forward:** OD-5 fixes the *kind* of fund-size representation
R2 requires, not the sample boundary. If source verification yields only partial PIT
coverage, an **additional explicit S1 sample-eligibility / sample-boundary rule will be
required under OD-5** — a rule made under the decision, not a reopening of it.

## Delegated Owner rulings of record

```
DELEGATED_OWNER_RULING
  DELEGATED_BY = Aaron
  DECIDED_BY   = Fable
  ACCEPTED_BY  = ChatGPT

  S0 DATA FEASIBILITY = PASS / CLOSED
  OD-1 DATA AUTHORITY = GRANT existing NQ Development archive under a NEW
                        R2 lineage-specific grant
  OD-2 SCOPE          = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY
  OD-5 FUND SIZE PATH = PATH_A_TRUE_PIT_DAILY          (same chain)
  OD-6 STALENESS      = PROVEN_PUBLICATION_ONLY_ZERO_CARRY   (same chain)
  R2_S1               = NOT AUTHORIZED
  R2_OUTCOME_EXPOSURE = NONE
```

Full text and provenance: **`R2_DELEGATED_OWNER_DECISIONS.md`**, which is the authority
record. This block is a state pointer to it.

Recorded as delegated-and-decided through that chain — **not** as Aaron personally
selecting each ruling.

## Accepted reservations — carried, not resolved

1. Post-2022 is **NOT** assigned to Validation / Lockbox. Its future sample tier
   remains **UNASSIGNED**.
2. Missing mutual-fund reset flow is **NOT** assumed to create only attenuation:
   **KNOWN MEASUREMENT OMISSION / MAGNITUDE UNKNOWN**.
3. Mutual-fund flow is **NOT** assumed to occur only at the close, and **NOT**
   assumed unable to matter pre-close.

Reservations 2 and 3 supersede the countervailing argument in
`R2_FEASIBILITY_REPORT.md` §11 row G-1; see the amendment appended to that file.

## Non-blocking backlog

`G-1` mutual-fund sleeve (under reservations 2 and 3) · `G-2` broader-scope fund
assets (moot under OD-2) · `G-4` never-launched confirmation · `G-5` SEC 2016 / 2024
series files · `G-6` vintage / restatement — partially and favourably tested
2026-09-19, zero restatements across 20,616 overlapping rows · `G-7` prospectus-dated
mandate table, S1's first collection task · `G-8` no local NQ data after 2022-01-01
(see reservation 1) · `G-9` intraday rebalance timing unobservable in principle ·
`G-10` ProShares endpoint stability — snapshot, hash and record headers at collection
time.

## Artifacts

| file | what it is |
|---|---|
| `R2_S0_PROVENANCE.md` | where R2 came from; what the feasibility stage is and is not |
| `R2_MINIMUM_DATA_CONTRACT.md` | prospective contract, written before availability was judged |
| `R2_DATA_SOURCE_AUDIT.md` | local / public / paid source audit (+ 2026-09-19 amendment) |
| `R2_FEASIBILITY_REPORT.md` | coverage matrix, identifiability finding, classification (+ 2026-09-19 amendment) |
| `R2_G3_ACCEPTANCE_CRITERIA.md` | G-3 closure standard, written before its evidence existed |
| `R2_G3_PUBLICATION_TIMING_REPORT.md` | G-3 modern-endpoint evidence. **Its full-sample close was NOT ACCEPTED by the controller** - see the amendment |
| `R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md` | 2010-2019 evidence regimes R-1..R-4 |
| `R2_G3_HISTORICAL_PIT_AMENDMENT.md` | corrected G-3 status: PARTIAL, safe start 2014-03-26 |
| `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md` | SV-1 evidence standard, written before any candidate was judged |
| `R2_SV1_SOURCE_MATRIX.md` | 20 candidates across 9 classes, with decisive evidence and missing facts |
| `R2_SV1_SOURCE_VERIFICATION_REPORT.md` | SV-1 result, 2016 acid test, acquisition readiness, forward option |
| `R2_SV1_VENDOR_ENQUIRY_PACKET.md` | 6 prepared vendor enquiries; all 6 dispatched |
| `R2_DELEGATED_OWNER_DECISIONS.md` | **authority record** — OD-1, OD-2, OD-5, OD-6 with provenance |
| `R2_FORWARD_PIT_COLLECTION.md` | forward PIT collection — purpose, schema, first capture, how to run |
| `tools/collect_forward_pit.py` | collector + verifier (v1.0.0, manifest schema v1) |
| `tools/test_collect_forward_pit.py` | 15 synthetic tests, no network |
| `tools/run_forward_pit_scheduled.py` | scheduled wrapper — lock, JSONL log, honest timing |
| `tools/test_run_forward_pit_scheduled.py` | 16 synthetic wrapper tests, no network |
| `tools/task_action.py` | canonical cmd.exe action-argument builder + validator |
| `tools/test_task_action.py` | 9 quoting regression tests incl. 2 negative controls |
| `tools/run_forward_pit_task.cmd` | Task Scheduler entry point; captures stdout + stderr |
| `tools/install_forward_pit_task.ps1` | resolves interpreter, registers, verifies, exports XML |
| `tools/remove_forward_pit_task.ps1` | removes ONLY `QuantTrade-R2-ForwardPIT` |
| `ops/R2_FORWARD_PIT_TASK.xml` | LIVE export — currently pre-repair Interactive |
| `ops/R2_FORWARD_PIT_TASK.template.xml` | sanitized declarative target definition, no secrets |
| `logs/forward_pit_scheduler.jsonl` | append-only operational log (no fund values) |
| `R2_VENDOR_WAVE1_DISPATCH.md` | Wave-1 dispatch package — Owner authorized; all 6 sent |
| `R2_VENDOR_RESPONSE_TRACKER.md` | one row per vendor; all 6 sent; no evidentiary responses yet |
| `vendor_outbound/` | 6 authoritative message files; 4 dispatched by email and 2 by official contact form |
| `data_forward_pit/2026-09-19/125150_ET/` | first capture — 5/5 funds, VERIFY PASS, read-only |
| `data_probe/proshares_nav_2026-09-17/` | first feasibility probe — hashed, not a research dataset |
| `data_probe/g3_timing_2026-09-19/` | G-3 timing evidence — CSVs, raw HTTP headers, directory indexes |
| `data_probe/g3_historical_pit_2026-09-19/` | 44 archived 2010–2018 captures with preserved origin headers, `MANIFEST.sha256` |

## Not present, deliberately

No sealed preregistration, no trial registry, no signal definition, no run identity,
no primary result, no outcome bundle. R2 has not reached S1 and none of those may be
created here.

## SV-1 source classifications (2026-09-19)

Full evidence: `R2_SV1_SOURCE_MATRIX.md`. Standard: `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md`.

```
VERIFIED_FULL         none
VERIFIED_PARTIAL      none
PLAUSIBLE_UNVERIFIED  ETF Global (direct / Massive / Nasdaq Data Link / WRDS)
                      LSEG Lipper Fund Flows
                      Bloomberg Global ETP Flows Data Solution
                      Morningstar Direct
                      FactSet ETF Standard DataFeed
                      Nasdaq Fund Network            (carried from B-7)
                      ProShares issuer archive / batch logs
REJECTED              ProShares published file as a PIT source   (R4, R5)
                      Bloomberg COFI Point-in-Time              (R1 - companies only)
                      FactSet Fundamentals Point-in-Time        (R1 - companies only)
                      LSEG Lipper ETF Daily Holdings            (R1)
                      CRSP Survivor-Bias-Free US Mutual Fund DB (R2 - monthly TNA)
                      CRSP US Stock daily file                  (R1, R2, R4)
                      Ultumus / SIX                             (R3 - rolling 5-year)
                      NYSE Arca EOD ETF Report                  (R1 - no fund-size
                                                                 field; R3)
                      Internet Archive over ProShares CSVs      (R2, R3)
                      Internet Archive over aggregator pages    (R1, R2)
```

Two structural findings that bound future work:

- **Every documented vendor point-in-time product is scoped to company fundamentals**,
  not fund size. Vendor PIT reputation does not transfer to ETP AUM.
- **The R2 universe straddles two listing venues** — QLD/QID/PSQ are NYSE Arca (`P`),
  TQQQ/SQQQ are Nasdaq (`Q`), per the official Nasdaq symbol directory. No single
  listing-venue reference product can cover more than 3 of 5, and OD-6 forbids a
  partial-universe `K_t`. This closes the exchange-archive class as a standalone route.

Also recorded: the **Internet Archive is available again** (`R2_DATA_SOURCE_AUDIT` A-6
found it offline earlier the same day). Re-tested for the five funds' ProShares CSVs over
2014-2019: QLD 0, QID 0, PSQ 0, TQQQ 2, SQQQ 0 status-200 captures — the earlier negative
finding stands on fresh evidence.

## G-3 correction of record (2026-09-19)

```
PRIOR_G3_CLOSE = NOT ACCEPTED BY CONTROLLER
REASON         = 2010-2019 historical PIT availability not established
CORRECTED      = G3_HISTORICAL_STATUS = PARTIAL
                 HISTORICAL_PIT_SAFE_START = 2014-03-26
                 PRE_SAFE_PERIOD = UNRESOLVED
```

The earlier close generalized 2020/2022/2026 endpoint behaviour to a sample beginning
2010-06-06. Contemporaneous archived artifacts show the published file carried **no
`Assets Under Management` column** in its 2011 and 2012 vintages, and there is **no
archival evidence at all** between 2012-09-26 and 2014-03-25. Prior evidence is not
deleted; see `R2_G3_HISTORICAL_PIT_AMENDMENT.md`.
