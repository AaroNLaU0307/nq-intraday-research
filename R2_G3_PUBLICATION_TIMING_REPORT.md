# R2_G3_PUBLICATION_TIMING_REPORT

```
RECORD_TYPE = GAP_CLOSURE_EVIDENCE
LINEAGE     = R2
GAP         = G-3  publication timing of prior-close ProShares AUM
CREATED     = 2026-09-19
STAGE       = S0 / DATA FEASIBILITY - PRE-S1
STANDARD    = R2_G3_ACCEPTANCE_CRITERIA.md, written BEFORE this evidence existed
SCOPE       = fund-side publication timing ONLY. No NQ data was decoded, and no
              tau, entry, exit, threshold or signal definition is chosen here.
```

All times are ET unless marked. The auditing machine is UTC+8; every ET time below
is derived from a UTC timestamp recorded at retrieval, and EDT = UTC-4 applies on
every date cited.

---

## 1. PRIOR_G3_EVIDENCE

Read back from the accepted artifacts and re-verified against the stored probe.

What the earlier work **did** establish:

- `R2_DATA_SOURCE_AUDIT.md` B-1(a) and `R2_FEASIBILITY_REPORT.md` section 5.1(2): at
  **15:58 ET on Thursday 2026-09-17**, the most recent row in all five ProShares
  files was **Wednesday 2026-09-16**. Day `t`'s own row was absent.
- Therefore: the `t-1` row was present by 15:58 ET on `t`, and there is no same-day
  contamination risk from this feed.
- Probe integrity re-verified today: the five files in
  `data_probe/proshares_nav_2026-09-17/` still hash to the recorded SHA-256 values,
  and all five carry `09/16/2026` as their newest row — so the five funds were
  **in sync** at that observation.

What it **did not** establish, and this is stated no more strongly than the evidence
allows:

- It did **not** prove publication before 15:30 ET. A single retrieval at 15:58 ET
  bounds publication of the `t-1` row at `<= 15:58 ET on t` and nothing tighter.
- It did **not** identify any mechanism, metadata or documentation explaining *when*
  the row appears. It was one observation with no supporting semantics.
- It carried **no** repeated evidence, so no defensible `T` could be stated.

G-3 was correctly left OPEN on that basis.

---

## 2. G3_ACCEPTANCE_CRITERIA

Fixed in `R2_G3_ACCEPTANCE_CRITERIA.md` before any new evidence was collected, in a
separate file so the ordering is auditable. In brief: Level A = documented
publication rule *for the quantity R2 actually uses*; Level B = timestamped retrieval
with enough repetition or supporting metadata to make `T` defensible; Level C =
proven availability by the next trading day's open. Nine named forms of evidence are
declared inadmissible in advance, including filesystem modified time after download,
cache time, "daily NAV must be ready by morning", industry convention, and any bound
adopted because it is convenient. A single weekend observation is declared weak on
its own. The bound must hold for all five funds, not the fastest.

---

## 3. FIRST_PARTY_DOCUMENTATION

Searched ProShares' own pages and the SEC rule text. The result is a clean negative
on Level A, and it matters that it is reported as a negative.

### 3.1  ProShares first-party — calculation time yes, publication time no

From the ProShares *Frequently Asked Questions on Performance and Pricing* page,
verbatim:

> "NAV is calculated by a standard methodology (detailed in the prospectus), and is
> set when the markets for the ETF's underlying securities close. This is usually
> 4:00 p.m. ET, when equity markets close, but some ETFs calculate NAVs at other
> times, when their underlying securities markets close."

The same page **contains no statement of when NAV, net assets, or fund data are
posted or published to the website** — no deadline, no "available by" time, no
publication schedule. This is exactly the distinction the task required be kept:
**a calculation timestamp is not a publication timestamp**, and ProShares documents
only the former.

One thing the page does establish, which upgrades the source's standing: it directs
users to the file this work relies on —

