# R2_SV1_VENDOR_ENQUIRY_PACKET

```
RECORD_TYPE           = SEND_READY_ENQUIRY_PACKET
LINEAGE               = R2
CREATED               = 2026-09-19
FINALIZED             = 2026-09-20
VENDOR_ENQUIRIES_SEND_READY = YES
VENDOR_ENQUIRIES_SENT       = NO
STATUS                = **NOT SENT. NOT AUTHORIZED TO SEND.**
AUTHORITY             = Sending any message below requires an explicit Aaron decision.
```

**Nothing here has been sent.** No enquiry, no form submission, no email, no trial, no
account, no quote request, no purchase. The only outward action taken while finalizing
this packet was reading public contact pages to identify the correct route.

Six vendors, ordered by **evidence**, not brand. Each message is self-contained and
copy-paste ready.

---

## 0. Disclosure boundary — binding on every message

Describe the use case **only** as:

> *historical point-in-time ETF fund-size research*

**Do not disclose:** expected alpha · strategy performance · proprietary trading logic ·
the `K_t` formula · the `L_t` normalisation · the NQ futures side · any hypothesis ·
any timing parameter · why 2010-2021 · why these five funds constitute a universe rather
than a convenience sample · any R2 internals.

The five tickers, the date range and the 2016 verification dates **are** named — they are
the question. Nothing states what is being measured with them. The messages below already
respect this; **do not add context when sending**.

Every question is factual and answerable. None asks for advice. None signals intent to
buy. A "yes" to any of them commits R2 to nothing.

---

## 1. Priority order and rationale

Ranked by how much the answer moves R2, given what SV-1 already established.

| # | vendor | why here | decisive unknown |
|---|---|---|---|
| **1** | **ETF Global** | the **only** candidate whose public documentation defines a stored, queryable availability field (`processed_date`) alongside `effective_date` | is a historical row's `processed_date` the *original* receipt date, and does coverage exist before 2017-04-03? |
| **2** | **LSEG / Lipper** | the **only** candidate documented to span the entire window — daily, AUM at fund and share-class level, US history from 1992 | does any vintage, revision or receipt semantics exist at all? |
| **3** | **Bloomberg** | the only public claim of a **revision history reaching 2007**, i.e. most of R2's window | is a "revision" a dated chain of successive values, or a corrected series with a note? |
| **4** | **Morningstar** | daily net-assets data points documented; deep history plausible (Tuzun used Morningstar Direct LETF data from 2006-06-19) | history depth of the *daily* variant, restatement policy, any availability stamp |
| **5** | **ProShares** | the **issuer** — uniquely placed on issuer-side publication and batch facts | were 2010-2021 batch logs or file versions retained? |
| **6** | **FactSet** | weakest public evidence; the institutional feed is not publicly documented | does the ETF Standard DataFeed carry a daily fund-size series at all? |

**On ranking ETF Global first.** It is the
`STRONGEST_PUBLICLY_DOCUMENTED_PIT_METADATA_CANDIDATE` — best-documented, **not**
known-best. Bloomberg, LSEG, Morningstar and FactSet are all `PLAUSIBLE_UNVERIFIED` and
none has been asked; any of them may hold more than it publishes. Priority reflects
information yield per question, not expected superiority.

**On ranking ProShares fifth, not first.** SV-1's earlier claim that ProShares is the only
party who can answer the 2016 case is **withdrawn**. Two distinct facts exist:

| fact | who can establish it |
|---|---|
| issuer-side **publication / batch** facts — when the file was written, why the batch did not run, when the row was back-filled | ProShares |
| **user-side availability** — when *its users* received the value | any vendor with genuine historical receipt / load logs |

OD-6 asks whether the value for `t-1` was available before the decision time. A vendor's
authentic receipt log answers that for that vendor's subscribers, independently of the
issuer.

**SIX / Ultumus is deliberately absent.** Its rolling 5-year lookback is published and
decisive for the 2010-2021 question; an enquiry would only confirm a documented limit. It
returns in §8 as a forward-looking option, and only if Aaron asks.

---

## 2. PRIORITY 1 — ETF Global

