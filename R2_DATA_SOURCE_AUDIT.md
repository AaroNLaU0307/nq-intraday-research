# R2_DATA_SOURCE_AUDIT

```
RECORD_TYPE = DATA_SOURCE_AUDIT
LINEAGE     = R2
CREATED     = 2026-09-18
STAGE       = S0 / DATA FEASIBILITY - PRE-S1
BASIS       = R2_MINIMUM_DATA_CONTRACT.md
```

Audited in the order the task requires: **local first, then public, then paid.** No
purchase was made, none is authorized, and no NQ outcome relationship was computed
anywhere in this audit.

All wall-clock references are ET. The auditing machine is UTC+8; the audit window
corresponds to roughly 15:30-16:30 ET on Thursday 2026-09-17.

---

## PART A - LOCAL DATA AUDIT

Searched: the whole `Quant trade` workspace tree, every project `data/` and
`data_cache/` directory, the KB dataset registry
(`quant-research-knowledge-base/registry/datasets/`), and the out-of-OneDrive data
root `C:\Users\Aaron\quant-data\`.

### A-1  Databento GLBX.MDP3 - NQ 1-minute OHLCV  (the only local NQ data)

```
SOURCE              Databento batch job GLBX-20260727-DL3BEBCHJA
                    C:\Users\Aaron\quant-data\databento-archive\intraday-trend\
                    development_signal\GLBX-20260727-DL3BEBCHJA\
FIELDS              ts_event, open, high, low, close, volume   (ohlcv-1m)
                    query: dataset GLBX.MDP3, symbols ["NQ.v.0"], stype_in continuous
DATE COVERAGE       2010-06-06 -> 2022-01-01 EXCLUSIVE.  139 monthly .dbn.zst files
                    (143 entries incl. manifest/metadata/condition). condition.json
                    marks each date "available".
POINT_IN_TIME SAFE  YES for intraday use. 1-minute bars are timestamped; a trailing
                    volume denominator and a close-to-tau benchmark proxy can both be
                    built strictly from data at or before tau.
IDENTITY SAFE       PARTIAL. `NQ.v.0` is a CONTINUOUS front-month stitch, not a fixed
                    contract. Roll convention is the vendor's. Volume near a roll is
                    split across contracts, so a volume denominator inherits the
                    vendor's roll definition - must be declared at S1, not discovered.
MISSINGNESS         Not re-measured here (files not decoded - see OUTCOME BLINDNESS).
                    Every file's SHA-256 is pinned in manifest.json; manifest hash
                    d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8.
KNOWN LIMITATIONS   1. Ends 2022-01-01. No local NQ data for 2022-2026.
                    2. **R2 HAS NO GRANT OVER THIS ARCHIVE.** The grant is
                       "NQ Development OHLCV ... R1 only" (R1 sealed prereg OD-1).
                       Reading it for R2 is an Owner decision, not an inheritance.
                    3. This is the "NQ Development" sample, which already carries
                       ITSF trial S0-T001 and R1. Using it for R2 is a further trial
                       on a reused sample - a trial-accounting decision, not a
                       technical one.
                    4. It is NQ futures, not the NDX index. Using NQ as the
                       `r_pre` benchmark proxy introduces basis; using it as the
                       liquidity denominator is exactly right.
```

### A-2  Databento GLBX.MDP3 - NQ bbo-1s  (execution-cost calibration)

```
SOURCE              GLBX-20260727-TV3MXWNMXD, same archive root
FIELDS              bbo-1s
DATE COVERAGE       2025-01 -> 2025-03 only (3 monthly files)
POINT_IN_TIME SAFE  n/a for R2
IDENTITY SAFE       n/a
KNOWN LIMITATIONS   Three months, four years after the OHLCV window ends. Irrelevant
                    to R2's fund-side reconstruction. R1's invariant L-10 forbade raw
                    BBO access; R2 has no grant here either.
```

### A-3  Local ETF panels - checked and REJECTED for R2

```
SOURCE              multi-asset-tsmom-research/data/close_prices_raw.csv
                    multi-asset-tsmom-research/data/xsmom_universes_prices.csv
                    (KB: dataset.yfinance.multi-asset-etf-panel)
FIELDS              Date + daily close per ticker. Nothing else.
DATE COVERAGE       ~2008-05 -> 2026-06 daily close
TICKERS             SPY QQQ IWM EFA EEM EWJ TLT IEF SHY LQD HYG USO UNG XLE GLD SLV
                    CPER DBA WEAT CORN UUP FXE FXY VNQ RWX XLF XLK XLV XLU GDX
                    (+ the xsmom country/sector set)