> "For historical daily NAV changes on any ProShares ETF, go to the Resources page
> and click on the file labeled 'Historical NAVs for all ProShares ETFs' in the ETF
> Data Downloads section."

So the historical NAV/AUM download is a **documented first-party ProShares data
product**, not an undocumented artifact. It carries no timing statement.

### 3.2  SEC Rule 6c-11 — binding, adjacent, and NOT sufficient

Retrieved the adopting release (SEC Release 33-10695, *Exchange-Traded Funds*,
effective 2019-12-23) and read the rule text. Verbatim, rule 6c-11(c)(1):

> "(c) Conditions. (1) Each business day, an exchange-traded fund must disclose
> prominently on its website, which is publicly available and free of charge:
>
> (i) **Before the opening of regular trading on the primary listing exchange** of
> the exchange-traded fund shares, the following information (as applicable) for each
> portfolio holding that will form the basis of the next calculation of current net
> asset value per share: (A) Ticker symbol; (B) CUSIP or other identifier;
> (C) Description of holding; (D) Quantity of each security or other asset held; and
> (E) Percentage weight of the holding in the portfolio;
>
> (ii) The exchange-traded fund's **current net asset value per share, market price,
> and premium or discount, each as of the end of the prior business day**; ..."

Three reasons this does **not** reach Level A for R2, all of which my acceptance
criteria anticipated:

1. **It names the wrong quantity.** Subparagraph (ii) requires NAV per share, market
   price and premium/discount. It does **not** require total net assets, assets under
   management, or shares outstanding — which is precisely what R2 uses.
2. **The intraday deadline attaches to the wrong subparagraph.** "Before the opening
   of regular trading" is the qualifier on **(i)**, the holdings disclosure. Item
   (ii) carries the "each business day" obligation and the "as of the end of the
   prior business day" content requirement, but no explicit intraday deadline in the
   rule text.
3. **It post-dates most of the sample.** Effective 2019-12-23. The release does note
   the "as of the end of the prior business day" formulation "is consistent with our
   existing exemptive orders", which is useful background for the pre-2019 period but
   is not itself a publication-time rule.

```
LEVEL A  =  NOT REACHED.
```

---

## 4. DIRECT_ENDPOINT_AND_METADATA_AUDIT

This is where the evidence actually is.

### 4.1  The five R2 endpoints, retrieved with full headers

Request window: **2026-09-19 13:04:56Z to 13:05:06Z UTC = 09:04:56 to 09:05:06 ET**,
Saturday. Server `Date` headers corroborate the client clock to within two seconds.

| fund | HTTP | Content-Length | `Last-Modified` (GMT) | = ET | ETag | newest row |
|---|---|---|---|---|---|---|
| QLD  | 200 | 455921 | Sat, 19 Sep 2026 01:01:02 | **2026-09-18 21:01:02** | `"6f4f1-65bcb8d084500"` | 09/18/2026 |
| QID  | 200 | 454971 | Sat, 19 Sep 2026 01:00:56 | **2026-09-18 21:00:56** | `"6f13b-65bcb8caaf0e7"` | 09/18/2026 |
| PSQ  | 200 | 414968 | Sat, 19 Sep 2026 01:01:06 | **2026-09-18 21:01:06** | `"654f8-65bcb8d3add4b"` | 09/18/2026 |
| TQQQ | 200 | 409104 | Sat, 19 Sep 2026 01:01:01 | **2026-09-18 21:01:01** | `"63e10-65bcb8cf5bdb5"` | 09/18/2026 |
| SQQQ | 200 | 405549 | Sat, 19 Sep 2026 01:01:12 | **2026-09-18 21:01:12** | `"6302d-65bcb8d94b4e1"` | 09/18/2026 |

`Server: Apache/2.4.37 (Red Hat Enterprise Linux)`. No `Cache-Control`, no `Expires`,
no `Age`, no CDN headers — the response comes from the origin, so `Last-Modified`
is the origin file's modification time and not an intermediary's.

