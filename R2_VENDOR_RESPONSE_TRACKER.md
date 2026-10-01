# R2_VENDOR_RESPONSE_TRACKER

```
RECORD_TYPE = VENDOR_RESPONSE_TRACKER
LINEAGE     = R2
WAVE        = 1
CREATED     = 2026-09-20
STATE       = four SENT_AWAITING_RESPONSE; ETF Global
              CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE; Morningstar
              SALES_ROUTING_COMPLETE_AWAITING_RESPONSE; no evidentiary vendor response
              received
UPDATED     = 2026-10-02 (CP-REPAIR-01: dispatch-record note, VERIFIED_PARTIAL rule note,
              trial flag; under D-R2-2026-10-02-01)
```

Companion to `R2_VENDOR_WAVE1_DISPATCH.md`. One row per vendor, filled in as replies
arrive.

**`UNKNOWN` is the correct entry for anything a vendor has not actually answered.** Do not
manufacture empty factual answers, and do not let a confident sales tone fill a gap. A
blank is a finding; an invented value is a defect.

---

## 1. Outbound status

| VENDOR | OUTBOUND_STATUS | SENT_AT | CHANNEL | MESSAGE_ID_OR_REFERENCE | RESPONSE_DATE | RESPONDER_ROLE |
|---|---|---|---|---|---|---|
| ETF Global | CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE | 2026-09-21T19:25+08:00 (11:25Z) | EMAIL | YAHOO_SENT/00_62116 | UNKNOWN | UNKNOWN |
| LSEG / Lipper | SENT_AWAITING_RESPONSE | 2026-09-21T20:16:08+08:00 (12:16:08Z) | OFFICIAL_CONTACT_FORM | LSEG_CONFIRMATION_PAGE/data-catalogue-thank-you | — | — |
| Bloomberg | SENT_AWAITING_RESPONSE | 2026-09-21T20:16:54+08:00 (12:16:54Z) | OFFICIAL_CONTACT_FORM | BLOOMBERG_CONFIRMATION_PAGE/request-demo/thank-you | — | — |
| Morningstar | SALES_ROUTING_COMPLETE_AWAITING_RESPONSE | 2026-09-21T19:26+08:00 (11:26Z) | EMAIL | YAHOO_SENT/00_62118; ROUTING_REPLY/YAHOO_THREAD_00_62118 | 2026-09-22 | Morningstar Direct Product Consultant |
| ProShares / ProFunds | SENT_AWAITING_RESPONSE | 2026-09-21T19:27+08:00 (11:27Z) | EMAIL | YAHOO_SENT/00_62120 | — | — |
| FactSet | SENT_AWAITING_RESPONSE | 2026-09-21T19:27+08:00 (11:27Z) | EMAIL | YAHOO_SENT/00_62121 | — | — |

The Owner supplied the remaining required values and authorized both mandatory
communications notices. Both official forms were submitted on 2026-09-21. LSEG returned
`Thank you for contacting us` and stated that the details were received. Bloomberg
returned `You've taken the first step!` and stated that the request is under review. No
provider reference number was displayed, so the non-sensitive confirmation-page paths are
recorded above. Contact details are not persisted in this tracker.

Morningstar Direct Support replied that the first enquiry came from an unregistered email
address and could not be handled as a platform-support request. The prepared reply asking
Support to route the historical point-in-time fund-size enquiry to the appropriate data
sales, licensing or product team was sent in the same thread on 2026-09-22. This was an
operational routing response, not evidence about Morningstar data coverage or point-in-time
semantics.

### Morningstar operational follow-up and trial