```
VENDOR                = ETF Global (ETFG), founded 2011, New York
PRODUCT / TEAM        = ETF Global fund-flow / reference dataset; data or institutional
                        sales team (small firm — a direct technical question is likely to
                        reach the right person)
OFFICIAL_CONTACT_ROUTE= contact form at etfg.com · phone +1 (212) 223-3834 (NY HQ).
                        A department-specific address is not publicly confirmed; the
                        published email format is [first-initial][last]@etfg.com.
EVIDENCE_ALREADY_KNOWN= API documentation defines, per record, `effective_date` ("when the
                        information was accurate or valid") and `processed_date` ("when
                        ETF Global received and processed the data"); both are stored and
                        both are queryable filters. Fields `nav`, `shares_outstanding`,
                        `fund_flow`. Redistributed history begins 2017-04-03. A published
                        study used ETF Global daily LETF AUM over 2012-2020. A WRDS listing
                        shows fund-flow coverage beginning 1993-01-25 — two decades before
                        the firm existed, which implies backfill.
DECISIVE_UNKNOWN      = (a) does a historical row preserve its ORIGINAL processed_date
                        after a correction; (b) is there an intraday receipt time, or only
                        a date; (c) does genuine pre-2017 coverage exist with authentic
                        stamps; (d) is shares_outstanding split-unadjusted.
```

### SEND_READY_MESSAGE

> **Subject: Historical point-in-time ETF fund-size data — availability enquiry**
>
> Hello,
>
> I am conducting historical point-in-time ETF fund-size research and am evaluating which
> data sources can establish not only what a fund's size was on a historical date, but
> **what value was actually available, and when**.
>
> The funds I need are five US-listed ProShares Nasdaq-100 ETFs — **QLD, QID, PSQ, TQQQ,
> SQQQ** — over approximately **2010-06-06 to 2021-12-31**.
>
> 1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
>    contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
>    respective inception dates?
> 2. Are the historical records **original vintage**, or retrospectively revised /
>    restated?
> 3. Do you retain the historical timestamp at which each daily value was received,
>    loaded, published, or first made available to users?
> 4. Is that timestamp **date only**, or date plus intraday time plus timezone?
> 5. Can historical data be queried **"as known at timestamp X"**, or through immutable
>    historical snapshots / vintages?
> 6. Could you provide a small verification sample for **2016-03-31, 2016-04-01,
>    2016-04-04 and 2016-04-05** for the five ETFs, including value date, fund-size value,
>    first receipt / load / publication timestamp, timezone, and a revision or vintage
>    identifier if one exists?
> 7. Are delisted ETFs preserved historically?
> 8. Which stable identifiers are included — CUSIP, ISIN, SEDOL, SEC Series ID, an
>    internal permanent ID?
> 9. What is the earliest historical coverage date?
> 10. What delivery formats exist — API, bulk files, cloud dataset, SFTP?
> 11. What academic or research licence options exist?
> 12. What pricing applies for only the historical dataset described above?
>
> Four questions specific to your documented schema:
>
> 13. Your fund-flow records carry both `effective_date` and `processed_date`, the latter
>     documented as the date ETF Global received and processed the data. For a **historical**
>     row, is the stored `processed_date` the date you **originally** received that value,
>     or is it updated if the value is later corrected or reloaded?
> 14. Is an **intraday** processing or receipt timestamp held internally, even if the
>     published field is date-only?
> 15. When a value is corrected, is the **previous record version retained**, or replaced?
> 16. The redistributed history begins **2017-04-03**. Does coverage before that date exist
>     in another product or archive — and if so, do those earlier records carry a genuine
>     `processed_date`, or were they constructed retrospectively?
>
> Thank you,
> [name]

```
WHAT_COUNTS_AS_PASS = Q13 "original, retained" AND Q15 "previous versions retained" AND
                      Q16 gives authentic pre-2017 coverage. Best case Q14 also yields an
                      intraday time. That is a credible VERIFIED_PARTIAL or better.
WHAT_COUNTS_AS_FAIL = Q13 "refreshed on reload", OR Q16 "2017-04-03 is the true start and
                      earlier rows are reconstructed". Either answer caps the source at
                      2017-04-03 with date-only granularity, which cannot satisfy OD-6 for
                      the great majority of the window.
```

---

## 3. PRIORITY 2 — LSEG / Lipper

