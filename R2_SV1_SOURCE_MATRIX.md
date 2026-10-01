# R2_SV1_SOURCE_MATRIX

```
RECORD_TYPE = SOURCE_MATRIX
LINEAGE     = R2
TASK        = SV-1
CREATED     = 2026-09-19
STANDARD    = R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md (written before any candidate was judged)
```

Nineteen candidates across nine classes. **No candidate is classified on an overall
impression**; every cell traces to a named document, schema, sample file or local R2
record. `n/v` = not verified (no document found). `AUTH` = `AUTHENTICATED_ACCESS_REQUIRED`.

---

## 1. The matrix

| # | SOURCE | PRODUCT | FIELD | DAILY | HISTORY_START | ALL_5_FUNDS | ORIGINAL_VINTAGE | PER_DATE_AVAILABILITY_TIMESTAMP | 2016_ACID | SURVIVORSHIP | OBTAINABLE_NOW | COST_CLASS | CLASSIFICATION |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ProShares/ProFunds | per-fund + master `historical_nav.csv` | `Assets Under Management` | YES | file: fund inception; **field: 2014-03-26 evidenced** | YES | **NO** — current-vintage file | **NO** — no per-row publication stamp | **FAIL** | n/a (issuer) | YES | FREE | **REJECTED** (R4, R5) |
| 2 | ProShares | issuer archive / batch logs (institutional) | unknown | n/v | n/v | n/v | n/v | n/v | **UNKNOWN** | n/a | enquiry only | n/v | **PLAUSIBLE_UNVERIFIED** |
| 3 | Morningstar | Direct | `Net Assets – Share Class (Daily)`, `Fund Size (Surveyed-Daily)` | **YES** (E-A) | n/v for the daily variant | n/v | n/v | **n/v** — `Net Assets Date` is a VALUE date | UNKNOWN | likely (2007 methodology) | YES (seat) | PAID | **PLAUSIBLE_UNVERIFIED** |
| 4 | ETF Global | direct licence | daily AUM (per Mathis & Moerke) | YES (E-C) | 2012 (E-C, paper sample) | n/v | n/v | n/v | UNKNOWN | n/v | YES | PAID | **PLAUSIBLE_UNVERIFIED** |
| 5 | ETF Global | via **Massive** REST `/etf-global/v1/fund-flows` | `nav`, `shares_outstanding`, `fund_flow` | **YES** (E-A) | **2017-04-03** (E-A) | n/v | n/v | **`processed_date` = "when ETF Global received and processed the data"** (E-A) | **FAIL** (predates history) | n/v | YES | $99/mo | **PLAUSIBLE_UNVERIFIED** ← nearest to VERIFIED_PARTIAL |
| 6 | ETF Global | via Nasdaq Data Link `ETFG/FUND`, `ETFG/FUNDN` | shares out., NAV, flow; FIGI/CUSIP/ISIN/SEDOL | YES | **2017-04-03** | n/v | n/v | n/v at this layer | **FAIL** | n/v | YES | PAID | **PLAUSIBLE_UNVERIFIED** |
| 7 | ETF Global | via WRDS (`Analytics`,`Fund Flow`,`Constituents`,`Industry`) | AUM among Analytics fields | **listed "Monthly"** | Analytics 2012-02-27; Fund Flow **1993-01-25** | n/v | n/v — 1993 start implies backfill | n/v | UNKNOWN | n/v | **AUTH** | ACADEMIC | **PLAUSIBLE_UNVERIFIED** |
| 8 | Bloomberg | Global ETP Flows Data Solution (ann. 2025-12-11) | flows from "changes in NAV and shares outstanding" | YES (implied) | **2007** ("flows **and revisions**") | likely | **"revisions"** — semantics undefined | **n/v** — revision record vs. availability stamp undistinguished | UNKNOWN | n/v | YES | PAID | **PLAUSIBLE_UNVERIFIED** |
| 9 | Bloomberg | Company Financials/Estimates/Pricing **Point-in-Time** (COFI) | company actuals | YES | 17 yrs | **NO — 85k companies, no funds** | YES (daily snapshots) | YES, but wrong universe | FAIL | n/a | YES | PAID | **REJECTED** (R1 — wrong universe) |
| 10 | FactSet | ETF Profile & Prices API / ETF Standard DataFeed | `price`/`timeSeries` = historical **NAV**; `fundFlows` = period aggregates | NAV yes; **fund size no** | n/v | n/v | n/v | **n/v** | UNKNOWN | n/v | YES | PAID | **PLAUSIBLE_UNVERIFIED** (weak) |
| 11 | FactSet | Fundamentals **Point-in-Time** | company fundamentals | YES | Feb 1999 | **NO — companies** | YES | YES, but wrong universe | FAIL | n/a | YES | PAID | **REJECTED** (R1 — wrong universe) |
| 12 | LSEG / Lipper | **Fund Flows** | "estimated net flows, gross in/outflows **and assets under management at fund and share class level**" | **YES** (E-A: "Data Frequency: Daily") | **US funds from 1992** (E-A) | likely — covers ETFs, CUSIP/ISIN/SEDOL | **n/v** | **n/v** | UNKNOWN | n/v | YES | PAID | **PLAUSIBLE_UNVERIFIED** ← best coverage |
| 13 | LSEG / Lipper | ETF Daily Holdings | holdings, not fund size | — | ETF portfolios daily only 3 months back | — | — | — | FAIL | — | YES | PAID | **REJECTED** (R1) |
| 14 | CRSP | Survivor-Bias-Free US Mutual Fund DB | `monthly_tna.mtna` | **NO — monthly** | 1961 | n/v (ETF coverage unverified) | n/a | NO | FAIL | **YES** (best in class) | YES | ACADEMIC | **REJECTED** (R2) |
| 15 | CRSP | US Stock daily file | `SHROUT` (thousands) | **NO** — observations from periodic reports + imputed | 1925 | yes as securities | no — split-adjustment factors | NO | FAIL | YES | YES | ACADEMIC | **REJECTED** (R1, R2, R4) |
| 16 | **Ultumus / SIX** | ETF Managed Data | daily NAV, shares outstanding, flows | **YES** | **rolling 5-year lookback** → ~2021-09 | likely | **YES — "complete version control", source-file traceability** | **YES — "absolute point-in-time accuracy"** (E-A/E-B) | **FAIL** (2016 outside window) | n/v | YES | PAID | **REJECTED** (R3) — *best PIT mechanism found, wrong era* |
| 17 | NYSE (ICE) | Arca EOD ETF Report | sample header inspected: Trade Date, Symbol, CUSIP, ISIN, Issue Name, Primary Exchange, Currency, volumes, OHLC, 4PM bid/offer | YES | archive ≥2019 | **NO — 3 of 5** (P-listed only) | n/a | n/a | **FAIL** | n/a | YES | PAID | **REJECTED** (R1 — **no fund-size field at all**; R3) |
| 18 | Nasdaq | Fund Network (NFN / MFQS) | spec defines Total Net Assets / Total Shares Outstanding (Cat F Type J) | daily dissemination | **that message marked "As of TBD 2027"** | ETF coverage unconfirmed | n/v | n/v | UNKNOWN | n/v | enquiry | n/v | **PLAUSIBLE_UNVERIFIED** (carried from B-7) |
| 19 | Internet Archive | over ProShares per-fund CSVs | AUM column in captured vintages | **NO** | — | **NO** — 2014-2019 captures: QLD 0, QID 0, PSQ 0, TQQQ 2, SQQQ 0 | YES (true vintage) | YES (capture timestamp) | **FAIL** | n/a | YES | FREE | **REJECTED** (R2, R3) |
| 20 | Internet Archive | over etfdb.com / etf.com fund pages | `AUM: $1,328.1 M` — no as-of, 0.1M rounding | **NO** — 20–129 captures/ticker over 2010-2021 (~2–4% of trading days) | 2010 | partial | third party's own value | capture timestamp only | **FAIL** — no capture 2016-03-31→04-05 | n/a | YES | FREE | **REJECTED** (R1, R2) |