### 4.2  Making the `Last-Modified` semantics clear enough to use

The task forbids treating `Last-Modified` as row-publication proof "unless its
semantics are sufficiently clear". Three independent checks make them clear:

**Check 1 — the ETag decodes to the same instant.** These are Apache
`FileETag MTime Size` ETags of the form `hex(size)-hex(mtime_in_microseconds)`.
Decoded:

| fund | ETag size field | Content-Length | equal? | ETag mtime decoded (UTC) | matches `Last-Modified`? |
|---|---|---|---|---|---|
| QLD  | 455921 | 455921 | **yes** | 2026-09-19 01:01:02.882Z | **yes** |
| QID  | 454971 | 454971 | **yes** | 2026-09-19 01:00:56.765Z | **yes** |
| PSQ  | 414968 | 414968 | **yes** | 2026-09-19 01:01:06.197Z | **yes** |
| TQQQ | 409104 | 409104 | **yes** | 2026-09-19 01:01:01.667Z | **yes** |
| SQQQ | 405549 | 405549 | **yes** | 2026-09-19 01:01:12.085Z | **yes** |

The size component equals Content-Length **exactly** for all five, and the decoded
mtime equals the `Last-Modified` header **to the second** with sub-second precision
added. Two independent header fields, generated by different code paths from the same
`stat()`, agree. This is a static file on disk and `Last-Modified` is when it was
written.

**Check 2 — the files are NOT touched nightly, so mtime means something.** The
directory index at `/etfdata/ByFund/` lists **238** per-fund `*-historical_nav.csv`
files. **173** were written on 2026-09-18; **65 were not**, with mtimes frozen as far
back as 2020. A blanket nightly `touch` would have moved all 238. It did not.
Therefore a file's mtime is the last time that fund's data was actually written.

**Check 3 — the file is append-only, so the write that moved mtime added the newest
row.** Comparing the stored 2026-09-17 probe against today's download:

| fund | probe rows | today rows | new rows | overlapping rows | byte-identical |
|---|---|---|---|---|---|
| QLD  | 5093 | 5095 | 2 (09/17, 09/18) | 5093 | **5093 / 5093** |
| QID  | 5078 | 5080 | 2 (09/17, 09/18) | 5078 | **5078 / 5078** |
| PSQ  | 5093 | 5095 | 2 (09/17, 09/18) | 5093 | **5093 / 5093** |
| TQQQ | 4176 | 4178 | 2 (09/17, 09/18) | 4176 | **4176 / 4176** |
| SQQQ | 4176 | 4178 | 2 (09/17, 09/18) | 4176 | **4176 / 4176** |

Across a two-day gap the files gained **exactly** the two intervening trading days
and **not one existing row changed**. One row per trading day, appended. (This is also
direct, if narrow, evidence against the G-6 restatement risk: zero restatements
observed over the interval tested.)

Taken together: the file serving `09/18/2026` as its newest row was written at
**21:00:56-21:01:12 ET on 2026-09-18**, and that write is the one that appended the
09/18 row.

### 4.3  The directory index, and its timezone verified rather than assumed

`/etfdata/` and `/etfdata/ByFund/` both return Apache autoindexes with a
`Last modified` column. Apache prints that column in **server-local** time, so the
timezone had to be established, not assumed. Two spot checks:

| file | index column | `Last-Modified` header (GMT) | header converted at UTC-4 |
|---|---|---|---|
| `/etfdata/historical_nav.csv` | `2026-09-18 21:00` | Sat, 19 Sep 2026 01:00:52 | **2026-09-18 21:00:52 ET** |
| `/etfdata/etf_splits.csv` | `2026-09-18 05:00` | Fri, 18 Sep 2026 09:00:38 | **2026-09-18 05:00:38 ET** |

Both match. **The index column is US Eastern**, so every index time quoted below is
already ET.