```
VENDOR                = LSEG (London Stock Exchange Group), Lipper fund data
PRODUCT / TEAM        = "Fund Flows" dataset within Lipper Fund Data; data sales /
                        data-catalogue enquiries. LSEG also operates a long-standing
                        academic research programme worth naming.
OFFICIAL_CONTACT_ROUTE= "Request details" form on the product page at
                        lseg.com/en/data-catalogue/funds/lipper-fund-data/fund-flows
                        (the official route for this dataset)
EVIDENCE_ALREADY_KNOWN= Product page states: Data Frequency "Daily"; "estimated net flows,
                        gross inflows, gross outflows and assets under management at fund
                        and share class level"; covers "mutual funds and ETFs"; "daily flow
                        history available from August 1, 2012 for non-US funds and from
                        1992 for US funds"; keyed on Lipper identifiers plus ISIN, SEDOL,
                        CUSIP.
DECISIVE_UNKNOWN      = every vintage/revision/receipt property — the page says nothing.
                        Also whether the daily AUM series itself (not only the flow series)
                        reaches 1992 for these five funds.
```

### SEND_READY_MESSAGE

> **Subject: Lipper Fund Flows — historical point-in-time ETF fund-size enquiry**
>
> Hello,
>
> I am conducting historical point-in-time ETF fund-size research and am evaluating which
> data sources can establish not only what a fund's size was on a historical date, but
> **what value was actually available, and when**.
>
> The funds I need are five US-listed ProShares Nasdaq-100 ETFs — **QLD, QID, PSQ, TQQQ,
> SQQQ** — over approximately **2010-06-06 to 2021-12-31**.
>
> 1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
>    contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
>    respective inception dates?
> 2. Are the historical records **original vintage**, or retrospectively revised /
>    restated?
> 3. Do you retain the historical timestamp at which each daily value was received,
>    loaded, published, or first made available to users?
> 4. Is that timestamp **date only**, or date plus intraday time plus timezone?
> 5. Can historical data be queried **"as known at timestamp X"**, or through immutable
>    historical snapshots / vintages?
> 6. Could you provide a small verification sample for **2016-03-31, 2016-04-01,
>    2016-04-04 and 2016-04-05** for the five ETFs, including value date, fund-size value,
>    first receipt / load / publication timestamp, timezone, and a revision or vintage
>    identifier if one exists?
> 7. Are delisted ETFs preserved historically?
> 8. Which stable identifiers are included — CUSIP, ISIN, SEDOL, SEC Series ID, an
>    internal permanent ID?
> 9. What is the earliest historical coverage date?
> 10. What delivery formats exist — API, bulk files, cloud dataset, SFTP?
> 11. What academic or research licence options exist?
> 12. What pricing applies for only the historical dataset described above?
>
> Two questions specific to Lipper Fund Flows:
>
> 13. The dataset is documented as carrying daily flow history from 1992 for US funds and
>     "assets under management at fund and share class level". Does the **AUM series
>     itself** extend that far at daily frequency for US ETFs, or only the flow series —
>     and what is the earliest daily net-assets value you hold for each of these five funds?
> 14. When a fund company revises a figure, does Lipper retain the **original vintage** and
>     a load or receipt timestamp, and are **historical revisions queryable** — for example,
>     retrieving the value as it stood in the database on a past date?
>
> Thank you,
> [name]

```
WHAT_COUNTS_AS_PASS = Q14 confirms retained original vintages plus queryable revisions
                      with a receipt timestamp, and Q13 confirms daily AUM across the
                      window. That is the best available outcome — full-window coverage
                      with availability semantics.
WHAT_COUNTS_AS_FAIL = Q14 "values are corrected in place, no prior version and no receipt
                      timestamp is retained". Deep coverage without vintage semantics
                      cannot satisfy OD-6 at any date, and the candidate closes.
```

---

## 4. PRIORITY 3 — Bloomberg

