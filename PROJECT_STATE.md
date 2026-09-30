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
                    GRANTED, NOT EXERCISED (no archive file decoded or inspected)
OUTCOME_EXPOSURE  = NONE
TRIAL_ACCOUNTING  = OD-1: separate R2 accounting; sample NOT fresh (prior exposure
                    disclosed); a first formal run would be sample ordinal 3, R2 trial 1
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
VENDOR_WAVE1      = 6/6 sent    RESPONSES_RECEIVED = 0 (evidentiary)
  ETF Global CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE · Morningstar
  SALES_ROUTING_COMPLETE_AWAITING_RESPONSE (SELF-REPORTED) · LSEG / Lipper, Bloomberg,
  ProShares / ProFunds, FactSet SENT_AWAITING_RESPONSE — all six PENDING_RESPONSE
FORWARD_PIT       = task QuantTrade-R2-ForwardPIT, daily 11:00 +08:00; principal
                    LogonType Password, RunLevel Limited, State Ready; next run
                    2026-10-01 11:00 +08:00 (read 2026-10-01 03:35 +08:00)
  derived by tools/reproduce.py, COUNTS_AS_OF_SNAPSHOT = 2026-09-30/144521_ET
  SNAPSHOTS = 15   SNAPSHOTS_VERIFIED = 15/15   JSONL_ROWS = 14
  NATURAL_CAPTURES = 9   CATCH_UPS = 2   MANUAL_CAPTURES = 6
  LAST_SNAPSHOT = 2026-09-30/144521_ET
  rule (D-R2-2026-10-01-02): NATURAL = task-start block + ROUTINE_FORWARD_COLLECTION +
  slot >= trigger StartBoundary + sole invocation for its slot; all else MANUAL.
  Forward dates only: repairs nothing in 2010-2021, assigns no sample tier.
OPEN_BLOCKERS     = B-3  pre-2014-03-26 AUM publication not established; no verified
                         source carries historical availability for 2010-2021
                    G-11 the publication batch can miss a day (2016-04-01); S1 needs a
                         per-date staleness rule under OD-6
LIVE_GRANTS       = OD-1 (standing, unexercised); forward collection (standing);
                    NO one-shot run grant; publication scope D-R2-2026-10-01-03a–e (public
                    mirror; the push is Aaron's own act, the builder holds no push grant)
LIVE_OBLIGATIONS  = none dated; vendor responses pending (no follow-up authorized)
FLAGS             = DATA_PURCHASE_AUTHORIZED NO · PAID_TRIAL_AUTHORIZED NO · CONTRACT NO ·
                    PAID_SUBSCRIPTION NO · FOLLOWUP_AUTHORIZED NO · FREE_TRIAL_AUTHORIZED
                    YES (applied, not activated) · POST_2022_SAMPLE_TIER UNASSIGNED ·
                    NQ_DATA_DECODED NO · NQ_RETURN_COMPUTED NO · R2_PNL_COMPUTED NO ·
                    TRIAL_CONSUMED NO · R2_S1_AUTHORIZED NO
NEXT_DECISION     = delegate acceptance of CP-R2-V2-01 (then CP-MONO-01); research:
                    classify the first evidentiary vendor reply under
                    R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md — holder: delegate, informed by
                    builder; any purchase / trial / follow-up / push — holder: Aaron
LAST_CHECKPOINT   = CP-R2-V2-01 (commit: git log -1 -- PROJECT_STATE.md)
```

**Not present, deliberately.** No sealed preregistration, no trial registry, no signal
definition, no run identity, no primary result, no outcome bundle. R2 has not reached S1
and none of those may be created here. Backlog: `DECISION_LOG.md` (BL-R2-01) and the G-1 …
G-10 list in the baseline `PROJECT_STATE.md`. Artifact map: `README.md`.