### 4.4  What else the index shows

```
/etfdata/  index, times in ET
  ByFund/                     2026-09-18 22:28   (dir)
  historical_nav.csv          2026-09-18 21:00   50M   all-funds master file
  etf_performance.csv         2026-09-18 05:00   127K
  etf_splits.csv              2026-09-18 05:00   24K
  psdlyhld.csv / .xls         2026-09-18 22:27   1.8M / 3.4M  daily holdings
```

The 50 MB `historical_nav.csv` master carries the **same 21:00 ET write time** as the
per-fund files — it is the same batch, and it is the file ProShares' own FAQ calls
"Historical NAVs for all ProShares ETFs". Recorded as a more efficient acquisition
path for S1; not a timing finding in itself.

---

## 5. HISTORICAL_OR_ARCHIVAL_EVIDENCE

### 5.1  Internet Archive — unavailable today, stated plainly

Both CDX queries for `accounts.profunds.com/etfdata/ByFund/...` returned the Internet
Archive's **"Internet Archive services are temporarily offline"** page rather than
index data. No Wayback capture evidence could be obtained in this task. This is a
fact about today, not a finding about the data: if Aaron wants a second, fully
independent line of evidence later, the Wayback route remains open.

### 5.2  Frozen terminal-write mtimes — a usable multi-year substitute

The 65 stale files in `/etfdata/ByFund/` preserve, in their mtimes, the clock time at
which the ProShares batch last wrote them. Their newest rows were then fetched and
compared. **46 of the 65 share a single `2020-02-17 13:14` timestamp — a midday bulk
filesystem copy, not a data write — and are excluded as meaningless for timing.** The
remaining 19 fall into six genuine terminal-write events:

| batch date and time (ET) | funds in that write | newest row in file | relation |
|---|---|---|---|
| **2020-04-02 19:25** | FINU, FINZ, SCOM, UBIO, UCOM, ZBIO | **04/02/2020** | **same day, evening** |
| 2020-04-02 19:25 | OILD, OILU | 04/01/2020 | +1 day — fund had no 04/02 NAV (mid-liquidation) |
| 2020-10-13 08:31 | XCOM, YCOM | 10/12/2020 | +1 day, **morning**, 08:31 ET |
| 2022-05-12 07:43 | CROC, EUFX | 05/11/2022 | +1 day, **morning**, 07:43 ET |
| **2022-05-16 20:21** | ALTS, DDG, EMSH, FUT, RALS, SBM | **05/16/2022** | **same day, evening** |
| 2024-05-06 18:40 | SPXB | 05/03/2024 | +3 days (Fri row, Mon write) — terminal cleanup |

Read carefully, this gives four **independent batch-clock observations spanning six
years**, and they say the same thing:

- the batch that appends date `d`'s rows runs **on date `d`, in the evening**:
  **19:25 ET (2020)**, **20:21 ET (2022)**, **21:00-21:01 ET (2026)**;
- the only writes that land the *next* morning are **terminal cleanup writes for
  funds being delisted**, and even those fall at **07:43 and 08:31 ET — still before
  the 09:30 open**.

Two limitations stated rather than buried. First, these are **terminal** writes, so
the sample of dates is selected on fund-delisting events, not random. Second, the
evening batch time has **drifted later** across the six years (19:25 -> 20:21 ->
21:01), which is a reason to leave headroom in the bound rather than pin it at 21:01.

---

## 6. LIVE_OBSERVATION

```
OBSERVATION_TIME_ET   = 2026-09-19  09:04:56 - 09:05:06 ET   (Saturday)
OBSERVATION_TIME_UTC  = 2026-09-19  13:04:56Z - 13:05:06Z
MARKET CALENDAR       = WEEKEND. Last trading day = Friday 2026-09-18.
                        Next trading day = Monday 2026-09-21.
```

