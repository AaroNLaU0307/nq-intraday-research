# R2_G3_HISTORICAL_PIT_AMENDMENT

```
RECORD_TYPE       = GAP_CLOSURE_AMENDMENT
LINEAGE           = R2
GAP               = G-3, historical point-in-time sub-gap (2010-2019)
CREATED           = 2026-09-19
STAGE             = S0 / DATA FEASIBILITY - PRE-S1

PRIOR_G3_CLOSE    = NOT ACCEPTED BY CONTROLLER
REASON            = 2010-2019 historical PIT availability not established
```

**This amendment does not rewrite `R2_G3_PUBLICATION_TIMING_REPORT.md`, and that
report is not to be read as though it had always been correct.** It stands as the
record of what was found on 2026-09-19 about the *current* endpoint. Its error was
one of scope: it proved a bound from 2020/2022/2026 artifacts and stated it for a
sample beginning 2010-06-06. Projecting modern endpoint behaviour backwards across a
schema change is exactly the look-ahead risk `R2_MINIMUM_DATA_CONTRACT.md` section 6
names as the vintage trap. The controller's HOLD is correct.

Evidence timeline: `R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md`.
Artifacts: `data_probe/g3_historical_pit_2026-09-19/` (44 files, `MANIFEST.sha256`).

---

## 1. What is superseded, and what is not

**Superseded.** The prior report's

```
AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN   (as a FULL-SAMPLE claim)
G3_STATUS        = CLOSED_PASS
```

is withdrawn as a statement about 2010-06-06 → 2022-01-01. It is re-established only
for **2014-03-26 onward**, and there only as a typical rather than guaranteed bound.

**Not reopened**, per the controller's accepted list: the existence of the endpoint;
the 2026 metadata semantics (`Last-Modified` / ETag agreement, ETag size equals
Content-Length, files not blindly touched nightly, append-only behaviour against the
stored probe); the five funds' 2026 synchronisation; the prohibition on same-day `t`
AUM; the 2020/2022/2026 evening-batch pattern; and the absence of NQ outcome
contamination. Those are cited below where needed and were not re-audited.

---

## 2. Corrected status

```
G3_HISTORICAL_STATUS                    = PARTIAL
HISTORICAL_PIT_SAFE_START               = 2014-03-26
PRE_SAFE_PERIOD                         = UNRESOLVED   (2010-06-06 -> 2014-03-25)
FULL_SAMPLE_AUM_AVAILABLE_BY            = UNKNOWN
SAFE_PERIOD_AUM_AVAILABLE_BY            = NEXT_TRADING_DAY_OPEN (09:30 ET on t),
                                          TYPICAL, NOT GUARANTEED - see G-11
R2_PRE_S1_TIMING_BLOCKER                = YES
OWNER_SAMPLE_BOUNDARY_DECISION_REQUIRED = YES
TARGET_FUND_HISTORICAL_TIMING_EVIDENCE  = PARTIAL
```

`2014-03-26` is the **earliest date for which there is positive evidence** that the
published file carried an `Assets Under Management` column and was written that same
evening with that date's row. It is not a claim that the field appeared on that date;
it is the earliest date the archive evidences.

---

## 3. Why the pre-2014 period fails, in one paragraph

It is not a timing failure. The timing evidence for 2011-2012 is actually strong —
six files written at 2011-07-18 19:44:26 ET to the second, and pre-open retrievals on
2012-09-18 08:39 ET and 2012-09-25 08:18 ET confirming the prior trading day was
already there. **The failure is that the field R2 uses did not exist in the published
artifact.** The 2011 and 2012 vintages carry eight columns ending at
`Shares Outstanding (000)`; there is no `Assets Under Management` column. What was
publishable then was `NAV x shares`, at integer-thousand share precision. Today's AUM
column reproduces that product — verified on 24 fund-date observations, agreeing
between 0 and 1.65e-2 relative, with the residual explained entirely by the coarser
published share precision — but the validation used six **non-target** funds, and no
contemporaneous 2010-2012 capture of QLD, QID, PSQ, TQQQ or SQQQ exists. Treating
today's AUM column as the 2011 published value therefore imports precision the public
file did not carry.

---

## 4. The new material finding: publication is not guaranteed even after 2014

On **2016-04-01**, a normal NYSE trading day, the batch did not run. At
**2016-04-03 20:01:54 ET** (UPRO) and **2016-04-04 00:19:39 ET** (SSO) the published
files' newest row was still 2016-03-31, both carrying
`Last-Modified: 2016-03-31 18:25:30 ET` — identical to the second, so the whole batch
was stalled, not one file. Both responses came directly from `Apache/2.2.3` with no
`Cache-Control`, `Expires`, `Age` or `Via` header, so this is the origin's state, not
a caching artifact. Today's files all carry a 04/01/2016 row, so it was back-filled
at least ~2.5 days late.

Across 15 independent contemporaneous retrievals spanning 2011-2018, **13 showed zero
missing trading days and 2 (the same stalled batch) showed one**. So the
next-trading-day-open bound describes the normal case and fails in at least one
observed case.

