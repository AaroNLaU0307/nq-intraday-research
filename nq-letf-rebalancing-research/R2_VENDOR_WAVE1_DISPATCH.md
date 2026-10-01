# R2_VENDOR_WAVE1_DISPATCH

```
RECORD_TYPE              = VENDOR_DISPATCH_PACKAGE
LINEAGE                  = R2
WAVE                     = 1
CREATED                  = 2026-09-20
VENDOR_WAVE1_COUNT       = 6
VENDOR_WAVE1_SEND_READY  = YES
VENDOR_WAVE1_SENT        = NO
STATUS                   = **NOT SENT. NOT AUTHORIZED TO SEND.**
```

**Nothing here has been sent.** No email, no web form, no phone call, no account, no
trial, no login request, no terms accepted, no invoice requested, no purchase. Aaron will
perform dispatch, or separately authorize it.

Copy-paste-ready message files live in **`vendor_outbound/`**, one per vendor, containing
only subject, contact route and message.

This package does **not** redo SV-1 and does **not** broaden the source search. It is the
already-accepted six enquiries, made dispatchable.

---

## 0. Why all six go out in parallel

Response latency is external and uncertain, and **sending in parallel does not affect
research outcomes**. Staging the enquiries by priority would let vendor response order
become a **source-selection forking path** — the earliest reply, rather than the best
evidence, would shape which source R2 pursues. That is a garden-of-forking-paths risk in
an operational disguise, and it is avoided by dispatching all six together.

**PRIORITY below is an information-value ranking only.** It says where the most decisive
answer is likely to come from. It does **not** stage dispatch, does not rank vendors by
expected quality, and must never be read as a pre-commitment to a source.

---

## 1. Disclosure boundary — binding on every message

Messages may disclose only:

- academic / research use;
- historical point-in-time ETF fund-size research;
- the five ETF tickers;
- the required dates and fields;
- the timestamp / vintage requirements.

Messages must **not** disclose: NQ or any futures instrument · alpha · any trading rule ·
the reset mechanism · `K_t` · `L_t` · any expected effect · any performance figure · any
R2 internal name, gap id or decision id.

The generated files already respect this, and a mechanical scan of `vendor_outbound/` for
forbidden terms returns nothing. **Do not add context when sending.**

### The 2016 verification sample

Every message asks for **2016-03-31, 2016-04-01, 2016-04-04 and 2016-04-05**, requesting
for each: value date · fund-size value (or NAV plus unadjusted shares outstanding) · first
receipt / load / publication timestamp · timezone · revision or vintage identifier.

These dates are a data-integrity probe. **Do not explain why they were chosen.** If asked,
"a known industry publication gap we use to test availability semantics" is true and
sufficient. The ProShares message uses the already-approved neutral wording and attributes
no error to anyone.

---

## 2. Dispatch table

| # | VENDOR | PRODUCT / TEAM | CONTACT_TYPE | STATUS |
|---|---|---|---|---|
| 1 | ETF Global | fund-flow / reference dataset; data or institutional sales | WEB_FORM | READY_NOT_SENT |
| 2 | LSEG / Lipper | Lipper Fund Data — "Fund Flows"; data-catalogue enquiries | WEB_FORM | READY_NOT_SENT |
| 3 | Bloomberg | Global ETP Flows Data Solution / Funds Data; Enterprise Data | WEB_FORM | READY_NOT_SENT |
| 4 | Morningstar | Morningstar Direct / Morningstar Data; Direct product support | EMAIL | READY_NOT_SENT |
| 5 | ProShares / ProFunds | public historical NAV data downloads; data operations | PHONE | READY_NOT_SENT |
| 6 | FactSet | ETF Standard DataFeed / ETF content; content and data sales | EMAIL | READY_NOT_SENT |

---

## 3. Vendor records

### 3.1 · PRIORITY 1 · ETF Global

```
VENDOR            = ETF Global (ETFG), founded 2011, New York
PRODUCT_OR_TEAM   = ETF Global fund-flow / reference dataset; data or institutional sales
PRIORITY          = 1
CONTACT_TYPE      = WEB_FORM  (phone fallback)
OFFICIAL_CONTACT_ROUTE = contact form at etfg.com · +1 (212) 223-3834 (New York HQ).
                    No department-specific address is publicly confirmed; the published
                    email format is [first-initial][last]@etfg.com.
MESSAGE           = vendor_outbound/01_etf_global.md
SUBJECT           = Historical point-in-time ETF fund-size data enquiry
DATE_PREPARED     = 2026-09-20
STATUS            = READY_NOT_SENT
RESPONSE_STATUS   = NONE
FOLLOW_UP_REQUIRED= UNKNOWN
SOURCE_CLASSIFICATION_BEFORE_CONTACT = PLAUSIBLE_UNVERIFIED
                    (STRONGEST_PUBLICLY_DOCUMENTED_PIT_METADATA_CANDIDATE)
```