```
VENDOR                = Bloomberg L.P.
PRODUCT / TEAM        = Global ETP Flows Data Solution / Funds Data, delivered via
                        Bloomberg Data License and Terminal; Enterprise Data team
OFFICIAL_CONTACT_ROUTE= "Contact Us" / request-information form on the Enterprise Data and
                        Data License pages at professional.bloomberg.com/products/data/.
                        Existing Terminal clients would instead use the support desk.
EVIDENCE_ALREADY_KNOWN= Announcement of 2025-12-11: "History includes a comprehensive
                        overview of historical flows and revisions dating back to 2007,
                        enabling clients to adjust analyses, refine portfolio strategies,
                        reconstruct market conditions, and backtest models." Flows tracked
                        by "monitoring changes in NAV and shares outstanding". Delivered
                        via Terminal, Data License and Enterprise Products; SFTP, REST API
                        or cloud. Separately, Bloomberg's documented point-in-time product
                        (Company Financials, Estimates and Pricing) covers ~85,000
                        COMPANIES and does not mention funds.
DECISIVE_UNKNOWN      = what a "revision" record contains; whether 2007-2025 history is a
                        retained contemporaneous archive or a 2025 reconstruction; whether
                        any PIT treatment exists for fund/ETP assets.
```

### SEND_READY_MESSAGE

> **Subject: Global ETP Flows / Funds Data — historical point-in-time fund-size enquiry**
>
> Hello,
>
> I am conducting historical point-in-time ETF fund-size research and am evaluating which
> data sources can establish not only what a fund's size was on a historical date, but
> **what value was actually available, and when**.
>
> The funds I need are five US-listed ProShares Nasdaq-100 ETFs — **QLD, QID, PSQ, TQQQ,
> SQQQ** — over approximately **2010-06-06 to 2021-12-31**.
>
> 1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
>    contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
>    respective inception dates?
> 2. Are the historical records **original vintage**, or retrospectively revised /
>    restated?
> 3. Do you retain the historical timestamp at which each daily value was received,
>    loaded, published, or first made available to users?
> 4. Is that timestamp **date only**, or date plus intraday time plus timezone?
> 5. Can historical data be queried **"as known at timestamp X"**, or through immutable
>    historical snapshots / vintages?
> 6. Could you provide a small verification sample for **2016-03-31, 2016-04-01,
>    2016-04-04 and 2016-04-05** for the five ETFs, including value date, fund-size value,
>    first receipt / load / publication timestamp, timezone, and a revision or vintage
>    identifier if one exists?
> 7. Are delisted ETFs preserved historically?
> 8. Which stable identifiers are included — CUSIP, ISIN, SEDOL, SEC Series ID, FIGI, an
>    internal permanent ID?
> 9. What is the earliest historical coverage date?
> 10. What delivery formats exist — API, bulk files, terminal export, cloud dataset, SFTP?
> 11. What academic or research licence options exist?
> 12. What pricing applies for only the historical dataset described above?
>
> Three questions specific to your ETP data:
>
> 13. Which **exact dataset** carries daily historical AUM, NAV and shares outstanding for
>     US ETPs, and through which product is it licensed?
> 14. That dataset is described as including "historical flows and revisions dating back to
>     2007". Does the revision history support **as-known-at-time retrieval** — retrieving a
>     value as Bloomberg held it on a past date — or does it record that a correction
>     occurred without retaining the superseded value?
> 15. Are **receipt or load timestamps preserved back to 2010**? Relatedly, was the
>     2007-onward history assembled from Bloomberg's contemporaneous archive, or
>     reconstructed later from other sources?
>
> Thank you,
> [name]

```
WHAT_COUNTS_AS_PASS = Q14 "as-known-at-time retrieval supported" AND Q15 "receipt
                      timestamps preserved back to 2010, from a contemporaneous archive".
                      That would be a genuinely strong source across most of the window.
WHAT_COUNTS_AS_FAIL = Q14 "corrected series, superseded values not retained", OR Q15 "the
                      pre-2025 history was reconstructed". A reconstructed row cannot carry
                      an authentic availability stamp, whatever its accuracy.
```

---

## 5. PRIORITY 4 — Morningstar