| ETF | LATEST_ROW_DATE | PRIOR_TRADING_DAY | T_MINUS_1_PRESENT | CURRENT_DAY_PRESENT |
|---|---|---|---|---|
| QLD  | 09/18/2026 | 09/18/2026 | **YES** | n/a - not a trading day |
| QID  | 09/18/2026 | 09/18/2026 | **YES** | n/a |
| PSQ  | 09/18/2026 | 09/18/2026 | **YES** | n/a |
| TQQQ | 09/18/2026 | 09/18/2026 | **YES** | n/a |
| SQQQ | 09/18/2026 | 09/18/2026 | **YES** | n/a |

**Honest weight of this observation.** Taken alone it is the weak case my own
acceptance criteria warned about: the Friday-to-Monday pair is the easiest possible
`(t-1, t)` gap, and nothing that holds across 65 hours establishes what holds across
a 17-hour overnight gap. **It is not what closes G-3.** Its value is that it carried
the HTTP metadata in section 4, which is what closes G-3 — and that metadata dates
the write to **Friday evening**, not to the weekend.

No future or background monitoring was scheduled. This task finishes on evidence
obtainable now.

---

## 7. CROSS_FUND_CONSISTENCY

The bound must hold for the whole universe, not the fastest fund.

**Today's batch, all 173 currently-updating ProShares funds:**

```
ET clock-time histogram of file writes on 2026-09-18:
    21:00  ->  60 files
    21:01  -> 113 files
    (no other minute)
```

A single batch, 173 files, inside a **two-minute window**.

**The five R2 funds, from the same index:**

```
QID   2026-09-18 21:00      (earliest of the five)
QLD   2026-09-18 21:01
PSQ   2026-09-18 21:01
SQQQ  2026-09-18 21:01
TQQQ  2026-09-18 21:01      latest to the second: SQQQ at 21:01:12
```

Spread across the R2 universe: **16 seconds** (21:00:56 to 21:01:12). The latest
fund, SQQQ, governs; no fund is materially slower than another. The prior
2026-09-17 observation independently found all five in sync at `t-1 = 09/16`.

There is **no material cross-fund difference in publication timing**, so no
fund-specific carve-out is needed and the universe-wide bound is not being set by one
laggard.

---

## 8. PROVEN_AVAILABILITY_BOUND

```
G3_STATUS           = CLOSED_PASS
AUM_AVAILABLE_BY    = NEXT_TRADING_DAY_OPEN   (09:30 ET on trading day t)
EVIDENCE_LEVEL      = B
```

**Why CLOSED_PASS.** The closure rests on Level B evidence — direct timestamped
retrieval plus origin-file metadata whose semantics were established by three
independent checks (ETag/Content-Length/`Last-Modified` agreement; 65 frozen files
proving mtime is not a nightly touch; append-only verification against the stored
2026-09-17 probe) — corroborated by four batch-clock observations spanning 2020, 2022
and 2026, and by cross-fund consistency across 173 files in a two-minute window.

**Why the bound is stated conservatively at the next trading day's open rather than
at 21:01 ET on `t-1`.** The metadata supports the tighter statement for the instance
observed, and every batch observed in six years completed by 21:01 ET on the row
date. But:

- the evening batch time has drifted later over six years (19:25 -> 20:21 -> 21:01),
  so pinning the bound at the latest observed value leaves no headroom;
- the multi-year batch observations come from a date sample selected on delistings;
- the one trading-day retrieval in hand (2026-09-17, 15:58 ET) bounds availability
  only at `<= 15:58 ET on t`, and the 2026-09-19 retrieval is the weak weekend case.

The next-trading-day open is the strongest bound the present evidence proves without
strain, and — importantly — **it is not the bound R2 would prefer**. It is adopted
because it is what the evidence supports, not because it is convenient. Under the
acceptance criteria this is a Level-C-shaped bound carried by Level-B evidence, and
the level is reported as the evidence, not the shape.