*(Rows 5/6 and 9/11 are listed separately because the product, not the vendor, is what
is being classified — the acceptance standard forbids crediting a vendor for a property
that lives in a different product of theirs.)*

---

## 2. DECISIVE_EVIDENCE and MISSING_FACTS, per candidate

### 1 · ProShares free published file — REJECTED
**Decisive:** `R2_G3_HISTORICAL_PIT_AMENDMENT` §4 and `R2_G3_PUBLICATION_TIMELINE`. The
file is complete today but "carries no record of when each row was added"; the AUM
column is absent from the 2011/2012 vintages; the 2016-04-01 row was back-filled ≥2.5
days late and nothing in today's file shows that.
**Missing:** nothing — this is settled. It remains R2's best **value** source and is not
an **availability** source.

### 2 · ProShares issuer archive / batch logs — PLAUSIBLE_UNVERIFIED
**Decisive:** none. No public statement of any vintage archive or batch log retention.
ProShares' own FAQ documents the *calculation* time ("usually 4:00 p.m. ET") and says
nothing about posting time. A CUSIP redistribution restriction took effect 2015-08-01.
**Missing:** whether ProShares retains nightly batch output or logs for 2010-2021.
**Why it matters:** ProShares is the **only party that can answer the 2016 acid test
definitively**, because the stall was theirs.