VERDICT             **NO leveraged or inverse ETF is present.** QQQ is unleveraged.
POINT_IN_TIME SAFE  Not assessed - the fields R2 needs are absent.
IDENTITY SAFE       Not assessed - same.
MISSINGNESS         n/a
KNOWN LIMITATIONS   Price only: no AUM, no net assets, no shares outstanding, no NAV,
                    no leverage field, no benchmark field, no launch/closure dates.
                    Survivor-selected by construction (a fixed present-day ticker
                    list). Unusable for R2 at any stage.
```

### A-4  Other local data - checked and irrelevant

| source | why not usable for R2 |
|---|---|
| `trade log/` HistData zips (47 files) | FX, metals, WTI M1 only. No equity index, no ETF. |
| `quant-backtest-framework/data_cache/*.pkl` | EURUSD/GBPJPY/GBPUSD/WTIUSD/XAUUSD M1. |
| `commodity-carry-research/data/` | manifest + README only; the Databento commodity data lives outside OneDrive. |
| `spot-mfi-btc-perp-research/data_cache/` | BTC spot/perp/funding parquet. |
| `orderflow-research-engine/data/` | order-flow parquet/raw for its own instruments. |
| `multi-asset-tsmom-research/data/benb/{HYG,LQD}_nav_daily.csv` | two credit-ETF NAV series; not NDX, not leveraged, no assets field. |
| `qros-runtime/data/` | governance state machine tables, not market data. |

### A-5  Local audit conclusion

```
LOCAL COVERAGE OF THE FUND SIDE OF R2   =  ZERO
LOCAL COVERAGE OF THE FUTURES SIDE      =  PARTIAL (2010-06-06 -> 2022-01-01),
                                           and NOT GRANTED to R2
```

No local source supplies historical AUM, NAV, shares outstanding, fund reference
history, corporate actions, benchmark identity, ETF daily pricing for leveraged
funds, or a leverage-mandate history. The KB dataset registry contains five dataset
entries, none of them an ETF reference or fund-flow dataset.

---

## PART B - PUBLIC DATA AUDIT

The question asked was not *"can I find today's TQQQ AUM"* but *"can the required
point-in-time history be reconstructed without look-ahead"*. Sources are therefore
graded on that, and `CURRENT PAGE AVAILABLE` is reported separately from
`HISTORICAL POINT-IN-TIME DATA AVAILABLE`.

### B-1  ProShares / ProFunds per-fund historical NAV file  - PRIMARY FINDING

```
SOURCE              https://accounts.profunds.com/etfdata/ByFund/<TICKER>-historical_nav.csv
                    linked from each fund page on proshares.com as "NAV History"
FIELDS              Date, ProShares Name, Ticker, NAV, Prior NAV, NAV Change (%),
                    NAV Change ($), Shares Outstanding (000),
                    **Assets Under Management**
FREQUENCY           daily, every trading day, from fund inception
HISTORICAL PIT?     **YES for the Assets Under Management column** (see caveats)
CURRENT PAGE ONLY?  no - this is a full history file, not a snapshot
```

Retrieved 2026-09-17 for the five Nasdaq-100 daily-reset ProShares ETFs:

| ticker | m | m(m-1) | rows | first row | last row | AUM first | AUM last |
|---|---|---|---|---|---|---|---|
| QLD  | +2 | 2  | 5093 | 2006-06-19 | 2026-09-16 | $10.5M | $13.65B |
| QID  | -2 | 6  | 5078 | 2006-07-11 | 2026-09-16 | $10.5M | $0.25B |
| PSQ  | -1 | 2  | 5093 | 2006-06-19 | 2026-09-16 | $52.5M | $0.82B |
| TQQQ | +3 | 6  | 4176 | 2010-02-09 | 2026-09-16 | $8.0M  | $34.58B |
| SQQQ | -3 | 12 | 4176 | 2010-02-09 | 2026-09-16 | $8.0M  | $2.15B |

```
DATE COVERAGE       inception to present, per fund, no truncation
MISSINGNESS         ZERO missing NAV, ZERO missing Shares Outstanding, ZERO missing
                    AUM across all 5 files (20,616 rows). No duplicate dates.
                    Weekday gaps: 190 (QLD/PSQ), 189 (QID), 156 (TQQQ/SQQQ) - i.e.
                    ~9.4 per year, consistent with NYSE holidays, so no trading day
                    is absent.
POINT_IN_TIME SAFETY
                    The AUM column is the point-in-time-usable field. Evidence, and
                    the two caveats:
                    (a) OBSERVED PUBLICATION LAG. At 15:58 ET on Thu 2026-09-17 the
                        most recent row in every file was Wed 2026-09-16. Day t's own
                        row was NOT yet present. So there is no same-day
                        contamination from this feed, and A_{t-1} is present by
                        15:58 ET on t.
                        LIMIT OF THIS EVIDENCE: one snapshot bounds publication of
                        the t-1 row at <= 15:58 ET on t. It does NOT prove
                        publication before 15:30 ET. **Closing this is an S1
                        prerequisite** and costs nothing: poll the URL with
                        timestamps over ~10 business days.
                    (b) VINTAGE / RESTATEMENT. The file is a current-vintage
                        rendering, not an archived vintage. A restatement of a past
                        AUM figure would be invisible. Residual, low, and boundable
                        by snapshotting the file forward from now.
IDENTITY SAFETY
                    **The NAV and Shares Outstanding columns are RETROACTIVELY
                    SPLIT-ADJUSTED and are NOT point-in-time per-share values.**
                    Measured directly: TQQQ's inception row shows NAV $0.2083 and
                    38,400,380 shares, against an actual inception NAV near $25.
                    For the inverse funds, which have had many reverse splits, the
                    adjustment is severe enough to corrupt the share column: SQQQ's
                    2010-09-02 row shows NAV $9,212,800 per share and "Shares
                    Outstanding (000)" = 10, and 140 SQQQ rows round to ZERO shares.
                    CONSEQUENCE, measured: reconstructing AUM as NAV x shares
                    disagrees with the published AUM on 2971/4176 SQQQ rows
                    (max relative error 1.00) and 4065/5078 QID rows (max 0.040),
                    while agreeing to 1e-7 on TQQQ, QLD and PSQ.
                    **RULE FOR R2: use the published AUM column directly. Never
                    reconstruct it from NAV x shares. The AUM product is
                    split-invariant; the two factors are not.**
SURVIVORSHIP        **The endpoint serves CLOSED funds.** Verified: OILU and OILD
                    (ProShares UltraPro 3x Crude Oil, liquidated 2020) each return
                    761 rows ending at their 2017-03-24 inception; DDG returns 3510
                    rows from 2008-06-09. So a survivorship-free ProShares panel is
                    obtainable - CONDITIONAL on knowing the ticker, because the
                    endpoint does not enumerate funds. The universe must come from
                    B-2.
KNOWN LIMITATIONS   1. ProShares ETFs only. ProFunds MUTUAL funds 404 (UOPIX, USPIX,
                       SOPIX all tested).
                    2. No leverage field, no benchmark field, no launch/closure flag,
                       no mandate history - only name, NAV, shares, AUM.
                       Mandate must come from B-3.
                    3. Not enumerable; no documented stability guarantee; no terms
                       page reviewed. Treat the URL pattern as undocumented and
                       liable to change. Snapshot, hash, and store.
COST / LICENCE      Free, no authentication. Licence terms NOT reviewed in this
                    audit - flagged as an Owner item before any durable local copy
                    is relied upon beyond a feasibility probe.
```

### B-2  SEC Investment Company Series and Class Information  - the universe source

```
SOURCE              https://www.sec.gov/files/investment/data/other/
                    investment-company-series-{and-,}class-information/...csv
FIELDS              Reporting File Number, CIK Number, Entity Name, Entity Org Type,
                    Series ID, Series Name, Class ID, Class Name, Class Ticker,
                    address fields
FREQUENCY           ANNUAL snapshot (one file per year)
DATE COVERAGE       downloaded and parsed: 2010, 2011, 2012, 2013, 2014, 2015, 2017,
                    2018, 2019, 2020, 2021, 2022, 2023, 2025, 2026  (15 files)
                    **GAPS: 2016 and 2024 returned 404 under both published naming
                    conventions tried.** Recorded as a coverage gap to close at S1
                    (a different filename, or the EDGAR series browse, will cover it).
HISTORICAL PIT?     YES at annual resolution: each year's file lists the series that
                    had IDs at that reporting date, so a series appearing in 2011 and
                    absent from 2017 bounds its lifetime to within a year.
IDENTITY SAFETY     STRONG. `Series ID` (S+9 digits) is the stable SEC identifier the
                    contract section 1 asks for, and it survives ticker changes.
MISSINGNESS         Material and measured: the **Class Ticker field is empty in the
                    2010-2015 files** for funds that were demonstrably trading
                    (QLD, TQQQ, PSQ, QID, SQQQ all appear with a blank ticker in
                    2010/2011 and with tickers from 2019). So a blank ticker is NOT
                    evidence that a fund never launched, and ticker-based joins must
                    be built from the later files plus EDGAR, not from these alone.
                    Column layout also differs across vintages (the 2014 parse
                    returned a blank Entity Name), so each file needs its own header
                    handling.
SURVIVORSHIP        By design the file includes series that have ceased operation but
                    are not yet reclassified, AND series that have IDs but never sold
                    shares. It is therefore over-inclusive, not survivor-selected -
                    the right direction of error for R2, but it means **existence in
                    this file does not establish operation.**
COST / LICENCE      Free, public domain.
```

**What the parse produced.** Filtering all 15 files for series whose name contains
Nasdaq-100 / QQQ *and* a leverage/inverse word yielded 124 distinct
(entity, series, ticker) rows. The result is carried into
`R2_FEASIBILITY_REPORT.md` section 3. The two findings that matter for feasibility:

1. The **US-listed NDX daily-reset ETF** set over 2006-2022 appears to be exactly the
   five ProShares funds in B-1. Direxion Shares ETF Trust's *Nasdaq-100 Bull 3X
   Shares* and *Nasdaq-100 Bear 3X Shares* appear in the 2010 and 2011 series files
   but vanish thereafter; Rydex ETF Trust's *Rydex 2x NASDAQ 100 ETF*, *Rydex Inverse
   2x NASDAQ 100 ETF* and *Rydex Inverse NASDAQ 100 ETF* likewise appear only in
   2010-2011; ProShares' own *Ultra / Short / UltraShort NASDAQ-100 Equal Weighted*
   appear only in 2010-2011.
2. A substantial **daily-reset NDX MUTUAL FUND** family exists throughout and is a
   real part of the mechanism: ProFunds UltraNASDAQ-100 (UOPIX/UOPSX, +2x),
   UltraShort NASDAQ-100 (USPIX/USPSX, -2x), Short NASDAQ-100 (SOPIX/SOPSX, -1x),
   plus the PROFUND VP annuity clones; and Rydex NASDAQ-100 2x Strategy
   (RYVYX/RYVLX/RYCCX), Inverse NASDAQ-100 2x Strategy (RYVNX/RYVTX/RYCDX), Inverse
   NASDAQ-100 Strategy (RYAIX/RYAPX/RYACX/RYALX), plus Rydex Variable Trust clones.

### B-3  SEC EDGAR filings and full-text search  - mandate, launch, closure

```
SOURCE              https://efts.sec.gov/LATEST/search-index?q=...   (full text, 2001+)
                    https://www.sec.gov/Archives/edgar/...            (filing bytes)
FIELDS              prospectus / post-effective-amendment text (485APOS, 485BPOS,
                    497), annual and semi-annual reports (N-CSR), series inventories
                    (NSAR-A/B, N-CEN), N-PORT
FREQUENCY           event-driven, each filing carries its own filing date
HISTORICAL PIT?     **YES, and this is the strongest point-in-time property in the
                    whole audit.** A prospectus states the leverage multiple and
                    benchmark, and its filing date proves when that statement was
                    public. That is exactly what contract section 2 requires.
IDENTITY SAFETY     STRONG - CIK + Series ID + file number.
MISSINGNESS         Full-text search covers 2001 onward, so a 1990s-era fund would
                    need the filing index rather than FTS. Not binding for R2.
COST / LICENCE      Free, public domain. Requires a declared User-Agent.
KNOWN LIMITATIONS   Manual / semi-automated extraction. The multiple and benchmark
                    live in prose, not a field, so a mandate-history table has to be
                    read out of documents and is labour, not a query.
SURVIVORSHIP TEST RUN
                    Full-text search for the candidate never-launched funds:
                      "Nasdaq-100 Bull 3X Shares"  -> 4 hits: N-1A (2008-04-30),
                        NSAR-A (2011-06-29), NSAR-B (2011-12-23), N-PX (2009-08-27).
                        All Direxion Shares ETF Trust. **No 497, no 485BPOS naming it
                        as offered, no N-CSR.**
                      "Nasdaq-100 Bear 3X Shares" -> the same 4 hits.
                      "Ultra NASDAQ-100 Equal Weighted" / "UltraShort NASDAQ-100
                        Equal Weighted" -> 3 hits each: ProShares 485APOS (2007-07-10)
                        and two ProShare Advisors 40-APP exemptive applications.
                        **No prospectus, no N-CSR.**
                      "Rydex 2x NASDAQ 100 ETF" -> 8 hits, all RYDEX ETF TRUST,
                        485BPOS in 2008/2009/2010 and 485APOS 2010. So it sat inside
                        an EFFECTIVE registration, which is a stronger position than
                        the Direxion pair. **Still no N-CSR hit.**
                    READING: registered-but-never-launched is the natural explanation
                    for all of these, since an operating fund files annual reports.
                    ABSENCE OF FILINGS IS SUGGESTIVE, NOT CONCLUSIVE. The decisive
                    check is the trust's N-CSR / NSAR total-net-assets schedule or a
                    "had not commenced operations" note. **Recorded as an open S1
                    prerequisite, cheap to close, and note that a never-launched fund
                    enters K_t with A = 0, so the downside of the residual is bounded.**
                    The Direxion NSAR-B FY2011 series attachment was retrieved and
                    inspected: its per-series column is "Is this the last filing for
                    this series?" and therefore does NOT report launch status. It
                    does confirm the two NDX 3X series were registered series of the
                    trust (numbers 94 and 95 of 134) as of 2011-10-31.
```

### B-4  SEC Form N-PORT  - assessed, insufficient alone

```
SOURCE              https://www.sec.gov/data-research/sec-markets-data/
                    form-n-port-data-sets
FIELDS              fund-level total assets, liabilities, NET ASSETS; position-level
                    holdings
FREQUENCY           reported MONTHLY (month-end), FILED quarterly
DATE COVERAGE       structured XML data sets from 2019-10 onward. Large entities
                    (>= $1bn) from the 2019-03 reporting period; full industry
                    coverage from 2020-03.
HISTORICAL PIT?     NO for R2's purpose, on two counts: (a) MONTHLY granularity
                    cannot support a DAILY reset footprint - A_{i,t-1} would have to
                    be interpolated across a month during which assets move with a
                    leveraged benchmark; (b) filing lags the reporting period, so the
                    figure was not public at t-1.
IDENTITY SAFETY     STRONG (CIK + Series ID).
MISSINGNESS         Starts 2019-10. Covers at most the last ~2 years of the local NQ
                    window.
COST / LICENCE      Free.
VERDICT             Not a primary source for A_{i,t-1}. **Genuinely useful as an
                    independent cross-check** on the B-1 AUM series for 2019-2022,
                    and as a free way to bound the mutual-fund sleeve (B-6).
```

### B-5  Issuer pages that are CURRENT-ONLY  - explicitly not historical evidence

```
proshares.com fund pages       current NAV, current net assets, 30-day volume,
                               leverage objective, benchmark, inception date.
                               TQQQ verified: leverage "3x", benchmark
                               "Nasdaq-100 Index (NDX)", inception 2010-02-09.
                               USE: mandate/benchmark/inception reference. The
                               HISTORY comes from B-1, not from this page.
direxion.com fund pages        CURRENT snapshot only. Verified by opening the
                               TECL/TECS product page in a browser: it shows current
                               NAV, 1-day NAV change, "Daily NAV", and a Documents &
                               Downloads block - **no downloadable historical NAV,
                               net assets or shares-outstanding series**, and no
                               equivalent of the ProShares NAV-History CSV.
                               The page also carries reverse-split announcements in an
                               "Operational Updates" panel, which is a usable free
                               corporate-action source.
                               NOTE: direxion.com returns HTTP 403 to non-browser
                               clients, so any collection needs a browser path.
Yahoo / Investing / etfdb /    current net assets and price history only. No
ycharts / firstratedata        historical AUM or shares-outstanding series.
                               Price history is irrelevant to R2's fund side.
```

**This block is the reason the audit separates the two questions.** Every one of
these pages can tell you today's TQQQ AUM. None of them is historical point-in-time
evidence, and none may be cited as such.

### B-6  Free routes to the daily-reset MUTUAL FUND sleeve  - partial only

The ProFunds and Rydex daily-reset NDX mutual funds (B-2 finding 2) are part of the
mechanism and have **no free daily assets series**:

- `accounts.profunds.com/etfdata/ByFund/` 404s for UOPIX, USPIX and SOPIX - the
  endpoint is ETF-only.
- Mutual funds publish a daily NAV but not a daily net-assets figure.
- Free asset figures are therefore: **N-CSR / N-CSRS financial statements
  (semi-annual)**, **N-CEN (annual, 2018+)**, **NSAR-B (annual, pre-2018)**, and
  **N-PORT (monthly, 2019-10+)**.

```
BEST FREE FREQUENCY FOR THE MUTUAL FUND SLEEVE  =  MONTHLY from 2019-10,
                                                   SEMI-ANNUAL before that
```

That is enough to **bound** the sleeve's share of `K_t`. It is not enough to include
it as a daily primary input. Carried to the feasibility report as material gap G-1.

### B-7  Nasdaq Fund Network (NFN / MFQS)  - candidate, UNVERIFIED for history

```
SOURCE              nasdaqtrader.com NFN Data Service specification (retrieved and
                    parsed); nfn.nasdaq.com; data.nasdaq.com/databases/NFN
FIELDS CONFIRMED    the spec defines both **Total Net Assets** and **Total Shares
                    Outstanding** as disseminated fields (Category F Type J),
                    alongside NAV.
FREQUENCY           daily dissemination
HISTORICAL PIT?     **UNVERIFIED.** The specification describes a real-time
                    collection-and-dissemination service, not a historical archive
                    product. Whether a purchasable daily history exists, and from
                    when, was not established.
COVERAGE RISK       the spec's fund-type language centres on mutual funds, annuities,
                    UITs, CITs and structured products; ETF coverage of the
                    net-assets / shares fields was NOT confirmed.
MISSINGNESS RISK    the spec states Total Shares Outstanding behaves differently when
                    no amount is entered - i.e. it is an OPTIONAL field, so
                    issuer-level missingness is possible.
VERDICT             CANDIDATE_UNVERIFIED. Do not plan on it. If Aaron wants it
                    closed, it is one vendor enquiry.
```

---

## PART C - PAID DATA OPTIONS

Listed only where a field claim is backed by vendor documentation or by a published
paper's own data section. **Nothing here is a recommendation to buy, and no purchase
is authorized.**

### C-1  ETF Global (via Nasdaq Data Link / direct)

```
VENDOR                  ETF Global
REQUIRED PRODUCT        ETF reference + fund-level analytics (the Nasdaq Data Link
                        ETFC "Constituents" database is the holdings product; the
                        fund-level AUM/leverage/benchmark fields sit in the broader
                        ETFG reference feed)
FIELDS EXPECTED         leverage amount; benchmark index referenced by the fund;
                        **assets under management at DAILY frequency**
EVIDENCE                Mathis & Moerke, *Liquidity Provision to Leveraged ETFs and
                        Equity Options Rebalancing Flows*, data section: "We obtain
                        information on all leveraged ETFs on U.S. equity indexes from
                        ETFGlobal including the leverage amount, the benchmark index
                        referenced by the fund and the assets under management of each
                        leveraged ETF at the daily frequency." Their sample runs
                        2012-2020 and averages 72 leveraged ETFs across 24 benchmarks.
                        This is the only source in the audit whose DAILY,
                        MULTI-ISSUER, leverage-and-benchmark-tagged AUM is
                        corroborated by a published research data section.
HISTORICAL DEPTH        at least 2012-2020 demonstrated by that paper. Exact start
                        date not verified from vendor documentation.
POINT_IN_TIME CHARACTER "sourced directly from fund sponsors, custodians,
                        distributors and administrators", T+1 update. Vintage/
                        restatement behaviour NOT verified.
ACCESS METHOD           Nasdaq Data Link subscription, or direct ETF Global licence
COST / LICENCE          not publicly listed; the Nasdaq Data Link documentation page
                        did not render field or price detail to this session
CONFIDENCE IT SATISFIES R2   **HIGH for the broad multi-issuer scope**, because it is
                        the one source that carries leverage + benchmark + daily AUM
                        together across issuers. REDUNDANT for the NDX-only scope,
                        which B-1 already covers free.
```

### C-2  Morningstar Direct

```
VENDOR                  Morningstar
REQUIRED PRODUCT        Morningstar Direct
FIELDS EXPECTED         total net assets, net asset value, shares outstanding,
                        category type; plus index return series
EVIDENCE                Tuzun (Federal Reserve Board FEDS 2013-48), data section:
                        "LETF information is obtained from Morningstar Direct, which
                        provides total net assets, net asset value, shares outstanding
                        and category type for ETFs. After I identify an ETF as a LETF,
                        I check its prospectus to identify both its target index and
                        the multiple it promises." Sample 2006-06-19 to 2011-12-31.
HISTORICAL DEPTH        demonstrated back to the first US equity LETF (2006-06-19)
POINT_IN_TIME CHARACTER field frequency for ETF total net assets not verified from
                        vendor documentation; the paper's use is daily, which is
                        suggestive but not proof of a daily field
NOTE                    **Morningstar Direct does NOT supply the leverage mandate.**
                        Tuzun read it from prospectuses - the same route as B-3. So
                        this vendor replaces B-1, not B-3.
ACCESS METHOD           Morningstar Direct licence (institutional seat)
COST / LICENCE          not publicly listed; institutional seat pricing
CONFIDENCE IT SATISFIES R2   MEDIUM-HIGH, with mandate still coming from EDGAR
```

### C-3  CRSP Survivor-Bias-Free US Mutual Fund Database (via WRDS)

```
VENDOR                  CRSP / Morningstar Indexes, distributed via WRDS
REQUIRED PRODUCT        CRSP Survivor-Bias-Free US Mutual Fund Database
FIELDS VERIFIED FROM DOCUMENTATION (CRSP_MFDB_Guide.pdf, retrieved and parsed):
                          daily_nav.dnav      daily NAV, per trading day
                          monthly_nav.mnav    month-end NAV
                          monthly_tna.mtna    MONTHLY total net assets, month-end;
                                              "Begins December 1961, annual data
                                              points through then Monthly"
                          monthly_returns, dividends, fees, holdings
HISTORICAL DEPTH        1962-2008 start depending on the item; >64,000 open-end
                        funds, >31,000 delisted retained
POINT_IN_TIME CHARACTER survivor-bias-free by design, which is exactly contract
                        section 1's hard requirement. BUT: **there is no daily TNA and
                        no daily shares-outstanding table.** Updated quarterly,
                        distributed with a monthly lag.
ACCESS METHOD           WRDS subscription
COST / LICENCE          institutional / academic subscription
CONFIDENCE IT SATISFIES R2   **LOW as a primary source** - monthly TNA cannot drive a
                        daily reset footprint. **HIGH as the survivorship and
                        gap-bounding cross-check**, and it is the best route to the
                        ProFunds/Rydex mutual-fund sleeve (gap G-1). ETF coverage
                        within the MF database was not verified and must be checked
                        before relying on it for the ETF side.
```

### C-4  Bloomberg / FactSet / LSEG-Refinitiv

```
VENDOR                  Bloomberg (Terminal / B-PIPE / Data License),
                        FactSet, LSEG (Refinitiv/Datastream)
FIELDS EXPECTED         daily fund total assets, NAV, shares outstanding, fund
                        reference, corporate actions
EVIDENCE                **NOT VERIFIED IN THIS AUDIT.** No field name, history depth
                        or point-in-time characteristic is claimed for these vendors,
                        because no documentation or schema/catalogue was inspected.
                        They are listed as plausible, not as established.
CONFIDENCE IT SATISFIES R2   UNASSESSED. Per the task's own rule, no field is claimed
                        without documentation, so no confidence is reported.
```

### C-5  Databento GLBX.MDP3 extension  - the only purchase that touches the futures side

```
VENDOR                  Databento (existing relationship; two prior jobs on disk)
REQUIRED PRODUCT        GLBX.MDP3, schema ohlcv-1m, symbol NQ.v.0 (or a defined
                        contract series), 2022-01-01 onward
FIELDS EXPECTED         ts_event, open, high, low, close, volume - identical to A-1,
                        so schema continuity is guaranteed rather than assumed
HISTORICAL DEPTH        continuous from the existing archive's end
POINT_IN_TIME CHARACTER same as A-1
ACCESS METHOD           Databento batch job, same as the two jobs already on disk
COST / LICENCE          Databento terms, licensed, not for redistribution. Cost not
                        quoted here.
CONFIDENCE IT SATISFIES R2   HIGH for what it does, which is **extend** the sample,
                        not enable it. R2 is answerable inside 2010-06-06 ->
                        2022-01-01 without it, subject to the grant and trial
                        questions in A-1.
```

---

## PART D - THE PROBE

`data_probe/proshares_nav_2026-09-17/` holds the five B-1 files as retrieved, with
SHA-256:

```
5f18bb6ceae615ed6968e1a38bf2e303d2ed2aa1e7ef593c0e9625e503a2db09  PSQ-historical_nav.csv
c84f6aa03e3a4cc5de1237e2de16086c6af8e0737c476c940525d1c69ad9bed1  QID-historical_nav.csv
a6ab72d8dd862302a2d7150e1782ddb8cf6b1435bafeb7a07b5cc9870e3fb883  QLD-historical_nav.csv
36772de4a617f59c519c03339a79862ba38c498821d16e0393fd77e3fb8ee156  SQQQ-historical_nav.csv
e31852544fe9b0b99b8fe3aae0e6cf95e0dbe68ba81539c0336a502b0ff67cb8  TQQQ-historical_nav.csv
```

**This is a feasibility probe, not a research dataset.** It is a single
current-vintage snapshot taken 2026-09-17 for the sole purpose of measuring schema,
coverage, missingness and internal consistency. It is not a sealed input, carries no
data grant, and must be re-acquired under whatever provenance discipline S1 defines
before any research use.

---

# AMENDMENT — 2026-09-19 (G-3 closed)

**The accepted body above is unchanged.** This block records what later evidence
changed, and is authoritative where it and the body disagree. Full evidence:
`R2_G3_PUBLICATION_TIMING_REPORT.md`.

## A-1 amendment — B-1 "POINT_IN_TIME SAFETY (a) OBSERVED PUBLICATION LAG"

The body records only that the `t-1` row was present at 15:58 ET on `t`, bounding
publication at `<= 15:58 ET` and no tighter. That bound is now superseded:

```
AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN  (09:30 ET on trading day t)
EVIDENCE_LEVEL   = B
G3_STATUS        = CLOSED_PASS
```

The endpoint returns a meaningful Apache `Last-Modified` **and** a
`FileETag MTime Size` ETag whose size component equals `Content-Length` exactly and
whose decoded mtime equals `Last-Modified` to the second. On 2026-09-19 all five R2
files carried `Last-Modified = 2026-09-18 21:00:56-21:01:12 ET` with newest row
`09/18/2026` — written the same evening as the row they carry. 173 of 238 fund files
were written in that same two-minute batch; 65 have mtimes frozen for years, which is
what proves mtime is a real write and not a nightly touch. Four independent batch
observations spanning 2020, 2022 and 2026 put the evening batch at 19:25, 20:21 and
21:00-21:01 ET on the row's own date.

## A-2 amendment — B-1 "KNOWN LIMITATIONS 3" (undocumented endpoint)

The body says to treat the URL pattern as undocumented. **Partially retired.**
ProShares' own performance-and-pricing FAQ directs users to "the file labeled
'Historical NAVs for all ProShares ETFs' in the ETF Data Downloads section", and that
master file (`/etfdata/historical_nav.csv`, 50 MB) carries the same 21:00 ET batch
write time as the per-fund files. The data product is **first-party documented**. The
residual is now the narrower `G-10`: no guarantee that the URL pattern, the open
Apache directory index, or the header semantics persist — so snapshot, hash and
record headers at collection time.

## A-3 amendment — B-5 "issuer pages that are CURRENT-ONLY"

Add, as verified first-party documentation of the **calculation** time only:
ProShares states NAV "is set when the markets for the ETF's underlying securities
close. This is usually 4:00 p.m. ET". The same page states **nothing** about when
data is posted. The calculation-versus-publication distinction therefore holds, and
no Level A publication rule exists for this quantity.

## A-4 amendment — new source assessed: SEC Rule 6c-11

`17 CFR 270.6c-11(c)(1)` (SEC Release 33-10695, effective 2019-12-23) requires each
business day that an ETF post, free and publicly, its portfolio holdings **before the
opening of regular trading**, and its **NAV per share, market price and premium or
discount, each as of the end of the prior business day**. Assessed and found
**insufficient for R2**: it names NAV per share, not total net assets or shares
outstanding; the "before the opening" deadline attaches to the holdings
subparagraph, not the NAV subparagraph; and it post-dates most of the sample.
Recorded as supporting context, not as a Level A closure.

## A-5 amendment — G-6 vintage / restatement risk, partially tested

Comparing `data_probe/proshares_nav_2026-09-17/` against the 2026-09-19 retrieval:
all **20,616 overlapping rows across the five funds are byte-identical**, and each
file gained exactly the two intervening trading days. Append-only over the interval
tested, zero restatements. The residual risk is reduced, not eliminated — one
two-day interval is not a general guarantee.

## A-6 — Internet Archive unavailable

Wayback CDX queries for the endpoint returned the Internet Archive's "temporarily
offline" page on 2026-09-19. No archival corroboration was obtainable; the route
remains open for later use.