**What would tighten it, if Aaron ever wants it tighter.** A timestamped poll of the
five URLs at a fixed pre-open and pre-15:30 clock time over ~10 consecutive trading
days, recording `Last-Modified` and the newest row each time, would support a bound
in the region of **21:30 ET on `t-1`**. That is a forward-collection task, not a
blocker, and S1 may not assume it.

**Not claimed:** no Level A documentation exists for the publication time of this
quantity (section 3), and no Wayback evidence was obtainable (section 5.1).

---

## 9. S1_TIMING_CONSTRAINT

```
S1_TAU_CONSTRAINT = tau > 09:30 ET on trading day t
```

Strict inequality, because the proven bound is the market open itself and the datum
must be available strictly before the decision is taken.

```
AUM_AVAILABLE_BY = 09:30 ET       does NOT mean       tau = 09:30 ET
```

This task selects no `tau`, no entry, no exit, no threshold and no signal definition.
The constraint above is the whole of what G-3 contributes to S1.

```
G3_CLOSES_DATA_TIMING_BUT_CREATES_MECHANISM_TIMING_BLOCKER = NO
```

The bound sits at the open, leaving the entire regular session available to S1. The
R2 mechanism is a late-day phenomenon, so every plausible pre-close interval remains
open and nothing about G-3 forces the design into a corner. No alternative signal
definition was considered, and none was needed.

---

## 10. UPDATED_PROJECT_ARTIFACTS

The R2 project is **not a git repository** (`git rev-parse` returns *fatal: not a git
repository*), and no repository was initialised — creating version-control
infrastructure is not part of closing G-3. Artifacts are plain files.

| path | action |
|---|---|
| `R2_G3_ACCEPTANCE_CRITERIA.md` | **new** - written before any new evidence, as its own file so the ordering is auditable |
| `R2_G3_PUBLICATION_TIMING_REPORT.md` | **new** - this file |
| `data_probe/g3_timing_2026-09-19/` | **new** - the five CSVs as retrieved, their raw HTTP response headers, and both Apache directory indexes, with SHA-256 recorded in section 13 |
| `PROJECT_STATE.md` | **updated** - G-3 closed; delegated Owner rulings recorded; blocker list revised |
| `R2_DATA_SOURCE_AUDIT.md` | **amended** - dated amendment appended; accepted body left intact |
| `R2_FEASIBILITY_REPORT.md` | **amended** - dated amendment appended; accepted body left intact |

Deliberately **not** created: no sealed preregistration, no trial registry, no signal
definition, no run identity, no outcome bundle.

### 10.1  Delegated Owner rulings, recorded as what they are

```
DELEGATED_OWNER_RULING
  DELEGATED_BY = Aaron
  DECIDED_BY   = Fable
  ACCEPTED_BY  = ChatGPT

  OD-1  DATA AUTHORITY = GRANT the existing local NQ Development archive to R2
                         under a NEW R2 lineage-specific grant.
                         For this G-3 task the archive was NOT decoded or inspected.
  OD-2  SCOPE          = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY.
                         Universe: QLD, QID, PSQ, TQQQ, SQQQ.
  R2_S1                = NOT AUTHORIZED
  R2_OUTCOME_EXPOSURE  = NONE
  S0 DATA FEASIBILITY  = PASS / CLOSED
```

These were delegated and decided through that chain. They are **not** recorded as
Aaron personally selecting each ruling.

### 10.2  Accepted Fable reservations — carried, not resolved

Recorded here because one of them bears directly on text I previously wrote:

1. **Post-2022 is NOT assigned to Validation / Lockbox.** Its future sample tier
   remains **UNASSIGNED**. Nothing in this task assigns it.
2. **Missing mutual-fund reset flow is NOT assumed to create only attenuation.** It
   is **KNOWN MEASUREMENT OMISSION / MAGNITUDE UNKNOWN**.
3. **Mutual-fund flow is NOT assumed to occur only at the close and therefore not to
   matter pre-close.**

