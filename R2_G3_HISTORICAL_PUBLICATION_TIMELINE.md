# R2_G3_HISTORICAL_PUBLICATION_TIMELINE

```
RECORD_TYPE = EVIDENCE_TIMELINE
LINEAGE     = R2
GAP         = G-3 (historical PIT sub-gap, 2010-2019)
CREATED     = 2026-09-19
STAGE       = S0 / DATA FEASIBILITY - PRE-S1
```

Regime boundaries are set **by observed evidence**, not by equal periods. All times
are US Eastern, converted from recorded UTC with the correct EST/EDT offset for each
date. Every row rests on a contemporaneous archived artifact whose origin HTTP
headers the Internet Archive preserved (`x-archive-orig-*`), not on current endpoint
behaviour.

---

## Regime R-1 — 2010-06-06 → 2012-09-25

```
PERIOD                 2010-06-06 -> 2012-09-25  (end = last date with direct evidence)
TARGET_FUNDS_ACTIVE    QLD, QID, PSQ (since 2006); TQQQ, SQQQ (since 2010-02-09) - all five
SOURCE                 accounts.profunds.com/etfdata/ByFund/<TICKER>-historical_nav.csv
                       + www.proshares.com/funds/<ticker>.html
FIELD                  **8-column schema: Date, Name, Ticker, NAV, Prior NAV,
                       NAV Change (%), NAV Change ($), Shares Outstanding (000).
                       NO "Assets Under Management" COLUMN.**
PUBLICATION_TIMING_EVIDENCE
                       Six files (EWV, MVV, SPXU, AGQ, SBM, TLL) captured 2011-07-18
                       20:20-21:23 ET, every one carrying
                       Last-Modified 2011-07-18 19:44:26-27 ET - identical to the
                       second across six unrelated funds, i.e. one batch - and newest
                       row 07/18/2011 (same day).
                       UYM captured 2012-09-18 08:39 ET (Tue, PRE-OPEN): newest row
                       09/17/2012, Last-Modified 2012-09-17 22:57:46 ET.
                       UYM captured 2012-09-25 08:18 ET (Tue, PRE-OPEN): newest row
                       09/24/2012, Last-Modified 2012-09-24 20:51:00 ET.
                       Target-fund page (TQQQ): "Price Information as of 9/27/10"
                       at 2010-09-28 14:59 ET; "as of 4/30/12" at 2012-05-01 07:13 ET
                       (PRE-OPEN) - prior trading day NAV, but NOT net assets.
PROVEN_BOUND           For NAV + shares outstanding: NEXT_TRADING_DAY_OPEN.
                       **For AUM: NONE - the field was not published.**
EVIDENCE_LEVEL         B (contemporaneous timestamped public artifacts)
CONFIDENCE             HIGH for the artifact and its timing; the AUM field's absence
                       is directly observed, not inferred
LOOKAHEAD_RISK         **HIGH for R2's field as planned.** Today's AUM column exists
                       for these dates but was NOT published then. Using it requires
                       the reconstruction bridge below, whose precision exceeds what
                       was publicly computable at the time.
```

**The reconstruction bridge, validated rather than assumed.** Today's AUM column was
compared against contemporaneous 2011-vintage `NAV x Shares Outstanding` for six
funds on four dates (2010-06-01, 2011-01-03, 2011-07-15, 2011-07-18), 24 fund-date
observations:

| fund | relative difference | explanation |
|---|---|---|
| EWV | 0 to 1.5e-16 | exact |
| MVV | 0 to 3.1e-11 | exact to float precision |
| SPXU | 4.9e-08 to 1.4e-07 | today's share count carries sub-thousand precision |
| AGQ | 3.2e-06 to 7.3e-06 | same |
| SBM | 6.7e-06 to 1.0e-05 | same |
| TLL | 0 to **1.65e-02** | 59 thousand shares; integer-thousand rounding bites hard |

So today's AUM column **does** reproduce the quantity that was publicly computable in
2011 — but only to the precision at which shares were then published, and the error
grows as the share count shrinks. The validation used **non-target** funds; no
contemporaneous 2010-2012 capture of QLD, QID, PSQ, TQQQ or SQQQ exists in the
archive.

---

## Regime R-2 — 2012-09-26 → 2014-03-25

```
PERIOD                 2012-09-26 -> 2014-03-25
TARGET_FUNDS_ACTIVE    all five
SOURCE                 same endpoint
FIELD                  UNKNOWN - the 8-column to 9-column schema change happened
                       somewhere inside this window
PUBLICATION_TIMING_EVIDENCE
                       **NONE. Zero captures of anything under /etfdata/ in 2013.**
PROVEN_BOUND           NONE
EVIDENCE_LEVEL         NONE
CONFIDENCE             n/a
LOOKAHEAD_RISK         UNQUANTIFIED - neither the field's presence nor its timing is
                       evidenced anywhere in this ~18-month window
```

A tempting but rejected tightening: the TQQQ fund page described the download as
"historical NAVs, NAV change (%, $), and shares outstanding" on 2014-02-26, which
would have bracketed the schema change to within a month. **A control check killed
it** — the page still carried that same wording on 2014-07-02, four months *after*
the AUM column is directly observed in the file. The link text is stale boilerplate
and brackets nothing.