```
MORNINGSTAR                          = SALES_ROUTING_COMPLETE_AWAITING_RESPONSE   (2026-10-01, SELF-REPORTED)
MORNINGSTAR_SUPPORT                  = ROUTING_REQUEST_SENT -> routed to Morningstar Sales team (SELF-REPORTED)
MORNINGSTAR_SUPPORT_CASE             = Morningstar support case (number withheld)   (SELF-REPORTED)
MORNINGSTAR_SUPPORT_SENT_AT          = 2026-09-22T14:30:19+08:00 (06:30:19Z)
MORNINGSTAR_SUPPORT_REFERENCE        = YAHOO_THREAD/00_62118
MORNINGSTAR_FREE_TRIAL               = APPLIED_NOT_ACTIVATED   (2026-10-01; was APPLIED)
MORNINGSTAR_FREE_TRIAL_APPLIED_AT    = 2026-09-22T14:37:41+08:00 (06:37:41Z)
MORNINGSTAR_FREE_TRIAL_REFERENCE     = MORNINGSTAR_DIRECT_TRIAL/THANK_YOU
MORNINGSTAR_TRIAL_CONFIRMATION       = Thank you — Enjoy your free two-week trial of Morningstar Direct.
MORNINGSTAR_SOURCE_VERIFICATION      = UNCHANGED_PENDING_EVIDENCE
```

`APPLIED` records the successful official-form confirmation. It does not assert that login
credentials or usable access have been granted. The trial request does not change any
source classification.

**2026-10-01 — Morningstar routing, SELF-REPORTED (Aaron handoff 2026-10-01).** Evidence
reference: `handoffs/2026-10-01_AARON_R2_HANDOFF.md` §17. As reported there, not reproduced
from any vendor message:

- Morningstar Direct Support opened a Morningstar support case (number withheld).
- The displayed trial route was not usable in practice; the free trial was never
  activated (`MORNINGSTAR_FREE_TRIAL = APPLIED_NOT_ACTIVATED`).
- Morningstar stated that Morningstar Cloud is not available on an individual student
  licence and suggested a university library; Aaron declined to pursue that route.
- Morningstar found no account under Aaron's university and routed the enquiry to
  its Sales team.
- Aaron chose to wait.

None of this answers the PIT question; no decisive cell changes and the classification
stays `PENDING_RESPONSE`. "No account under Aaron's university" is not evidence about Morningstar's
data. No follow-up, trial activation, purchase or library-access step is authorized.

The support-case number and the university name are withheld from this published record
under delegate decision D-R2-2026-10-01-03 (Owner instruction); they are held in the
unpublished original handoff in the author's workspace (`Workspace Docs/handoffs/`).

The Morningstar e-mail thread is not yet stored in the project; until Aaron exports it
(contact details redacted) into `vendor_inbound/`, the handoff is the only evidence
reference.

**2026-10-02 — dispatch record, SELF-REPORTED (CP-AUDIT-01 R2-G18, D-R2-2026-10-02-01).**

- The files in `vendor_outbound/` are the messages **as prepared 2026-09-20** (status
  READY_NOT_SENT, with unfilled name / affiliation placeholders). The sent copies, the
  recipients and any inbound vendor message are not stored in the project; the dispatch
  evidence is the SELF-REPORTED `SENT_AT` / `MESSAGE_ID_OR_REFERENCE` cells above.
- Channels changed from the plan: ETF Global was planned as a web form and ProShares as a
  phone route; both were e-mailed (CHANNEL = EMAIL above). The recipient addresses are not
  recorded (contact details are not persisted).
- ETF Global's academic-affiliation clarification: that it was received and answered is
  SELF-REPORTED; its date and content are UNKNOWN, so the ETF Global RESPONSE_DATE and
  RESPONDER_ROLE read UNKNOWN.
- Citation correction: the withholding note above cites "D-R2-2026-10-01-03 (Owner
  instruction)". That id was never logged; the governing rows are OWNER-R2-2026-10-01 and
  D-R2-2026-10-01-03c (`DECISION_LOG.md`).

## 2. Decisive PIT semantics

The four columns that actually decide the question. Everything else is context.