Reservations 2 and 3 **supersede** the countervailing argument in
`R2_FEASIBILITY_REPORT.md` section 11 row G-1, which reasoned that the mutual-fund
sleeve's omission is one-directional and that its 4pm NAV strike makes it a
close-print rather than a pre-close phenomenon. That reasoning is withdrawn as an
assumption. The amendment appended to that file records the withdrawal. None of these
three is part of G-3 and none is resolved here.

---

## 11. REMAINING_PRE_S1_BLOCKERS

```
R2_PRE_S1_BLOCKERS_REMAINING = NONE
R2_READY_FOR_S1_DESIGN       = YES
```

G-3 was the only remaining pre-S1 blocker named by the accepted feasibility work;
OD-1 and OD-2 disposed of the other two. It is now closed, so nothing blocks S1
**design**.

**This does not authorize S1.** Aaron / ChatGPT must issue a separate S1 design
authorization. `R2_S1_AUTHORIZED = NO`.

Carried forward as **non-blocking** items, unchanged in status by this task —
G-1 mutual-fund sleeve (now under reservations 2 and 3) · G-2 broader-scope assets
(moot under OD-2 = NDX-only) · G-4 never-launched confirmation · G-5 SEC 2016/2024
series files · G-6 vintage/restatement, **partially and favourably tested today**:
zero restatements across 20,616 overlapping rows over the 09-17 to 09-19 interval ·
G-7 prospectus-dated mandate table, still S1's first collection task · G-8 no local
NQ data after 2022-01-01, and the post-2022 sample tier is UNASSIGNED per reservation
1 · G-9 intraday rebalance timing unobservable in principle.

One genuinely new, minor residual from today, recorded rather than hidden:

- **G-10 (new, non-blocking).** The ProShares endpoint exposes an open Apache
  directory index and serves files over plain Apache with no cache headers. Nothing
  guarantees the URL pattern, the index, or the `Last-Modified`/ETag semantics will
  persist. Any S1 acquisition should snapshot, hash and record headers at collection
  time rather than assume the endpoint is stable. Mitigated by the fact that the
  master file is first-party documented (section 3.1).

---

## 12. OUTCOME_BLINDNESS_AUDIT

```
NQ_DATA_DECODED               = NO
NQ_RETURN_COMPUTED            = NO
R2_PNL_COMPUTED               = NO
PREDICTIVE_RELATIONSHIP_TESTED = NO
ENTRY_TIME_CHOSEN             = NO
EXIT_TIME_CHOSEN              = NO
THRESHOLD_CHOSEN              = NO
S1_PREREG_CREATED             = NO
TRIAL_CONSUMED                = NO
```