```
VENDOR                = Morningstar, Inc.
PRODUCT / TEAM        = Morningstar Direct / Morningstar Data; Direct product support, who
                        route data-semantics questions to the data content team
OFFICIAL_CONTACT_ROUTE= MorningstarDirect@morningstar.com · +1 866 229-0216 ·
                        or the Contact Us form at morningstar.com/company/contact-us
EVIDENCE_ALREADY_KNOWN= Morningstar Direct release notes record the data points
                        "Net Assets - Share Class (Daily)" and "Fund Size (Surveyed-Daily)"
                        under "Historical Cash Flow Data", so a daily fund-size point
                        exists. A "Net Assets Date" data point exists but records the date a
                        value DESCRIBES. A published Federal Reserve study used Morningstar
                        Direct total net assets, NAV and shares outstanding for leveraged
                        ETFs from 2006-06-19.
DECISIVE_UNKNOWN      = history depth of the DAILY variant; five-fund coverage; restatement
                        policy; whether any load or publication timestamp exists.
```

### SEND_READY_MESSAGE

> **Subject: Morningstar Direct — daily historical net assets, vintage and timestamp enquiry**
>
> Hello,
>
> I am conducting historical point-in-time ETF fund-size research and am evaluating which
> data sources can establish not only what a fund's size was on a historical date, but
> **what value was actually available, and when**.
>
> The funds I need are five US-listed ProShares Nasdaq-100 ETFs — **QLD, QID, PSQ, TQQQ,
> SQQQ** — over approximately **2010-06-06 to 2021-12-31**.
>
> 1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
>    contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
>    respective inception dates?
> 2. Are the historical records **original vintage**, or retrospectively revised /
>    restated?
> 3. Do you retain the historical timestamp at which each daily value was received,
>    loaded, published, or first made available to users?
> 4. Is that timestamp **date only**, or date plus intraday time plus timezone?
> 5. Can historical data be queried **"as known at timestamp X"**, or through immutable
>    historical snapshots / vintages?
> 6. Could you provide a small verification sample for **2016-03-31, 2016-04-01,
>    2016-04-04 and 2016-04-05** for the five ETFs, including value date, fund-size value,
>    first receipt / load / publication timestamp, timezone, and a revision or vintage
>    identifier if one exists?
> 7. Are delisted ETFs preserved historically?
> 8. Which stable identifiers are included — CUSIP, ISIN, SEDOL, SEC Series ID, an
>    internal permanent ID?
> 9. What is the earliest historical coverage date?
> 10. What delivery formats exist — API, bulk files, Direct export, cloud dataset, SFTP?
> 11. What academic or research licence options exist?
> 12. What pricing applies for only the historical dataset described above?
>
> Three questions specific to Morningstar Direct:
>
> 13. From what date are the data points **"Net Assets - Share Class (Daily)"** and
>     **"Fund Size (Surveyed-Daily)"** populated for US ETFs, and specifically for these
>     five funds?
> 14. Do Morningstar Direct or Morningstar Data retain **original historical daily
>     net-asset vintages** when a figure is later revised, and does any **load or
>     publication timestamp** exist alongside the "Net Assets Date"?
> 15. If neither is retained, is it correct that the historical daily net-assets series is
>     **current-vintage only** — that is, it reflects today's best value for each past date?
>
> Thank you,
> [name]

```
WHAT_COUNTS_AS_PASS = Q13 gives a start at or before 2010-06-06 for all five AND Q14
                      confirms retained original vintages with a load timestamp.
WHAT_COUNTS_AS_FAIL = Q15 confirmed — current-vintage only. Deep, accurate and unusable
                      for OD-6, which is exactly the trap the free ProShares file sets.
```

---

## 6. PRIORITY 5 — ProShares / ProFunds

```
VENDOR                = ProShares / ProFunds (the ISSUER)
PRODUCT / TEAM        = the public "Historical NAVs for all ProShares ETFs" data download
                        and the per-fund historical NAV files; this is a data-operations
                        question, not a retail one
OFFICIAL_CONTACT_ROUTE= ProShares Client Services, +1 866-776-5125 (the only public door;
                        ask to be routed to data operations or product data)
EVIDENCE_ALREADY_KNOWN= The published file carries an "Assets Under Management" column
                        today; that column is ABSENT from the archived 2011 and 2012
                        vintages and present by 2014-03-26. No archival evidence exists at
                        all for 2012-09-26 to 2014-03-25. The ProShares FAQ documents the
                        NAV CALCULATION time ("usually 4:00 p.m. ET") and says nothing about
                        posting time. A CUSIP redistribution restriction took effect
                        2015-08-01.
DECISIVE_UNKNOWN      = whether any batch log or historical file version from 2010-2021 was
                        retained, and whether original publication timestamps can be
                        established.
NOTE                  = ProShares can settle ISSUER-SIDE publication facts. It cannot speak
                        to when any vendor's users received a value. Both matter; neither
                        subsumes the other.
```