### 3 · Morningstar Direct — PLAUSIBLE_UNVERIFIED
**Decisive:** Morningstar Direct release notes: *"New data points 'Net Assets - Share
Class (Daily)' and 'Fund Size (Surveyed-Daily)' under 'Historical Cash Flow Data'"* —
daily fund size exists (R1, R2 met at E-A). Tuzun (FEDS 2013-48) used Morningstar Direct
TNA/NAV/shares for LETFs from 2006-06-19 (E-C, R3 suggestive).
**Missing:** history depth **of the daily variant**; five-fund coverage; whether values
are restated; **any availability timestamp**. The `Net Assets Date` data point is a
VALUE date, which the standard explicitly rules insufficient.

### 4–7 · ETF Global (four access routes) — PLAUSIBLE_UNVERIFIED
**Decisive (route 5, E-A, the strongest single finding in SV-1):** Massive's ETF Global
Fund Flows API defines **two** date fields on every record —
- `effective_date`: *"The date showing when the information was accurate or valid; some
  issuers, such as Vanguard, release their data on a delay, so the effective_date can be
  several weeks earlier than the processed_date."*
- `processed_date`: *"The date showing when ETF Global received and processed the data."*

That is exactly the VALUE-DATE / AVAILABILITY-DATE pair R4 demands, it is stored per
record, and **both are queryable filter parameters** — so the archive is indexed on
availability, not only on value date. Fields `nav` and `shares_outstanding` give fund
size by R1(b). *"Records date back to April 3, 2017."*

**Missing, and each is decisive:**
1. Does a **historical** row preserve its **original** `processed_date`, or is the row
   replaced (and the stamp refreshed) when a value is corrected? Documentation is silent.
2. `processed_date` is a **date, not a timestamp**. R2 needs "before `tau` on `t`", and
   `tau > 09:30 ET`. `processed_date <= t-1` would prove availability before `t`'s open;
   `processed_date = t` cannot be resolved against `tau` without a time. Nasdaq Data
   Link states the feed updates "Tuesday to Saturday following all trading days with a
   reporting lag of 1 day", which points at `processed_date = t` for a `t-1` value —
   i.e. **the common case is exactly the unresolvable one**.
3. Is `shares_outstanding` **unadjusted**? TQQQ and SQQQ both carry split history;
   `R2_MINIMUM_DATA_CONTRACT` §4 requires `A` to be split-invariant.
