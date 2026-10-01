# PROJECT_STATE — nq-letf-rebalancing-research (R2)

Current state only, rewritten each checkpoint (v2 §6); state, never authority. Superseded facts: git history (baseline `bd66324`) and the dated amendment files.

```
PROJECT           = nq-letf-rebalancing-research      LINEAGE = R2
RESEARCH_QUESTION = Does the aggregate daily-reset rebalancing demand of the Nasdaq-100
                    leveraged and inverse ETFs leave a mechanically predictable late-day
                    footprint that transmits into Nasdaq-100 index futures?
STAGE             = PRE-S1 / WAITING_FOR_EXTERNAL_EVIDENCE   ACTIVE_HYPOTHESIS = NONE   LANE = n/a
SCOPE             = OD-2 NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY: QLD QID PSQ TQQQ SQQQ;
                    generic momentum substitute FORBIDDEN (sign(F_t) = sign(r_pre));
                    distinctness must come from K_t / L_t, else PARK
AUTHORITY         = R2_DELEGATED_OWNER_DECISIONS.md (OD-1/2/5/6) + DECISION_LOG.md
DATA_GRANT        = OD-1, NQ Development archive 2010-06-06 -> 2022-01-01 exclusive:
                    GRANTED, NOT EXERCISED. No NQ data file decoded; S0 recorded pre-grant
                    metadata-only reads (listing, condition.json, hashes) — COR-R2-G02
OUTCOME_EXPOSURE  = NONE    TRIAL_ACCOUNTING = OD-1: separate R2 accounting; sample NOT
                    fresh (exposure disclosed); a first formal run = sample ordinal 3, R2 trial 1
CAUSAL_TIMING     = (D-R2-2026-10-01-01, verbatim)
  G3_HISTORICAL_STATUS             = PARTIAL                       (unchanged)
  AUM_FIELD_OBSERVED_START         = 2014-03-26                    (fact; unchanged)
  HISTORICAL_DAILY_PIT_SAFE_START  = NOT_ESTABLISHED
  PRE_2014-03-26_PERIOD            = UNRESOLVED                    (unchanged)
  FULL_SAMPLE_AUM_AVAILABLE_BY     = UNKNOWN                       (unchanged)
  G11_STALENESS_PROBLEM            = MATERIAL                      (unchanged)
  S1_TAU_CONSTRAINT                = tau > 09:30 ET on trading day t, applicable only to
                                     dates a verified source proves eligible under OD-6
                                     (mechanical constraint; tau is not chosen)
SOURCE_VERIFICATION = SV1_RESULT = NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED; strongest
                    documented candidate class PLAUSIBLE_UNVERIFIED (ETF Global et al.);
                    2016 acid test 0/20; R2_PATH_C_PARK_TRIGGER = NO (evidentiary)
VENDOR_WAVE1      = 6/6 sent, RESPONSES_RECEIVED = 0 (evidentiary), all PENDING_RESPONSE:
  ETF Global CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE · Morningstar SALES_ROUTING_
  COMPLETE_AWAITING_RESPONSE (SELF-REPORTED) · LSEG, Bloomberg, ProShares, FactSet SENT_
  AWAITING_RESPONSE. Nasdaq Fund Network REJECTED (R3) 2026-10-02; these six are the set
FORWARD_PIT       = task QuantTrade-R2-ForwardPIT, daily 11:00 +08:00; principal
                    LogonType Password, RunLevel Limited, State Ready; last result 0;
                    next run 2026-10-02 11:00 +08:00 (read 2026-10-02 02:07 +08:00)
  derived by tools/reproduce.py, COUNTS_AS_OF_SNAPSHOT = 2026-09-30/230001_ET
  SNAPSHOTS = 16   SNAPSHOTS_VERIFIED = 16/16   JSONL_ROWS = 15
  NATURAL_CAPTURES = 10   CATCH_UPS = 2   MANUAL_CAPTURES = 6
  LAST_SNAPSHOT = 2026-09-30/230001_ET
  rule (D-R2-2026-10-01-02): NATURAL = task-start block + ROUTINE_FORWARD_COLLECTION +
  slot >= 2026-09-21T11:00+08:00 (pinned) + sole invocation for its slot; else MANUAL.
  Gaps: 2026-09-21 11:00 MISSING_FORWARD_CAPTURE; 2026-09-20 NO_FIRING_RECORD.
  Forward dates only: repairs nothing in 2010-2021, assigns no sample tier.
OPEN_BLOCKERS     = B-3  pre-2014-03-26 AUM publication not established; no verified
                         source carries historical availability for 2010-2021
                    G-11 the publication batch can miss a day (2016-04-01); S1 needs a
                         per-date staleness rule under OD-6
LIVE_GRANTS       = OD-1 (standing, unexercised); forward collection (standing);
                    no one-shot run grant; publication scope D-R2-2026-10-01-03a–e (push is
                    Aaron's own act); R1 record-correction lease (D-R2-2026-10-02-01)
LIVE_OBLIGATIONS  = none dated; vendor responses pending (no follow-up authorized)
FLAGS             = DATA_PURCHASE_AUTHORIZED NO · PAID_TRIAL_AUTHORIZED NO · CONTRACT NO ·
                    PAID_SUBSCRIPTION NO · FOLLOWUP_AUTHORIZED NO · TRIAL_ACTIVATION_AUTHORIZED
                    NO (free trial applied 2026-09-22, not activated) · POST_2022_TIER UNASSIGNED ·
                    NQ_DATA_DECODED NO · NQ_RETURN_COMPUTED NO · R2_PNL_COMPUTED NO ·
                    TRIAL_CONSUMED NO · R2_S1_AUTHORIZED NO
NEXT_DECISION     = delegate acceptance of CP-REPAIR-01, then CP-MONO-01, then Aaron's push;
                    research: classify the first evidentiary vendor reply under criteria §2
                    (COR-R2-G15) — delegate, informed by builder; purchase/trial/follow-up: Aaron
LAST_CHECKPOINT   = CP-R2-V2-01 at e11a1c9266a53b8c0c021b5081745941f098b4a2, ACCEPTED
                    (ACC-CP-R2-V2-01); CP-REPAIR-01 pending (commit range in DECISION_LOG)
```

**Not present, deliberately.** No sealed preregistration, no trial registry, no signal definition,
no run identity, no primary result, no outcome bundle: R2 has not reached S1 and none may be created
here. Backlog: `DECISION_LOG.md` (BL-R2-01 … 05), G-1 … G-10 in baseline `PROJECT_STATE.md`. Map: `README.md`.