**EVIDENCE_ALREADY_KNOWN.** API documentation defines, per record, `effective_date` ("when
the information was accurate or valid") and `processed_date` ("when ETF Global received and
processed the data"); both are stored and both are queryable filters. Fields `nav`,
`shares_outstanding`, `fund_flow`. Redistributed history begins 2017-04-03. A published
study used ETF Global daily leveraged-ETF AUM over 2012-2020. A WRDS listing shows
fund-flow coverage beginning 1993-01-25 — two decades before the firm existed, which
implies backfill.

**DECISIVE_UNKNOWN.** (a) whether a historical row preserves its **original**
`processed_date` after a correction; (b) whether an intraday receipt time exists;
(c) whether genuine pre-2017 coverage exists with authentic stamps; (d) whether
`shares_outstanding` is split-unadjusted.

**PASS_CONDITION.** Q13 "original, retained" **and** Q15 "previous versions retained"
**and** Q16 gives authentic pre-2017 coverage. Best case Q14 also yields an intraday time.

**FAIL_CONDITION.** Q13 "refreshed on reload", **or** Q16 "2017-04-03 is the true start and
earlier rows are reconstructed". Either caps the source at 2017-04-03 with date-only
granularity.

---

### 3.2 · PRIORITY 2 · LSEG / Lipper

```
VENDOR            = LSEG (London Stock Exchange Group), Lipper fund data
PRODUCT_OR_TEAM   = "Fund Flows" dataset within Lipper Fund Data; data-catalogue enquiries
PRIORITY          = 2
CONTACT_TYPE      = WEB_FORM
OFFICIAL_CONTACT_ROUTE = "Request details" form at
                    lseg.com/en/data-catalogue/funds/lipper-fund-data/fund-flows
MESSAGE           = vendor_outbound/02_lseg_lipper.md
SUBJECT           = Lipper Fund Flows — historical point-in-time ETF fund-size data enquiry
DATE_PREPARED     = 2026-09-20
STATUS            = READY_NOT_SENT
RESPONSE_STATUS   = NONE
FOLLOW_UP_REQUIRED= UNKNOWN
SOURCE_CLASSIFICATION_BEFORE_CONTACT = PLAUSIBLE_UNVERIFIED  (widest documented coverage)
```

**EVIDENCE_ALREADY_KNOWN.** Product page states: Data Frequency "Daily"; "estimated net
flows, gross inflows, gross outflows and assets under management at fund and share class
level"; covers "mutual funds and ETFs"; "daily flow history available from August 1, 2012
for non-US funds and from 1992 for US funds"; keyed on Lipper identifiers plus ISIN, SEDOL,
CUSIP.

**DECISIVE_UNKNOWN.** Every vintage / revision / receipt property — the page says nothing.
Also whether the daily **AUM** series (not only the flow series) reaches 1992 for these five
funds.

**PASS_CONDITION.** Q14 confirms retained original vintages plus queryable revisions with a
receipt timestamp, and Q13 confirms daily AUM across the window.

**FAIL_CONDITION.** Q14 "values are corrected in place; no prior version and no receipt
timestamp retained". Deep coverage without vintage semantics cannot satisfy OD-6 at any date.

---

### 3.3 · PRIORITY 3 · Bloomberg

```
VENDOR            = Bloomberg L.P.
PRODUCT_OR_TEAM   = Global ETP Flows Data Solution / Funds Data; Enterprise Data team
PRIORITY          = 3
CONTACT_TYPE      = WEB_FORM
OFFICIAL_CONTACT_ROUTE = "Contact Us" / request-information form on the Enterprise Data and
                    Data License pages at professional.bloomberg.com/products/data/
MESSAGE           = vendor_outbound/03_bloomberg.md
SUBJECT           = Global ETP Flows / Funds Data — historical point-in-time fund-size enquiry
DATE_PREPARED     = 2026-09-20
STATUS            = READY_NOT_SENT
RESPONSE_STATUS   = NONE
FOLLOW_UP_REQUIRED= UNKNOWN
SOURCE_CLASSIFICATION_BEFORE_CONTACT = PLAUSIBLE_UNVERIFIED
```

**EVIDENCE_ALREADY_KNOWN.** Announcement of 2025-12-11: "History includes a comprehensive
overview of historical flows and revisions dating back to 2007, enabling clients to adjust
analyses… reconstruct market conditions, and backtest models." Flows tracked by "monitoring
changes in NAV and shares outstanding". Delivered via Terminal, Data License and Enterprise
Products; SFTP, REST API or cloud. Separately, Bloomberg's documented point-in-time product
covers ~85,000 **companies** and does not mention funds.

**DECISIVE_UNKNOWN.** What a "revision" record contains; whether the 2007-2025 history is a
retained contemporaneous archive or a 2025 reconstruction; whether any point-in-time
treatment exists for fund / ETP assets.

**PASS_CONDITION.** Q14 "as-known-at-time retrieval supported" **and** Q15 "receipt
timestamps preserved back to 2010, from a contemporaneous archive".

**FAIL_CONDITION.** Q14 "corrected series, superseded values not retained", **or** Q15 "the
pre-2025 history was reconstructed". A reconstructed row cannot carry an authentic
availability stamp, whatever its accuracy.

---

### 3.4 · PRIORITY 4 · Morningstar

```
VENDOR            = Morningstar, Inc.
PRODUCT_OR_TEAM   = Morningstar Direct / Morningstar Data; Direct product support, who
                    route data-semantics questions to the data content team
PRIORITY          = 4
CONTACT_TYPE      = EMAIL  (web form and phone as alternatives)
OFFICIAL_CONTACT_ROUTE = MorningstarDirect@morningstar.com · +1 866 229-0216 ·
                    morningstar.com/company/contact-us
MESSAGE           = vendor_outbound/04_morningstar.md
SUBJECT           = Morningstar Direct — daily historical net assets, vintage and timestamp
                    enquiry
DATE_PREPARED     = 2026-09-20
STATUS            = READY_NOT_SENT
RESPONSE_STATUS   = NONE
FOLLOW_UP_REQUIRED= UNKNOWN
SOURCE_CLASSIFICATION_BEFORE_CONTACT = PLAUSIBLE_UNVERIFIED
```

**EVIDENCE_ALREADY_KNOWN.** Morningstar Direct release notes record the data points "Net
Assets - Share Class (Daily)" and "Fund Size (Surveyed-Daily)" under "Historical Cash Flow
Data", so a daily fund-size point exists. A "Net Assets Date" data point exists but records
the date a value **describes**. A published Federal Reserve study used Morningstar Direct
total net assets, NAV and shares outstanding for leveraged ETFs from 2006-06-19.

**DECISIVE_UNKNOWN.** History depth of the **daily** variant; five-fund coverage;
restatement policy; whether any load or publication timestamp exists.

**PASS_CONDITION.** Q13 gives a start at or before 2010-06-06 for all five **and** Q14
confirms retained original vintages with a load timestamp.

**FAIL_CONDITION.** Q15 confirmed — current-vintage only. Deep, accurate and unusable for
OD-6, which is exactly the trap the free ProShares file sets.

---

### 3.5 · PRIORITY 5 · ProShares / ProFunds

```
VENDOR            = ProShares / ProFunds (the ISSUER)
PRODUCT_OR_TEAM   = public "Historical NAVs for all ProShares ETFs" download and the
                    per-fund historical NAV files; data operations
PRIORITY          = 5
CONTACT_TYPE      = PHONE
OFFICIAL_CONTACT_ROUTE = ProShares Client Services, +1 866-776-5125 — ask to be routed to
                    data operations or product data. No published data-operations address.
MESSAGE           = vendor_outbound/05_proshares.md
SUBJECT           = Historical ProShares NAV/AUM data files — original publication timing
                    enquiry
DATE_PREPARED     = 2026-09-20
STATUS            = READY_NOT_SENT
RESPONSE_STATUS   = NONE
FOLLOW_UP_REQUIRED= UNKNOWN
SOURCE_CLASSIFICATION_BEFORE_CONTACT = PLAUSIBLE_UNVERIFIED
```

**EVIDENCE_ALREADY_KNOWN.** The published file carries an "Assets Under Management" column
today; that column is **absent** from the archived 2011 and 2012 vintages and present by
2014-03-26. No archival evidence exists at all for 2012-09-26 to 2014-03-25. The ProShares
FAQ documents the NAV **calculation** time ("usually 4:00 p.m. ET") and says nothing about
posting time. A CUSIP redistribution restriction took effect 2015-08-01.

**DECISIVE_UNKNOWN.** Whether any batch log or historical file version from 2010-2021 was
retained, and whether original publication timestamps can be established.

**SCOPE NOTE — what this vendor can and cannot settle.** ProShares can establish
**issuer-side publication / batch** facts: when the file was written, and when a row was
back-filled. It **cannot** speak to when any vendor's users received a value — that is
established by a vendor holding genuine historical receipt / load logs. Both questions
matter and neither party subsumes the other.

**PASS_CONDITION.** Q13 or Q14 yes. Retained file versions or batch logs would be
transformative: it is the one route that could reach 2010, and it would settle Q15 and Q16
directly.

**FAIL_CONDITION.** "We publish a current file and keep no versions or logs" — the expected
answer. It closes the issuer route cleanly and leaves vendor receipt logs as the remaining
path.

---

### 3.6 · PRIORITY 6 · FactSet

```
VENDOR            = FactSet Research Systems
PRODUCT_OR_TEAM   = ETF Standard DataFeed / FactSet ETF data; content and data sales
PRIORITY          = 6
CONTACT_TYPE      = EMAIL  (web form as alternative)
OFFICIAL_CONTACT_ROUTE = sales@factset.com · factset.com/contact-us
                    (existing clients: support@factset.com / +1 877-322-8738)
MESSAGE           = vendor_outbound/06_factset.md
SUBJECT           = FactSet ETF data — daily historical fund assets, history depth and
                    vintage enquiry
DATE_PREPARED     = 2026-09-20
STATUS            = READY_NOT_SENT
RESPONSE_STATUS   = NONE
FOLLOW_UP_REQUIRED= UNKNOWN
SOURCE_CLASSIFICATION_BEFORE_CONTACT = PLAUSIBLE_UNVERIFIED (weak)
```

**EVIDENCE_ALREADY_KNOWN.** The public ETF API catalogue exposes `price` and `timeSeries`
("historical NAV") and `fundFlows` ("cash inflow/outflows for various time periods" —
period aggregates, not a daily series). No daily total-net-assets series, no
shares-outstanding series and no availability field are documented. FactSet Fundamentals
Point-in-Time covers **companies** from February 1999.

**DECISIVE_UNKNOWN.** Whether the institutional ETF Standard DataFeed carries a daily
fund-size series at all, and with what history and vintage support.

**PASS_CONDITION.** Q13 names a genuine daily fund-size field with adequate depth (Q14) and
Q15 confirms vintage or timestamp support.

**FAIL_CONDITION.** Q15 "point-in-time treatment is available for company fundamentals
only" — the expected answer, matching the public documentation.

---

## 4. Classifying the responses when they arrive

Record answers in `R2_VENDOR_RESPONSE_TRACKER.md`. Classification remains
`VERIFIED_FULL | VERIFIED_PARTIAL | PLAUSIBLE_UNVERIFIED | REJECTED`, under the standard in
`R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md`.

**Do not classify from sales language.** A representative saying *"yes, we have historical
data"* is **insufficient** — it answers a question R2 never asked. The decisive semantics
are: original vintage retained · per-date receipt / publication timestamp · timestamp
resolution · as-known-at-time query · the 2016 sample actually delivered. A vendor moves to
`VERIFIED_*` only on evidence for those, not on assurance about them.

Leave any fact the vendor did not actually answer as `UNKNOWN`. **Do not manufacture empty
factual answers**, and do not let a confident tone fill a gap.

---

## 5. Do not send

Even though this package is ready, do **not**: send email · submit a web form · call ·
create an account · start a trial · request a login · accept terms · request an invoice ·
purchase anything.

```
VENDOR_WAVE1_SENT = NO
R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
PAID_PURCHASE_REQUIRED                = UNKNOWN / CONDITIONAL
R2_PATH_C_PARK_TRIGGER                = NO
```

The PARK trigger is **evidentiary**: it fires only if this bounded enquiry process **closes**
with no qualifying source and no material candidate remaining. A calendar deadline is not
scientific evidence.