4. Five-fund coverage — not verifiable without an account (`AUTH`; SV-1 forbids one).
5. **The pre-2017 question.** ETF Global was founded in 2011. WRDS lists its Fund Flow
   coverage starting **1993-01-25** — SPY's inception, two decades before the firm
   existed. Any pre-2017 row is therefore **reconstructed**, and a reconstructed row
   cannot carry an authentic availability stamp. The academic 2012-2020 daily AUM use
   (Mathis & Moerke) proves the *values* exist; under the standard's E-C rule it proves
   nothing about R4.
6. WRDS labels all four ETF Global tables "Monthly" while the Fund Flow date range is
   day-granular and the Industry table starts 1969-12-31 (a null-date artifact) — so the
   label may be update cadence, not observation frequency. Unresolvable without `AUTH`.

### 8 · Bloomberg Global ETP Flows — PLAUSIBLE_UNVERIFIED
**Decisive:** *"History includes a comprehensive overview of historical flows **and
revisions** dating back to 2007, enabling clients to adjust analyses… reconstruct market
conditions, and backtest models."* Flows are derived by *"monitoring changes in NAV and
shares outstanding"*. Delivered via Terminal, Data License, SFTP/REST/cloud.
**Missing:** what a "revision" record actually contains. A revision **chain** (value v1
superseded by v2) is not the same as an **availability stamp** (v1 first obtainable at
time T). Nothing states which this is. And the product was announced **2025-12-11** with
history reaching 2007 — so unless Bloomberg retained its own contemporaneous archive, the
2007-2017 portion is a 2025 reconstruction, with the same defect as ETF Global's pre-2017.
**Note the trap the task warned about:** Bloomberg's genuine, documented point-in-time
product (COFI) covers **85,000 companies**, explicitly not funds. Bloomberg's PIT
reputation does not transfer to ETP AUM.

### 10 · FactSet — PLAUSIBLE_UNVERIFIED (weak)
**Decisive:** the public ETF API catalogue offers `price`/`timeSeries` = "historical NAV",
and `fundFlows` = "cash inflow/outflows **for various time periods**" — period aggregates,
not a daily fund-size series. No shares-outstanding time series, no AUM series, no
availability field. FactSet Fundamentals PIT covers companies from February 1999.
**Missing:** everything about the institutional ETF Standard DataFeed, whose page does
not render substantive content publicly.

### 12 · LSEG Lipper Fund Flows — PLAUSIBLE_UNVERIFIED (best coverage)
**Decisive (E-A, product page):** `Data Frequency: Daily`; *"We provide estimated net
flows, gross inflows, gross outflows and **assets under management at fund and share
class level**"*; *"money moving into and out of mutual funds **and ETFs**"*; *"daily flow
history available from August 1, 2012 for non-US funds and **from 1992 for US funds**"*;
standardised on Lipper IDs plus ISIN, SEDOL, CUSIP (R8).
This **supersedes the SV-1 brief's lead** that LSEG coverage "may start much later than
R2's sample" — that was true of *ETF Daily Holdings*, a different product. On coverage,
Lipper is the only candidate that spans the entire 2010-06-06 → 2021-12-31 window.
**Missing:** every R4/R5 property. Not one word about vintages, revisions, restatement or
receipt timestamps. Also unverified: that the daily AUM series (not just daily *flows*)
extends to 1992 for these five funds.

### 14/15 · CRSP — REJECTED
**Decisive:** MF database `monthly_tna.mtna` is month-end (already in
`R2_DATA_SOURCE_AUDIT` C-3). The US Stock file's shares outstanding is *"taken directly
from an annual or quarterly report… supplemented with imputed shares observations derived
from distributions affecting shares outstanding using Factor to Adjust Shares"* — a
reported-and-imputed observation series, structurally unable to track daily
creation/redemption, and carrying adjustment factors that break split-invariance.