### SEND_READY_MESSAGE

> **Subject: Historical ProShares NAV/AUM data files — original publication timing enquiry**
>
> Hello,
>
> I am conducting historical point-in-time ETF fund-size research using the public
> ProShares historical NAV data downloads, and I am trying to establish not only what each
> fund's size was on a historical date, but **when that value was originally published**.
>
> The funds I need are **QLD, QID, PSQ, TQQQ and SQQQ**, over approximately **2010-06-06 to
> 2021-12-31**.
>
> 1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
>    contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
>    respective inception dates?
> 2. Are the historical records in the current file **original vintage**, or have values
>    been retrospectively revised or restated since first publication?
> 3. Do you retain the historical timestamp at which each daily value was first published
>    to the public data downloads?
> 4. Is any such timestamp **date only**, or date plus intraday time plus timezone?
> 5. Are historical **versions** of these files retained, such that the file as published on
>    a past date could be retrieved?
> 6. Could you provide, or help document, the publication timing for **2016-03-31,
>    2016-04-01, 2016-04-04 and 2016-04-05** for the five ETFs — value date, fund-size
>    value, and original publication timestamp with timezone?
> 7. Are files for closed or liquidated ProShares products preserved historically?
> 8. Which stable identifiers are carried in the historical files — CUSIP, ISIN, SEC Series
>    ID, an internal permanent ID?
> 9. What is the earliest date for which you hold the published file in its original form
>    (as distinct from the earliest row in today's file)?
> 10. What delivery formats exist for historical data beyond the public CSV downloads?
> 11. Are there academic or research access arrangements for historical fund data?
> 12. Does any pricing apply for access to historical file versions or publication metadata?
>
> Four issuer-specific questions:
>
> 13. Are **historical batch logs**, or historical versions of the daily NAV/AUM files from
>     2010-2021, retained anywhere — including internally or by a service provider?
> 14. Can the **original publication timestamp** of a given historical row be established
>     from your records?
> 15. The "Assets Under Management" column appears in the published file by 2014 but is not
>     present in archived copies from 2011 and 2012. **When was that column added** to the
>     published file?
> 16. We observed an archived period in early April 2016 where the public historical file
>     appeared to lag the trading calendar, and would like to understand the original
>     publication timing for those dates.
>
> Thank you,
> [name]

```
WHAT_COUNTS_AS_PASS = Q13 or Q14 yes. Retained file versions or batch logs would be
                      transformative: it is the one route that could reach 2010, and it
                      would settle Q15 and Q16 directly.
WHAT_COUNTS_AS_FAIL = "we publish a current file and keep no versions or logs" — the
                      expected answer. It closes the issuer route cleanly and leaves the
                      vendor receipt-log route as the only remaining path.
NOTE ON TONE        = Q16 is phrased as an observation and a request to understand, not as
                      an allegation. Do not reword it to attribute an error.
```

---

## 7. PRIORITY 6 — FactSet

```
VENDOR                = FactSet Research Systems
PRODUCT / TEAM        = ETF Standard DataFeed / FactSet ETF data; content and data sales
OFFICIAL_CONTACT_ROUTE= sales@factset.com or the form at factset.com/contact-us for new
                        data content (existing clients would use support@factset.com /
                        +1 877-322-8738)
EVIDENCE_ALREADY_KNOWN= The public ETF API catalogue exposes `price` and `timeSeries`
                        ("historical NAV") and `fundFlows` ("cash inflow/outflows for
                        various time periods" — period aggregates, not a daily series).
                        No daily total-net-assets series, no shares-outstanding series and
                        no availability field are documented. FactSet Fundamentals
                        Point-in-Time covers COMPANIES from February 1999.
DECISIVE_UNKNOWN      = whether the institutional ETF Standard DataFeed carries a daily
                        fund-size series at all, and with what history and vintage support.
```

### SEND_READY_MESSAGE

> **Subject: FactSet ETF data — daily historical fund assets, history depth and vintage enquiry**
>
> Hello,
>
> I am conducting historical point-in-time ETF fund-size research and am evaluating which
> data sources can establish not only what a fund's size was on a historical date, but
> **what value was actually available, and when**.
>
> The funds I need are five US-listed ProShares Nasdaq-100 ETFs — **QLD, QID, PSQ, TQQQ,
> SQQQ** — over approximately **2010-06-06 to 2021-12-31**.
>
> 1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
>    contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
>    respective inception dates?
> 2. Are the historical records **original vintage**, or retrospectively revised /
>    restated?
> 3. Do you retain the historical timestamp at which each daily value was received,
>    loaded, published, or first made available to users?
> 4. Is that timestamp **date only**, or date plus intraday time plus timezone?
> 5. Can historical data be queried **"as known at timestamp X"**, or through immutable
>    historical snapshots / vintages?
> 6. Could you provide a small verification sample for **2016-03-31, 2016-04-01,
>    2016-04-04 and 2016-04-05** for the five ETFs, including value date, fund-size value,
>    first receipt / load / publication timestamp, timezone, and a revision or vintage
>    identifier if one exists?
> 7. Are delisted ETFs preserved historically?
> 8. Which stable identifiers are included — CUSIP, ISIN, SEDOL, SEC Series ID, an
>    internal permanent ID?
> 9. What is the earliest historical coverage date?
> 10. What delivery formats exist — API, bulk files, cloud dataset, SFTP?
> 11. What academic or research licence options exist?
> 12. What pricing applies for only the historical dataset described above?
>
> Three questions specific to FactSet's ETF content:
>
> 13. Which **exact field** carries an ETF's historical total assets, and in which product
>     does it live? The public ETF API appears to expose historical NAV and period fund-flow
>     aggregates rather than a daily fund-size series.
> 14. What is the **historical depth** of that field for US ETFs, and specifically for these
>     five funds?
> 15. Does any **vintage or timestamp support** exist for fund assets, comparable to
>     FactSet Fundamentals Point-in-Time for company fundamentals?
>
> Thank you,
> [name]

```
WHAT_COUNTS_AS_PASS = Q13 names a genuine daily fund-size field with adequate depth (Q14)
                      and Q15 confirms vintage or timestamp support.
WHAT_COUNTS_AS_FAIL = Q15 "point-in-time treatment is available for company fundamentals
                      only" — the expected answer, matching the public documentation.
```

---

## 8. SIX / Ultumus — a different question, and only if Aaron asks

Ultumus publishes a **rolling 5-year lookback** with version control and source-file
traceability, so the retrospective question is already settled: it cannot reach 2010-2021.
No enquiry is needed to establish that.

The live question is forward-looking and is an **Owner decision, not an enquiry**: whether
Aaron wants a commercial PIT feed running alongside the free forward collection now in
place. If he does, ask only:

> 1. Is the 5-year historical lookback a **rolling retention window**, or a fixed archive
>    start date?
> 2. Is historical receipt-time metadata included in the standard product, or is it a
>    custom request?

---

## 9. What answers would do to R2's state

| outcome | consequence |
|---|---|
| any vendor confirms retained original vintages **with** a receipt timestamp covering the window | a candidate reaches `VERIFIED_FULL` or `VERIFIED_PARTIAL`; a data-acquisition decision becomes possible |
| coverage confirmed but **starting later** than 2010-06-06 | `VERIFIED_PARTIAL`. An **additional explicit S1 sample-eligibility / sample-boundary rule is then required under OD-5** — a rule made under the decision, **not** a reopening of OD-5 |
| ProShares confirms retained batch logs or file versions | the one route that could reach 2010, and it settles the 2016 case on the issuer side |
| all six answer "no availability semantics" and the enquiry process **closes** with no material candidate remaining | `PATH_C_PARK_TRIGGER = YES` — an **evidentiary** trigger. A calendar deadline is not scientific evidence and cannot fire it |

```
R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
PAID_PURCHASE_REQUIRED                = UNKNOWN / CONDITIONAL
```

A paid purchase is **not yet known to be required**. An answer may reveal a free or
academic route, or that no qualifying product exists at any price. Nothing in this packet
authorizes contact, and no answer authorizes a purchase — acquisition is a separate Owner
decision.