| VENDOR | ORIGINAL_VINTAGE | PER_DATE_TIMESTAMP | TIMESTAMP_RESOLUTION | AS_KNOWN_AT_QUERY | 2016_ACID_TEST |
|---|---|---|---|---|---|
| ETF Global | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| LSEG / Lipper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Bloomberg | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Morningstar | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| ProShares / ProFunds | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| FactSet | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

`TIMESTAMP_RESOLUTION` legal values: `DATE_ONLY` · `DATE_TIME_TZ` · `NONE` · `UNKNOWN`.
`2016_ACID_TEST` legal values: `PASS` · `FAIL` · `UNKNOWN` — `PASS` requires the sample to
have been **delivered with availability timestamps**, never a promise that it could be.

## 3. Coverage and field identity

| VENDOR | PRODUCT_NAMED | FIELD_IDENTITY | DAILY_FREQUENCY | HISTORY_START | ALL_5_FUNDS | SURVIVORSHIP | IDENTIFIER_SUPPORT |
|---|---|---|---|---|---|---|---|
| ETF Global | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| LSEG / Lipper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Bloomberg | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Morningstar | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| ProShares / ProFunds | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| FactSet | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

**These columns record what the vendor states, not what was previously inferred from public
documentation.** SV-1's documentary findings stay in `R2_SV1_SOURCE_MATRIX.md`; a vendor
statement that contradicts them is itself a finding worth recording, not a correction to
apply silently.

## 4. Commercial and disposition

| VENDOR | DELIVERY | LICENCE | PRICE | CLASSIFICATION_AFTER_RESPONSE | FOLLOW_UP | EVIDENCE_REFERENCE |
|---|---|---|---|---|---|---|
| ETF Global | UNKNOWN | UNKNOWN | UNKNOWN | PENDING_RESPONSE | UNKNOWN | vendor_outbound/01_etf_global.md |
| LSEG / Lipper | UNKNOWN | UNKNOWN | UNKNOWN | PENDING_RESPONSE | UNKNOWN | vendor_outbound/02_lseg_lipper.md |
| Bloomberg | UNKNOWN | UNKNOWN | UNKNOWN | PENDING_RESPONSE | UNKNOWN | vendor_outbound/03_bloomberg.md |
| Morningstar | UNKNOWN | UNKNOWN | UNKNOWN | PENDING_RESPONSE | UNKNOWN | vendor_outbound/04_morningstar.md |
| ProShares / ProFunds | UNKNOWN | UNKNOWN | UNKNOWN | PENDING_RESPONSE | UNKNOWN | vendor_outbound/05_proshares.md |
| FactSet | UNKNOWN | UNKNOWN | UNKNOWN | PENDING_RESPONSE | UNKNOWN | vendor_outbound/06_factset.md |

`CLASSIFICATION_AFTER_RESPONSE` legal values: `VERIFIED_FULL` · `VERIFIED_PARTIAL` ·
`PLAUSIBLE_UNVERIFIED` · `REJECTED` · `PENDING_RESPONSE` · `NO_RESPONSE`.

`EVIDENCE_REFERENCE` should be updated on reply to point at the stored reply itself — the
email, transcript or attachment — not at the outbound message. **A vendor's own written
statement is the evidence; a summary of it is not.**

---

## 5. How to classify a reply

Under `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md`, unchanged.

**Do not classify from sales language.** *"Yes, we have historical data"* is insufficient
— it answers a question R2 never asked. Every candidate already has historical data; what
R2 needs is proof of **what was available, and when**.

A move to `VERIFIED_FULL` or `VERIFIED_PARTIAL` requires the vendor to have established:

1. **ORIGINAL_VINTAGE** — the stored historical value is the one originally delivered, or
   the superseded value is retained;
2. **PER_DATE_TIMESTAMP** — a receipt / load / publication timestamp is held **per record**,
   distinct from the date the value describes;