### 16 · Ultumus / SIX — REJECTED on era, and the most informative rejection in SV-1
**Decisive (verbatim, ultumus.com):** *"Achieve absolute point-in-time accuracy with
complete version control and a comprehensive **5-year historical lookback** where every
data point is fully traceable back to its source file."* Plus *"full version control and
historical tracking of all ETF provider file re-issues"*, *"direct download links to raw
ETF issuer files"*, and *"Tracks historical flow data, including net asset values, shares
outstanding"*.
**Why it is rejected:** a **rolling** 5-year window reaches ~2021-09-19 today. Overlap
with R2's Development window is ~73 trading days at the very end, and it shrinks to zero
during 2026. Ultumus itself was founded ~2017 and acquired by SIX in 2021, so a deeper
archive cannot exist.
**What it establishes:** PIT-grade ETF fund-size data, with issuer source files retained
and re-issues versioned, is a **real, purchasable product class** — retained for about
five years. That is the single most decision-relevant fact SV-1 found, and it cuts both
ways: it is why 2010-2021 is hard, and it is why forward collection has value.

### 17 · NYSE Arca EOD ETF Report — REJECTED, and a caution
**Decisive:** the free public sample file's header, inspected directly:
`Trade Date|Symbol|CUSIP|ETP ISIN|Issue Name|Primary Excahnge|Currency|TOTAL Volume|NYSE
Arca volume|NYSE Volume|Consolidated High/Low/Close Price|NYSE ARCA High/Low/Close
Price|Consolidated 4PM Bid|Consolidated 4PM Offer|Consolidated Bid Ask Midpoint|NYSE Arca
4PM Bid|NYSE Arca 4PM Offer|NYSE Arca 4PM Bid Ask Midpoint`
— **no shares outstanding, no NAV, no net assets.** Secondary prose describing this
product as carrying "shares outstanding… and the Net Asset Value" is wrong. Inspecting
the schema rather than the description is precisely what the standard requires.
**Second, independent defeat — the universe straddles two listing venues.** From the
official Nasdaq symbol directory (`nasdaqtraded.txt`): `PSQ|…|P`, `QID|…|P`, `QLD|…|P`,
`SQQQ|…|Q`, `TQQQ|…|Q`. QLD/QID/PSQ are **NYSE Arca (P)**; TQQQ/SQQQ are **Nasdaq (Q)**.
No single listing-venue reference product can ever cover more than 3 of the 5 funds, and
OD-6 forbids a partial-universe `K_t`. This defeats the whole exchange-archive class as a
standalone route, not just this product.

### 19/20 · Internet Archive routes — REJECTED
**Decisive, re-tested 2026-09-19 (the archive is back up; `R2_DATA_SOURCE_AUDIT` A-6
recorded it offline earlier the same day):**
- ProShares per-fund CSVs, 2014-2019, status-200 captures: QLD **0**, QID **0**, PSQ
  **0**, TQQQ **2** (one 302 on 2016-03-10, one 200 on 2018-09-29), SQQQ **0**.
- Aggregator pages, 2010-2021 status-200 captures: etfdb QLD 70 / QID 129 / PSQ 64 /
  TQQQ 91 / SQQQ 90; etf.com QLD 33 / QID 20 / PSQ 20 / TQQQ 61 / SQQQ 37. Against ~2,900
  trading days that is 2-4% density. The captured page carries `AUM: $1,328.1 M` with
  **no as-of date** and 0.1M rounding.
- TQQQ's 2016 etfdb captures are 03-18, 04-16, 04-21, 10-18, 12-11 — **none inside
  2016-03-31 → 2016-04-05.**

A capture timestamp is a genuine R4-C availability proof. At this density it cannot
produce a daily eligibility table. Retained as an **audit** instrument, not a source.

---

## 3. What the matrix shows structurally

1. **Every vendor with a documented point-in-time product scopes it to company
   fundamentals** (Bloomberg COFI: 85k companies; FactSet Fundamentals PIT: companies
   since 1999). The industry built PIT to handle accounting restatement. Fund AUM was
   never the target.