The OD-1 grant over the local NQ Development archive exists but was **not exercised**:
no file in `C:\Users\Aaron\quant-data\databento-archive\` was opened, decoded,
listed for content, or referenced for any price, return, volume or liquidity value in
this task. G-3 is entirely fund-side.

Everything inspected was: ProShares HTTP responses and their headers; two Apache
directory indexes; six ProShares CSV files' date columns and row counts; the ProShares
performance-and-pricing FAQ; the SEC Rule 6c-11 adopting release; and the previously
stored R2 probe. No quantity derived from NQ, and no relationship between any fund
quantity and any market outcome, was computed at any point.

---

## 13. EVIDENCE PROBE — `data_probe/g3_timing_2026-09-19/`

Retrieved 2026-09-19 09:04:56-09:05:06 ET. SHA-256:

```
4179071ba4d67741f49a5b353cfcd77324ccd29db258cab66183f5dec1ad8bb3  ByFund-directory-index.html
8450c53d3a70803a41e6d700c68b7d32cf7dbcd04d2413a52ba941cfe27119b3  etfdata-directory-index.html
d27ffbfa88b0bee392a84ac34bbe96c17b0ab4c6459f3cebc72c0b978d35a7fd  PSQ-historical_nav.csv
e4cf0f756c6da6238632560216e053deab049774fd89f6edce7241ca538127da  PSQ-http-response-headers.txt
2a2339d614797a0436a55ec3696aafbe1c1ef3711c6fb3ddb4c000d2d96b254a  QID-historical_nav.csv
87eff147750316191b81bc853db777f2a74cb525a1111854068287565f657d94  QID-http-response-headers.txt
6f567db402587d0bdea0815325a2c3fc90af6113b8a9ec4b3b569989be5f1839  QLD-historical_nav.csv
41f888b3c51d3128332476d83cd1a5db27fb0b357f3aeceb4660ec63729429ed  QLD-http-response-headers.txt
a7cf5bbf21859afd95e56f7b9d00f723b1859388d12242c08d15027fbe857bcf  SQQQ-historical_nav.csv
42a00ce27c98a084eaca99787905b00c2893039f72483ce66372bf1333ff1b93  SQQQ-http-response-headers.txt
7905de6556cdacf85fd35d9e26dc41a73857263b3de0c188999a4d99e4f2b2d2  TQQQ-historical_nav.csv
0dc2706e047911a13ac115ff42dcb7cf19e195bb8ffbf9fdd654c9465bdc6859  TQQQ-http-response-headers.txt
```

A dated evidence snapshot for the G-3 finding. **Not a research dataset**, and it
carries no data grant.

### Sources

- ProShares, *Frequently Asked Questions on Performance and Pricing* —
  https://www.proshares.com/faqs/performance-pricing-faqs
- ProShares / ProFunds ETF data endpoints — https://accounts.profunds.com/etfdata/
  and https://accounts.profunds.com/etfdata/ByFund/
- SEC Release 33-10695, *Exchange-Traded Funds* (rule 6c-11), effective 2019-12-23 —
  https://www.sec.gov/rules/final/2019/33-10695.pdf
- `R2_DATA_SOURCE_AUDIT.md` Part B-1 and `data_probe/proshares_nav_2026-09-17/`
  (this project, prior session)

---

# CONTROLLER HOLD — 2026-09-19 : THIS REPORT'S CLOSE IS NOT ACCEPTED

```
G3_REPORT         = HOLD
MATERIAL_BLOCKERS = 1
BLOCKER           = 2010-2019 HISTORICAL POINT-IN-TIME AVAILABILITY GAP
PRIOR_G3_CLOSE    = NOT ACCEPTED BY CONTROLLER
```

**The body above is left intact as the record of what was found about the CURRENT
endpoint on 2026-09-19. Its `G3_STATUS = CLOSED_PASS` and its
`AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN` must NOT be read as full-sample claims.**

The error was scope, not method: the bound was evidenced from 2020 / 2022 / 2026
artifacts and then stated for a Development window beginning 2010-06-06. Later
evidence shows the published file carried **no `Assets Under Management` column at
all** in its 2011 and 2012 vintages, so modern behaviour could not have been
projected backwards.

Corrected status, evidence and regime timeline:

- `R2_G3_HISTORICAL_PIT_AMENDMENT.md`
- `R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md`
- `data_probe/g3_historical_pit_2026-09-19/`

```
G3_HISTORICAL_STATUS        = PARTIAL
HISTORICAL_PIT_SAFE_START   = 2014-03-26
PRE_SAFE_PERIOD             = UNRESOLVED   (2010-06-06 -> 2014-03-25)
FULL_SAMPLE_AUM_AVAILABLE_BY = UNKNOWN
R2_PRE_S1_TIMING_BLOCKER    = YES
```

Sections 4-7 of the body (endpoint existence, 2026 metadata semantics, five-fund
synchronisation, the 2020/2022/2026 evening-batch pattern) remain accepted and were
not re-audited. Section 11's `R2_READY_FOR_S1_DESIGN = YES` is **withdrawn**.