---

## Regime R-3 — 2014-03-26 → 2019-12-31

```
PERIOD                 2014-03-26 -> 2019-12-31  (start = earliest AUM-bearing capture)
TARGET_FUNDS_ACTIVE    all five
SOURCE                 same endpoint
FIELD                  **9-column schema including "Assets Under Management"**
PUBLICATION_TIMING_EVIDENCE   11 contemporaneous observations (table below)
PROVEN_BOUND           NEXT_TRADING_DAY_OPEN (09:30 ET on t) - TYPICAL, NOT GUARANTEED
EVIDENCE_LEVEL         B
CONFIDENCE             MEDIUM-HIGH, reduced by one documented batch failure
LOOKAHEAD_RISK         LOW on a typical day; NOT ZERO - see the 2016-04-01 failure
```

| row date | fund | cols | origin write (ET) | IA retrieval (ET) | newest row | trading days missing at retrieval |
|---|---|---|---|---|---|---|
| 2014-03-26 | UVXY | 9 | 2014-03-26 18:25:05 Wed | 2014-03-27 13:46:07 Thu | 03/26/2014 | 0 |
| 2014-03-26 | SVXY | 9 | 2014-03-26 18:25:02 Wed | 2014-03-27 13:50:36 Thu | 03/26/2014 | 0 |
| 2016-03-31 | UPRO | 9 | 2016-03-31 18:25:30 Thu | 2016-04-03 20:01:54 Sun | 03/31/2016 | **1 — 2016-04-01** |
| 2016-03-31 | SSO | 9 | 2016-03-31 18:25:30 Thu | 2016-04-04 00:19:39 Mon | 03/31/2016 | **1 — 2016-04-01** |
| 2016-09-12 | SH | 9 | 2016-09-12 18:33:01 Mon | **2016-09-13 01:15:31 Tue (PRE-OPEN)** | 09/12/2016 | 0 |
| 2016-12-05 | TBT | 9 | 2016-12-05 18:56:50 Mon | 2016-12-06 16:18:09 Tue | 12/05/2016 | 0 |
| 2017-05-05 | TBT | 9 | 2017-05-05 18:59:13 Fri | 2017-05-06 02:58:20 Sat | 05/05/2017 | 0 |
| 2017-07-07 | UCO | 9 | 2017-07-07 20:42:46 Fri | 2017-07-09 18:05:58 Sun | 07/07/2017 | 0 |
| 2017-09-15 | BIB | 9 | 2017-09-15 19:31:03 Fri | 2017-09-18 07:40:15 Mon (pre-open) | 09/15/2017 | 0 |
| 2018-07-19 | EUO | 9 | 2018-07-19 18:36:56 Thu | **2018-07-20 01:23:13 Fri (PRE-OPEN)** | 07/19/2018 | 0 |
| **2018-09-28** | **TQQQ** | 9 | **2018-09-28 19:08:47 Fri** | 2018-09-29 10:49:09 Sat | **09/28/2018** | 0 |

Write times cluster **18:25 → 20:43 ET on the row's own date**. Two retrievals are
pre-open on a trading day across a true overnight gap (SH 2016-09-13 01:15 ET;
EUO 2018-07-20 01:23 ET), which is the exact shape of the target claim.

**The failure, stated plainly.** 2016-04-01 was a normal NYSE trading day — today's
files all carry a row for it. Yet at **2016-04-03 20:01 ET** (UPRO) and
**2016-04-04 00:19 ET** (SSO) the published files' newest row was still
**2016-03-31**, with both carrying `Last-Modified 2016-03-31 18:25:30 ET` — identical
to the second, so the whole batch had not run since Thursday evening. Both responses
came straight from `Apache/2.2.3` with no `Cache-Control`, `Expires`, `Age` or `Via`
header, so this is the origin's own state and not a stale intermediary. The 04/01 row
was therefore back-filled at least ~2.5 days late, possibly during a trading day.

---

## Regime R-4 — 2020-01-01 onward

```
PERIOD                 2020-01-01 -> present
STATUS                 ALREADY ACCEPTED BY THE CONTROLLER - not re-audited here.
                       Evidence: R2_G3_PUBLICATION_TIMING_REPORT.md sections 4-7
                       (2020 / 2022 / 2026 evening-batch pattern, endpoint metadata
                       semantics, five-fund synchronisation).
```

---

## Cross-regime summary

| regime | period | AUM field published? | timing evidence | bound for `A_{i,t-1}` |
|---|---|---|---|---|
| R-1 | 2010-06-06 → 2012-09-25 | **NO** | strong, for NAV + shares | **none for AUM** |
| R-2 | 2012-09-26 → 2014-03-25 | unknown | **none** | **none** |
| R-3 | 2014-03-26 → 2019-12-31 | **YES** | 11 observations, 1 failure | next-trading-day open, typical not guaranteed |
| R-4 | 2020-01-01 → | YES | accepted | accepted |

Latest evening write observed anywhere in 2010-2019: **22:57:46 ET (2012-09-17)**.
Latest within R-3: **20:42:46 ET (2017-07-07)**.