2. **The one vendor class that does keep ETF fund-size vintages keeps them ~5 years**
   (Ultumus/SIX), because the need it serves is operational and regulatory, not historical
   research.
3. **Deep history and availability evidence are inversely distributed.** Lipper reaches
   1992 with no vintage semantics; ETF Global documents an availability field but only
   from 2017-04-03; Ultumus documents true vintages but only ~5 years back.
4. **Vendors younger than the sample must have backfilled it.** ETF Global (founded 2011)
   carrying a 1993 start, and Bloomberg announcing 2007 history in December 2025, are both
   reconstructions unless proven otherwise — and a reconstructed row cannot carry an
   authentic availability stamp.
5. **The R2 universe straddles NYSE Arca and Nasdaq**, which kills any single-venue
   reference-data route given OD-6's ban on a partial-universe `K_t`.


---

# AMENDMENT — 2026-09-20 (acceptance corrections)

The matrix body above is unchanged. Two labelling corrections apply to how it is read;
full text at `R2_SV1_SOURCE_VERIFICATION_REPORT.md` AMENDMENT 2026-09-20.

1. **Row 5's marginal note "nearest to VERIFIED_PARTIAL" and the report's `BEST_SOURCE`
   label are withdrawn as rankings.** ETF Global is the
   `STRONGEST_PUBLICLY_DOCUMENTED_PIT_METADATA_CANDIDATE` — the only candidate whose
   *public documentation* defines a stored availability field. Bloomberg, LSEG Lipper,
   Morningstar and FactSet remain `PLAUSIBLE_UNVERIFIED` and **unasked**; any may prove
   superior. Best-documented is not known-best.

2. **Row 2's framing of ProShares as uniquely decisive is corrected.** A vendor holding
   genuine historical receipt / load logs can definitively establish when **its users**
   received a value. ProShares can establish **issuer-side publication / batch** facts.
   Those are distinct questions and both are worth asking; neither party subsumes the other.

Classifications themselves are unchanged. `SV1_VERIFIED_SOURCE = NONE`.

---

# Correction of record 2026-10-02 — CP-AUDIT-01 (R2-G14, R2-G20)

```
APPLIES_TO = R2_SV1_SOURCE_MATRIX.md and R2_SV1_SOURCE_VERIFICATION_REPORT.md
AUTHORITY  = delegate decision D-R2-2026-10-02-01 (DECISION_LOG.md)
FINDINGS   = audits/2026-10-01_CP-AUDIT-01/2026-10-01_CP-AUDIT-01_R2.md §3
```

The table and text above are **not edited**; this section governs where they disagree.

1. **Row 18, Nasdaq Fund Network: REJECTED (R3)**, replacing PLAUSIBLE_UNVERIFIED. The only
   documented Total Net Assets message is "As of TBD 2027", so history begins after the
   sample. The NFN specification bytes were never captured. No enquiry (COR-R2-G14).
2. **Candidate count.** The table has **20** numbered candidates, not "Nineteen". The SV-1
   report's §3 list ("Twenty products") has 19 items: it omits row 14 (CRSP
   Survivor-Bias-Free US Mutual Fund Database).
3. **TQQQ Internet Archive captures, 2014-2019: status-200 = 1** (2018-09-29), not 2; the
   other TQQQ entry is a 302 (2016-03-10). The SV-1 report §4 "two for TQQQ" carries the same
   error. The stored bytes hold exactly one target-fund CSV capture
   (`20180929144909_TQQQ`, HTTP 200) and no CDX output.
4. **Attribution of the 2016 302 is UNRESOLVED.** This matrix says TQQQ (2016-03-10);
   `R2_G3_HISTORICAL_PIT_AMENDMENT.md` §6 attributes the 2016 302s to SQQQ. No CDX output is
   stored, and no re-query is made (it needs the network, and nothing depends on it).

No classification other than row 18 changes. Row 19 stays REJECTED (R2, R3) at any count.