3. **TIMESTAMP_RESOLUTION** — enough resolution to answer availability against a decision
   time. `DATE_ONLY` is a real limitation and must be recorded as such, not rounded away;
4. **2016_ACID_TEST = PASS** — the sample actually delivered, with availability timestamps.

Coverage shorter than 2010-06-06 → 2021-12-31 gives at most `VERIFIED_PARTIAL`, recorded
with exact `HISTORY_START`. Partial coverage is never promoted to full.

**A `VERIFIED_PARTIAL` outcome does not reopen OD-5.** OD-5 is decided
(`PATH_A_TRUE_PIT_DAILY`). Partial coverage means an **additional explicit S1
sample-eligibility / sample-boundary rule is required under OD-5** — a rule made under the
decision, not a revision of it.

**2026-10-02 — correction to item 4 and to the §2 `2016_ACID_TEST` legend (CP-AUDIT-01
R2-G15, delegate decision D-R2-2026-10-02-01).** `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md` §2
governs. R6 (the 2016 acid test) must be **assessed** for every VERIFIED candidate;
`2016_ACID_TEST = PASS` is **required only for VERIFIED_FULL**, or where the claimed PIT scope
covers 2016-03-31 to 2016-04-05. A candidate whose proven PIT coverage starts after
2016-04-05 can be VERIFIED_PARTIAL with `2016_ACID_TEST = FAIL` (outside its scope), recorded
with its exact `HISTORY_START`. Item 4 above and the legend in §2 are read with this
correction; `R2_VENDOR_WAVE1_DISPATCH.md` §4 (the same stricter wording) is superseded by this
note. This is a record correction, not a methodology change.

## 6. Current state

```
VENDOR_WAVE1_AUTHORIZED     = YES
VENDOR_WAVE1_SENT_COUNT     = 6
VENDOR_WAVE1_TOTAL          = 6
VENDOR_WAVE1_STATUS         = ALL_SENT
ETF_GLOBAL                  = CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE
LSEG_LIPPER                 = SENT_AWAITING_RESPONSE
BLOOMBERG                   = SENT_AWAITING_RESPONSE
MORNINGSTAR                 = SALES_ROUTING_COMPLETE_AWAITING_RESPONSE   (SELF-REPORTED, §1)
MORNINGSTAR_SUPPORT         = ROUTED_TO_SALES_TEAM, Morningstar support case (number withheld)  (SELF-REPORTED, §1)
MORNINGSTAR_FREE_TRIAL      = APPLIED_NOT_ACTIVATED                       (SELF-REPORTED, §1)
PROSHARES_PROFUNDS          = SENT_AWAITING_RESPONSE
FACTSET                     = SENT_AWAITING_RESPONSE
RESPONSES_RECEIVED          = 0 (evidentiary)  (operational routing replies excluded)
SV1_VERIFIED_SOURCE         = NONE
R2_VENDOR_RESPONSE_REQUIRED = YES
R2_PATH_C_PARK_TRIGGER      = NO
TRIAL_ACTIVATION_AUTHORIZED = NO   (the 2026-09-22 free-trial application was carried out under
                                     an authorization recorded only in bd66324; decider,
                                     instant and scope UNKNOWN — DECISION_LOG COR-R2-G16)
PAID_TRIAL_AUTHORIZED       = NO
DATA_PURCHASE_AUTHORIZED    = NO
CONTRACT_AUTHORIZED         = NO
PAID_SUBSCRIPTION_AUTHORIZED= NO
TRIAL_CONSUMED              = NO
```

All six vendor enquiries have been dispatched. Morningstar's enquiry has been routed to
its Sales team (SELF-REPORTED, §1) and awaits a substantive answer. ETF Global's academic-affiliation
clarification was answered and remains awaiting the vendor's substantive response. No
source classification has changed. The PARK trigger is evidentiary and fires only if this
bounded process **closes** with no qualifying source and no material candidate remaining.