```
G-11 (NEW, BLOCKING for a per-day guarantee)
  The ProShares publication batch can miss a trading day. A design that assumes
  A_{i,t-1} is present every day would silently substitute an older value.
  S1 must carry an explicit STALENESS RULE - a per-date check that the prior
  trading day's row exists - and must pre-declare what happens when it does not.
  This is a design obligation, not something feasibility can dispose of, and it
  cannot be verified retrospectively from the current file, which carries no
  record of when each row was added.
```

---

## 5. Sample-boundary discipline

**The safe-start date was determined by schema evidence alone.** To make the absence
of post-hoc selection checkable rather than merely asserted: truncating at 2014-03-26
would **remove the part of the sample most favourable to R2's scientific case**. The
accepted feasibility work measured `K_t` composition inverting from **QID-dominated
(68.7% on 2010-06-07)** to **TQQQ-dominated (79.0% on 2021-12-31)**, with the
inverse-fund share of `K_t` ranging 10.7%-81.6%. The early era is where the
compositional channel — R2's only route to content beyond same-day return — is most
distinctive. Cutting it makes R2's case **harder**, not easier.

**I have not changed R2's Development sample start, and must not.** The window
remains `2010-06-06 → 2022-01-01 exclusive` until Aaron decides otherwise. Historical
PIT evidence determines **data eligibility only**; it is not, and may not become, a
reason to prefer a period on the basis of signal strength. No R2 outcome was
inspected in reaching any conclusion here.

---

## 6. Failed searches, recorded

| search | result |
|---|---|
| Wayback captures of `/etfdata/` anything in **2013** | **zero** |
| Wayback capture of the `/etfdata/` or `/etfdata/ByFund/` directory index, any date | **none** |
| Wayback capture of the master `/etfdata/historical_nav.csv` before 2021 | **none** (earliest 2021-11-30) |
| Target-fund CSV captures 2010-2019 | **TQQQ 2018-09-29 only**; QID none ever; QLD earliest 2024; PSQ earliest 2023; SQQQ 2016 captures are 302 redirects, earliest 200 is 2023 |
| ProShares fund pages 2010-2015 for a Net Assets field | **absent** — pages show NAV, NAV change, market price, volume only |
| ProShares first-party statement of *publication* (not calculation) time | **none found**; 2010 page documents "NAV Calculation Time 4:00 p.m. ET" only |
| Nasdaq Fund Network / MFQS as a historical TNA source | **rejected** — the NFN valuation message carrying `Total Net Assets` / `Total Shares Outstanding` (Category F, Type J) is marked **"As of TBD 2027"**, i.e. forthcoming. No historical 2010-2019 NFN specification establishing ETF TNA dissemination was found |
| Tuzun / Morningstar Direct availability timing | **none** — the paper gives fields and sample (2006-06-19 → 2011-12-31) but no statement of when data were available to users |
| Mathis & Moerke / ETF Global availability timing | **none** — daily-frequency AUM is stated, availability timing is not; sample begins 2012 |
| Fund-page link text as a schema bracket | **rejected by control check** — identical wording persisted to 2014-07-02, months after the AUM column is directly observed |

---

## 7. Owner decisions this raises

```
OD-5  SAMPLE BOUNDARY (Owner / S1 design decision - NOT taken here)
      Given HISTORICAL_PIT_SAFE_START = 2014-03-26, does R2:
        (a) restrict the Development sample to the PIT-safe period;
        (b) keep 2010-06-06 and carry the pre-2014 period under an explicitly
            declared reconstruction assumption (today's AUM column stands for the
            contemporaneous NAV x shares product), disclosed as a limitation;
        (c) commission further archival work to close R-1 and R-2;
        (d) park R2 on PIT grounds.
      Changing the sample start is an Owner/S1 decision. This report does not make it.

OD-6  STALENESS RULE (S1 design obligation created by G-11)
      S1 must pre-declare a per-date staleness check and its handling. Aaron should
      decide whether that is a design detail or needs an explicit ruling.
```

Cheapest route to (c), if wanted: the archive holds the parallel ProFunds
`aadata/ByFund/historical_nav-<TICKER>.csv` tree with captures from **2013-06** and
**2013-09** — the same publisher's batch. It would not give target-fund AUM, but it
could bracket the schema change inside R-2. Not attempted here; it is corroboration,
not target-fund evidence.

---

## 8. Outcome blindness

```
NQ_DATA_DECODED = NO     NQ_RETURN_COMPUTED = NO     R2_PNL_COMPUTED = NO
PREDICTIVE_RELATIONSHIP_TESTED = NO                  ENTRY/EXIT/THRESHOLD CHOSEN = NO
L_t CONSTRUCTED = NO     VOLUME/LIQUIDITY STATISTIC COMPUTED = NO
S1_PREREG_CREATED = NO   TRIAL_REGISTRY CREATED = NO TRIAL_CONSUMED = NO
R2_S1_AUTHORIZED = NO
```

The OD-1 grant over the local NQ Development archive exists and was **not exercised**.
Everything inspected was archived ProShares/ProFunds HTTP artifacts, CSV date and
share/NAV/AUM columns, archived ProShares fund pages, and two already-retrieved
academic PDFs plus the Nasdaq NFN specification.
