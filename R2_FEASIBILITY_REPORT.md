# R2_DATA_FEASIBILITY_REPORT

```
RECORD_TYPE = DATA_FEASIBILITY_REPORT
LINEAGE     = R2
CREATED     = 2026-09-18
STAGE       = S0 / DATA FEASIBILITY - PRE-S1
AUTHOR      = Claude Opus 5, Main Agent, fresh top-level session
AUTHORITY   = ../QUANT_WORKFLOW_VNEXT.md
SCOPE       = outcome-blind data feasibility ONLY. No alpha test, no preregistration,
              no trading rule, no timing choice, no purchase.
```

---

## 1. AUTHORITY_AND_EXISTING_WORK

**Authority read.** `QUANT_WORKFLOW_VNEXT.md` (workspace root, cutover 2026-09-12) in
full, plus the workspace `CLAUDE.md` entry point. Lifecycle
`S0 FRAME -> S1 DESIGN+SEAL -> S2 BUILD -> S3 RUN -> S4 VERDICT -> STOP`. This task
sits inside S0. Under section 4 neither of Astra's two normal appearances applies and
no named trigger fired; under section 5 Fable is a constructive design seat and no
design question is open here. No reviewer was dispatched, and none is owed. Owner
gates in section 10 are respected throughout: no data access beyond an existing grant
was taken, nothing was purchased, nothing was pushed, no governance document outside
this new project was modified.

**Existing-work search.** Searched the whole `Quant trade` tree for: leveraged ETF,
LETF, inverse ETF, ProShares, Direxion, QLD, TQQQ, SQQQ, QID, PSQ, Nasdaq-100
rebalance, daily reset, rebalancing demand, closing flow, R2.

```
RESULT:  NO R2 PROJECT EXISTS.  NO DUPLICATE LINEAGE WAS CREATED.
```

The only pre-existing mentions of leveraged-ETF vocabulary are incidental lines inside
four Fable design documents at the workspace root, one archived TSMOM cost report and
one archived README - none of them R2 work. The `R2_*` filename hits inside
`mean-reversion-research/` are that project's internal revision labels (`R2_1`), not
this lineage.

**R2's own provenance.** `nq-event-diffusion-research/R1_S0_PROVENANCE.md` section 2
records R2's disposition as *"RESEARCH, conditional on separate data feasibility"*.
That is the entire basis for this task. **R1 was not reopened**: no R1 outcome, P&L,
interval, event behaviour or verdict was read, and R1's own disposition is not used as
a prior on R2 in either direction. The files read inside that project were the S0
provenance record, the delegated-decisions grant lines, the trial-registry accounting
lines, and the data-adapter module's schema declaration - all pre-outcome governance
and data-plumbing material.

**Project created.** `Quant trade/nq-letf-rebalancing-research/`, labelled
`STAGE = S0 (DATA FEASIBILITY / PRE-S1)` in its `PROJECT_STATE.md`.

---

## 2. R2_MINIMUM_DATA_CONTRACT

Written **before** availability was judged, in `R2_MINIMUM_DATA_CONTRACT.md`. Summary
of what it obliges, by contract section:

| # | requirement | in one line |
|---|---|---|
| 1 | fund identity | point-in-time, survivorship-free universe on a stable identifier, with launch, closure, mandate-change history and reset frequency; ticker is not identity |
| 2 | target leverage | `m_{i,t}` from the document in force at `t`; today's mandate may not be projected backwards |
| 3 | prior-known fund size | `A_{i,t-1}` with a provable pre-`tau` publication time; no backfill, no untested vintage |
| 4 | shares / corporate actions | assets must be split-invariant; per-share series are not; launches, closures, run-off, mergers, ticker changes each handled explicitly |
| 5 | reset mechanics | the equation, derived and source-verified, with an explicit sign convention |
| 6 | causal timing | an `AVAILABLE_BY` for every input; the trailing-window trap and the vintage trap named |
| 7 | normalization | at least one pre-specified, point-in-time, defensible liquidity denominator; not optimized |
| 8 | kill conditions | F-1..F-5 written in advance so the conclusion cannot be reverse-engineered |

**The equation, verified not asserted.** For a daily-reset fund with multiple `m` and
prior-close assets `A`:

```
    dS_{i,t}  =  m_{i,t} * ( m_{i,t} - 1 ) * A_{i,t-1} * r_pre_t
```

aggregated over a single-benchmark universe:

```
    F_t = K_t * r_pre_t ,     K_t = SUM_i m_{i,t}*(m_{i,t}-1)*A_{i,t-1}
    f_t = F_t / L_t = ( K_t / L_t ) * r_pre_t
```

Sign convention: `dS > 0` means buy benchmark exposure, `dS < 0` sell. `m(m-1) > 0`
for every admissible multiple - `+2 -> 2`, `+3 -> 6`, `-1 -> 2`, `-2 -> 6`,
`-3 -> 12` - so **long and inverse funds rebalance in the same direction as the
benchmark and their demands do not cancel**, and a `-3x` fund carries twice the weight
of a `+3x` fund of equal size.

Verified against two independent credible derivations, both quoted in the contract:
Tuzun, *Are Leveraged and Inverse ETFs the New Portfolio Insurers?* (Federal Reserve
Board FEDS 2013-48, section III, which also cites Cheng & Madhavan 2009 for the same
derivation), and Mathis & Moerke, *Liquidity Provision to Leveraged ETFs and Equity
Options Rebalancing Flows* (section 2.3 eq. 6). Both state the same-direction property
explicitly.

**The structural consequence, recorded because it constrains R2's validity.** Over a
single-benchmark universe the sum factorizes into one scalar times the return, so
`sign(F_t) == sign(r_pre_t)` **always, by construction**. R2's entire beyond-return
content therefore lives in the magnitude modulation `K_t / L_t`. Section 9 tests
whether the obtainable data make that modulation non-degenerate.

---

## 3. HISTORICAL_FUND_UNIVERSE

Built outcome-blind from the SEC Investment Company Series and Class annual files
(15 annual vintages, 2010-2026, gaps at 2016 and 2024), cross-checked against EDGAR
full-text search, the ProShares fund directory, and the ProShares per-fund history
endpoint. **Not restricted to funds alive today.** No subsequent NQ return was
examined for any fund.

### 3.1  US-listed Nasdaq-100 daily-reset ETFs - the core mechanism universe

| ticker | fund | issuer | benchmark | m | launch | closure | mandate history | in R2 universe? |
|---|---|---|---|---|---|---|---|---|
| QLD  | Ultra QQQ | ProShares | Nasdaq-100 (NDX) | +2 | 2006-06-19 | live | no change found | **YES** |
| QID  | UltraShort QQQ | ProShares | Nasdaq-100 (NDX) | -2 | 2006-07-11 | live | no change found | **YES** |
| PSQ  | Short QQQ | ProShares | Nasdaq-100 (NDX) | -1 | 2006-06-19 | live | no change found | **YES** |
| TQQQ | UltraPro QQQ | ProShares | Nasdaq-100 (NDX) | +3 | 2010-02-09 | live | no change found | **YES** |
| SQQQ | UltraPro Short QQQ | ProShares | Nasdaq-100 (NDX) | -3 | 2010-02-09 | live | no change found | **YES** |

Launch dates are the first row of each fund's own NAV history file and match the
ProShares fund page's stated inception for TQQQ (2010-02-09). "No change found" means
no mandate change was found in this audit; it is **not** a certification. Contract
section 2 requires a prospectus-dated mandate table, which is S1 collection work.

### 3.2  Registered but, on the evidence, never launched - the survivorship guard

| series | issuer | appears in | evidence |
|---|---|---|---|
| Nasdaq-100 Bull 3X Shares | Direxion Shares ETF Trust | SEC series files 2010, 2011 | EDGAR FTS: N-1A 2008-04-30, NSAR-A, NSAR-B, N-PX only. **No 497, no 485BPOS offering it, no N-CSR.** NSAR-B FY2011 confirms it was series #94 of 134. |
| Nasdaq-100 Bear 3X Shares | Direxion Shares ETF Trust | SEC series files 2010, 2011 | identical evidence; series #95 of 134 |
| Rydex 2x NASDAQ 100 ETF | Rydex ETF Trust | 2010, 2011 | 485BPOS 2008/2009/2010 + 485APOS 2010 - an *effective* registration, stronger than the Direxion pair. **Still no N-CSR.** |
| Rydex Inverse 2x NASDAQ 100 ETF | Rydex ETF Trust | 2010, 2011 | as above |
| Rydex Inverse NASDAQ 100 ETF | Rydex ETF Trust | 2010, 2011 | as above |
| Ultra NASDAQ-100 Equal Weighted | ProShares Trust | 2010, 2011 | 485APOS 2007-07-10 + two 40-APP exemptive applications only |
| Short NASDAQ-100 Equal Weighted | ProShares Trust | 2010, 2011 | as above |
| UltraShort NASDAQ-100 Equal Weighted | ProShares Trust | 2010, 2011 | as above |

**Stated honestly: absence of annual-report filings is suggestive, not conclusive.**
The decisive test is the trust's N-CSR / NSAR total-net-assets schedule or a "had not
commenced operations" note, and it is an open S1 prerequisite (section 11, G-4). The
consequence of the residual is bounded: a never-launched series enters `K_t` with
`A = 0`, so misclassifying one as never-launched can only understate `K_t`, and only
by whatever assets it actually had.

### 3.3  Daily-reset Nasdaq-100 MUTUAL FUNDS - in the mechanism, not in the ETF panel

Present across the whole 2010-2026 series-file range:

| family | share classes | m | issuer |
|---|---|---|---|
| UltraNASDAQ-100 ProFund | UOPIX, UOPSX | +2 | ProFunds |
| UltraShort NASDAQ-100 ProFund | USPIX, USPSX | -2 | ProFunds |
| Short NASDAQ-100 ProFund | SOPIX, SOPSX | -1 | ProFunds |
| ProFund VP UltraNASDAQ-100 / UltraShort / Short | VA clones | +2 / -2 / -1 | ProFunds |
| NASDAQ-100 2x Strategy Fund | RYVYX, RYVLX, RYCCX | +2 | Rydex Dynamic Funds |
| Inverse NASDAQ-100 2x Strategy Fund | RYVNX, RYVTX, RYCDX | -2 | Rydex Dynamic Funds |
| Inverse NASDAQ-100 Strategy Fund | RYAIX, RYAPX, RYACX, RYALX | -1 | Rydex Series Funds |
| Rydex Variable Trust clones | VA clones | +2 / -2 / -1 | Rydex Variable Trust |

These are genuine daily-reset leveraged NDX vehicles and they rebalance. They are the
principal completeness gap (section 11, G-1). Two things about them matter and pull in
opposite directions: their daily assets are not publicly available at daily frequency
from any source found, **and** their exposure is struck against the 4pm NAV, so their
rebalancing is a close-print phenomenon rather than a pre-close one - which is an
argument for excluding them from a pre-close footprint that S1 must make explicitly
rather than assume.

### 3.4  Excluded by reset frequency - a mechanism exclusion, not an oversight

Monthly- and weekly-reset leveraged NDX vehicles are a **different mechanism** and
must not be aggregated into a daily reset footprint:

Direxion Monthly NASDAQ-100 Bull 2X (DXQLX), Bull 1.25X (DXNLX), Bull 1.75X (DXQLX),
Bear 2X (DXQSX), Bear 1.25X (DXNSX); Rydex Monthly Rebalance NASDAQ-100 2x Strategy
(RMQAX, RMQCX, RMQHX); Innovator Nasdaq-100 Monthly 2x ETF; Direxion Insurance Trust
VP NASDAQ-100 1.25X clones.

### 3.5  Post-2022 launches - outside any sample the local futures data can reach

ProShares Ultra QQQ Mega (QQUP, +2x NDXMEGA, first NAV row 2025-06-10), UltraShort QQQ
Mega (QQDN, -2x, 2025-06-10), Ultra QQQ Top 30 (QQXL, +2x NDX30P, 2025-08-13),
UltraShort QQQ Top 30 (QQXS), Short QQQ Top 30 (QQD), Ultra QQQ Equal Weight (EQQQ,
+2x NDXE, 2026-07-21), ProShares QuadPro QQQ, ProShares Daily Target 3x Mega QQQ,
Daily Target 3x QQQ Equal Weight; Direxion Daily QQQ Bull 4X; GraniteShares 4x Short
QQQ Daily; Defiance / Themes / Tidal structured NDX products.

Recorded for two reasons. First, they make the universe genuinely time-varying going
forward. Second, they introduce **benchmark heterogeneity** (NDXMEGA, NDX30P, NDXE
alongside NDX), which is the one structural change that would break the exact
factorization in section 2 - see section 9.

### 3.6  Non-US-listed and non-NDX vehicles - named, unpriced, undecided

Leveraged NDX products listed outside the US (for example Canadian and European
daily-reset NDX ETFs/ETPs) and non-NDX leveraged ETFs whose hedges land in
NDX-correlated names (technology, semiconductor, FANG-type baskets, and single-stock
leveraged products on NDX mega-caps) both transmit into NQ through the same
index-arbitrage channel. Their inclusion is a **scope decision for Aaron** (OD-2),
not a feasibility fact, and it is the decision that moves this report between
classification B and classification C.

---

## 4. LOCAL_DATA_AUDIT

Full detail in `R2_DATA_SOURCE_AUDIT.md` Part A. Result:

```
LOCAL COVERAGE OF R2'S FUND SIDE     =  ZERO
LOCAL COVERAGE OF R2'S FUTURES SIDE  =  PARTIAL, AND NOT GRANTED TO R2
```

| source | fields | coverage | PIT safe | identity safe | missingness | limitation |
|---|---|---|---|---|---|---|
| Databento GLBX.MDP3 NQ ohlcv-1m (`GLBX-20260727-DL3BEBCHJA`) | ts_event, o/h/l/c, volume | 2010-06-06 -> 2022-01-01 excl, 139 files | YES intraday | PARTIAL - `NQ.v.0` continuous stitch, vendor roll | not re-measured; every file SHA-256-pinned | **no R2 grant**; ends 2022-01; already carries ITSF S0-T001 and R1 trials |
| Databento NQ bbo-1s (`GLBX-20260727-TV3MXWNMXD`) | bbo-1s | 2025-01..2025-03 | n/a | n/a | n/a | three months, no R2 grant, irrelevant to the fund side |
| yfinance multi-asset ETF panel | Date + daily close | ~2008-05 -> 2026-06 | n/a | n/a | n/a | **no leveraged or inverse ETF present**; no AUM/NAV/shares/leverage/benchmark; survivor-selected ticker list |
| `trade log/` HistData | FX/metals/WTI M1 | 2015-2025 | n/a | n/a | n/a | wrong asset class |
| other project caches | BTC, order flow, commodity carry, FX pickles | various | n/a | n/a | n/a | none carry fund reference data |
| `{HYG,LQD}_nav_daily.csv` | NAV | daily | n/a | n/a | n/a | credit ETFs, no assets field |
| KB dataset registry | 5 dataset entries | - | - | - | - | none is an ETF-reference or fund-flow dataset |

No alpha, P&L, return or outcome quantity was computed against any of these.

---

## 5. PUBLIC_DATA_AUDIT

Full detail in `R2_DATA_SOURCE_AUDIT.md` Part B. The audit keeps
`CURRENT PAGE AVAILABLE` strictly separate from
`HISTORICAL POINT-IN-TIME DATA AVAILABLE`.

### 5.1  The primary finding

**ProShares publishes, free and without authentication, a per-fund daily history file
containing Assets Under Management from fund inception, and it serves closed funds.**

```
https://accounts.profunds.com/etfdata/ByFund/<TICKER>-historical_nav.csv

columns: Date, ProShares Name, Ticker, NAV, Prior NAV, NAV Change (%),
         NAV Change ($), Shares Outstanding (000), Assets Under Management
```

Retrieved and QA'd for all five NDX funds: **20,616 rows, zero missing NAV, zero
missing shares, zero missing AUM, zero duplicate dates**, and weekday gaps of
189-190 over twenty years (~9.4/yr, the NYSE holiday count) so no trading day is
absent. Survivorship verified independently: the liquidated OILU and OILD return
their full 761-row histories, DDG returns 3,510 rows from 2008.

Two measured caveats, both material and both recorded rather than smoothed over:

1. **NAV and Shares Outstanding are retroactively split-adjusted and are not
   point-in-time per-share values.** TQQQ's inception row reads NAV $0.2083 with
   38,400,380 shares against an actual inception NAV near $25. For the reverse-split-
   heavy inverse funds the share column is corrupted by rounding: SQQQ 2010-09-02
   shows NAV $9,212,800/share and "Shares Outstanding (000)" = 10, and 140 SQQQ rows
   round to zero shares. Reconstructing AUM as NAV x shares therefore disagrees with
   the published AUM on **2971/4176 SQQQ rows (max relative error 1.00)** and
   **4065/5078 QID rows (max 0.040)**, while agreeing to 1e-7 on TQQQ, QLD and PSQ.
   **Rule for R2: use the published AUM column; never reconstruct it from NAV x
   shares.** The product is split-invariant; the factors are not.
2. **Publication timing is bounded but not pinned.** At 15:58 ET on Thu 2026-09-17
   the latest row in every file was Wed 2026-09-16 - day `t`'s own row absent, so no
   same-day contamination, and `A_{t-1}` present by 15:58 ET on `t`. One snapshot
   bounds publication at <= 15:58 ET on `t`; it does not prove <= 15:30. Closing this
   costs a timestamped poll over ~10 business days and is an S1 prerequisite (G-3).

### 5.2  The rest of the public picture

| source | what it gives | historical PIT? |
|---|---|---|
| SEC series/class annual files (15 vintages 2010-2026, gaps 2016 & 2024) | Series ID, series name, entity, class ticker - the **survivorship-aware universe** | YES at annual resolution. Ticker field empty 2010-2015, so a blank ticker is not evidence of non-launch |
| SEC EDGAR filings + full-text search | **leverage multiple and benchmark from the prospectus in force**, launch, closure, mandate change | **YES - the strongest PIT property in the audit**, because the filing date proves when the statement was public. Extraction is prose-reading labour, not a query |
| SEC Form N-PORT | fund-level net assets | NO as a primary input: monthly granularity, filed in arrears, starts 2019-10. Useful as an independent cross-check for 2019-2022 and to bound the mutual-fund sleeve |
| N-CSR / N-CSRS / N-CEN / NSAR-B | fund assets for the mutual-fund sleeve | semi-annual pre-2018, annual thereafter. Bounding only |
| proshares.com fund pages | current NAV/net assets, **leverage objective, benchmark, inception** | reference only; history comes from 5.1 |
| direxion.com fund pages | current snapshot only. Verified in-browser: no downloadable historical NAV/assets/shares series, no ProShares-style history CSV. Carries reverse-split announcements (a free corporate-action source). Returns HTTP 403 to non-browser clients | NO |
| Yahoo / Investing / etfdb / ycharts / firstratedata | current net assets, price history | NO - **these are the "current page" trap and may not be cited as historical evidence** |
| Nasdaq Fund Network (NFN/MFQS) | spec confirms **Total Net Assets** and **Total Shares Outstanding** as daily disseminated fields | **UNVERIFIED** for historical archive, for ETF coverage, and the shares field is optional so issuer missingness is possible. `CANDIDATE_UNVERIFIED` - do not plan on it |
| `accounts.profunds.com` for mutual funds | nothing - UOPIX, USPIX, SOPIX all 404 | endpoint is ETF-only |

---

## 6. PAID_DATA_OPTIONS

Full detail in `R2_DATA_SOURCE_AUDIT.md` Part C. **No purchase is authorized and none
was made.** No field is claimed for a vendor without documentation or a published
data section behind it.

| vendor | product | fields expected | evidence | depth | PIT character | access | cost | confidence it satisfies R2 |
|---|---|---|---|---|---|---|---|---|
| **ETF Global** | ETF reference / fund analytics (Nasdaq Data Link ETFC is the holdings product) | leverage amount, benchmark index, **AUM at DAILY frequency** | Mathis & Moerke data section verbatim: leverage amount, benchmark index and daily-frequency AUM for all US-equity leveraged ETFs; their sample 2012-2020, ~72 LETFs, 24 benchmarks | >= 2012-2020 demonstrated; exact start unverified | sourced from sponsors/custodians/administrators, T+1; vintage behaviour unverified | Nasdaq Data Link or direct licence | not public | **HIGH for the broad multi-issuer scope. REDUNDANT for NDX-only**, which 5.1 covers free |
| **Morningstar Direct** | Morningstar Direct seat | total net assets, NAV, shares outstanding, category | Tuzun data section verbatim, sample from 2006-06-19 | back to the first US equity LETF (2006) | daily use demonstrated in the paper; field frequency unverified from vendor docs | institutional seat | not public | MEDIUM-HIGH. **Does not supply the mandate** - Tuzun read leverage and target index from prospectuses, i.e. the same EDGAR route |
| **CRSP Survivor-Bias-Free US MF DB** (WRDS) | CRSP MFDB | verified field names: `daily_nav.dnav`, `monthly_nav.mnav`, **`monthly_tna.mtna` (MONTHLY, month-end, "Begins December 1961")**, returns, fees, holdings | CRSP_MFDB_Guide.pdf, retrieved and parsed | 1962-2008 start by item; >64k funds, >31k delisted retained | survivor-bias-free by design; **no daily TNA, no daily shares table**; quarterly update, monthly lag | WRDS | subscription | **LOW as primary** (monthly cannot drive a daily footprint). **HIGH as the survivorship/gap-bounding cross-check** and the best route to the mutual-fund sleeve. ETF coverage inside the MF database unverified |
| Bloomberg / FactSet / LSEG-Refinitiv | - | - | **NOT VERIFIED. No documentation or schema inspected, so no field is claimed** | - | - | - | - | **UNASSESSED** - deliberately, per the no-unverified-claims rule |
| **Databento** | GLBX.MDP3 ohlcv-1m, NQ, 2022-01-01 -> | identical schema to the archive already on disk | existing archive + job metadata | continuous from 2022-01-01 | same as the existing archive | Databento batch job, existing relationship | not quoted | HIGH for what it does: it **extends** the sample, it does not enable it |

---

## 7. POINT_IN_TIME_AND_CAUSALITY_AUDIT

`tau` denotes a candidate late-day decision time, which this report does **not**
choose.

| input | best source | `AVAILABLE_BY` | verdict |
|---|---|---|---|
| fund existence on `t` | SEC series files + EDGAR launch/closure filings | filing/effectiveness date, well before `t` | **SAFE** |
| stable identity | SEC Series ID | static | **SAFE** |
| leverage mandate `m_{i,t}` | prospectus / 485BPOS in force at `t` | filing date, before `t` | **SAFE, and PIT by construction** - the filing date proves publicity |
| benchmark identity | same filings + fund page | before `t` | **SAFE** |
| **prior-close assets `A_{i,t-1}`** | ProShares per-fund history, AUM column | observed present by 15:58 ET on `t`; day-`t` row absent | **CONDITIONALLY SAFE.** Bound is <= 15:58 ET, not <= 15:30. **G-3 must close this before S1 seals any `tau` earlier than the measured bound** |
| shares outstanding | same file | same | **DO NOT USE** as a primary path - retroactively split-adjusted and rounding-corrupted (section 5.1) |
| splits / reverse splits | issuer press releases (ProShares, Direxion "Operational Updates") | announced in advance | **SAFE**, and made moot for `A` by using the split-invariant assets column |
| distributions | issuer + EDGAR | announced in advance | **SAFE** |
| closure / liquidation | issuer announcement + EDGAR | announced in advance | **SAFE**; the run-off window is a distinct state and must be flagged |
| same-day creations/redemptions | none | **AFTER `tau`** | **CORRECTLY UNAVAILABLE** - excluded by the contract, not a defect |
| benchmark return `r_pre_t` | local Databento NQ ohlcv-1m as an NQ-basis proxy; NDX itself not held locally | by `tau` from bars timestamped <= `tau` | **SAFE mechanically, BLOCKED by authority** - no R2 grant, and the window ends 2022-01-01. Using NQ rather than NDX introduces basis that S1 must declare |
| liquidity denominator `L_t` | local NQ 1-min volume, trailing window strictly from dates `< t` | by `tau` | **SAFE mechanically, BLOCKED by authority**, same grant and window limits |
| vintage integrity of the AUM file | single current-vintage snapshot | n/a | **RESIDUAL RISK.** Restatement of a past AUM value would be invisible. Bounded by snapshotting forward from now |

### 7.1  The two causal traps, and where each bites

- **Trailing-window trap.** Any denominator, baseline or normalization computed from a
  window that includes date `t` after `tau` is look-ahead however innocuous. Fully
  avoidable here: the local 1-minute data supports strictly-prior windows.
- **Vintage trap.** The free AUM history is a current-vintage rendering, not an
  archived vintage. Recorded as residual; low materiality for a split-invariant assets
  figure, and cheaply bounded going forward.

### 7.2  The authority finding, stated plainly

The single hardest point-in-time requirement in the contract - a fund-size figure
provably knowable before a late-day decision - **is satisfiable with free data**. The
blocking problem on the futures side is **not** point-in-time integrity. It is that
R2 holds no data grant and the local window ends 2022-01-01.

---

## 8. COVERAGE_MATRIX

`PIT` = point-in-time safe. `NDX-only scope` unless stated.

| # | required field | required? | best source | available? | PIT safe? | start | end | freq | missingness / coverage | identity risk | look-ahead risk | research impact if absent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | point-in-time fund universe | **YES** | SEC series files + EDGAR | **YES** | YES (annual res.) | 2010 (files); 2006 via EDGAR | 2026 | annual + event | **gaps: 2016, 2024 files 404**; ticker blank 2010-2015 | LOW (Series ID) | LOW | F-1: `K_t` loses capital in large-move states |
| 2 | launch / commencement date | YES | EDGAR + first NAV row | **YES** | YES | 2006-06-19 | - | event | never-launched set needs N-CSR confirmation (G-4) | LOW | LOW | fund counted before it traded |
| 3 | closure / liquidation date | YES | EDGAR + issuer; endpoint serves closed funds | **YES** | YES | - | - | event | run-off window unflagged | LOW | **LOW - and this is the survivorship guard** | F-1 |
| 4 | target leverage `m_{i,t}` | **YES** | prospectus in force (EDGAR) | **YES** | **YES by construction** | 2006 | 2026 | event | prose extraction, manual | LOW | LOW | F-3: mandate assumed constant |
| 5 | benchmark identity | YES | prospectus + fund page | **YES** | YES | 2006 | 2026 | event | - | LOW | LOW | wrong `r_pre` applied; breaks factorization handling |
| 6 | reset frequency (daily vs monthly) | **YES** | prospectus / fund name | **YES** | YES | 2006 | 2026 | event | - | LOW | LOW | monthly funds wrongly aggregated - wrong mechanism |
| 7 | **prior-close assets `A_{i,t-1}`** | **YES** | ProShares per-fund AUM column | **YES, FREE, FROM INCEPTION** | **CONDITIONAL - bound 15:58 ET, G-3** | 2006-06-19 (QLD/PSQ), 2010-02-09 (TQQQ/SQQQ) | 2026-09-16 | daily | **ZERO missing over 20,616 rows; zero dup dates; no absent trading days** | LOW (AUM is split-invariant) | **LOW once G-3 closes; MEDIUM until then** | F-2: the design dies |
| 8 | shares outstanding | NO (cross-check only) | same file | present but **unusable as primary** | **NO** | - | - | daily | 140 SQQQ rows round to zero | **HIGH - retroactively split-adjusted** | **HIGH if used per-share** | none, if `A` is taken directly |
| 9 | splits / reverse splits | YES (handling) | issuer press releases | **YES** | YES | - | - | event | - | resolved by using `A` | LOW | per-share series corrupted |
| 10 | distributions | YES (handling) | issuer + EDGAR | **YES** | YES | - | - | event | - | LOW | LOW | NAV drop misread as redemption |
| 11 | mergers / ticker changes | YES (handling) | EDGAR + Series ID | **YES** | YES | - | - | event | none found in the NDX-only set | LOW | LOW | two economic objects merged |
| 12 | `r_pre_t` benchmark return to `tau` | **YES** | local Databento NQ ohlcv-1m (proxy) | **PARTIAL** | YES mechanically | 2010-06-06 | **2022-01-01 excl** | 1-min | **NO DATA 2022-2026**; **NO R2 GRANT** | MEDIUM (`NQ.v.0` continuous roll) | LOW | mechanism cannot be evaluated at all |
| 13 | NDX index itself (intraday) | optional | not local; vendor | **NO** | - | - | - | - | absent | - | - | NQ-vs-NDX basis must be declared as an assumption |
| 14 | liquidity denominator `L_t` | **YES** | local NQ 1-min volume, trailing | **PARTIAL** | YES with strictly-prior window | 2010-06-06 | 2022-01-01 excl | 1-min | same window + grant limits | MEDIUM (roll) | LOW if trailing | F-5: no economic magnitude |
| 15 | NDX constituent cash liquidity | optional | TAQ / CRSP (paid) | **NO** | - | - | - | - | absent | - | - | alternative denominator unavailable |
| 16 | mutual-fund sleeve daily assets | **YES for a complete aggregate** | none found | **NO** | - | - | - | - | **best free/paid frequency is MONTHLY (N-PORT 2019-10+, CRSP `mtna`); SEMI-ANNUAL before 2018** | LOW | LOW | **G-1: aggregate `K_t` understated, time-varyingly** |
| 17 | non-NDX correlated LETF daily assets | only under the broad scope (OD-2) | ETF Global / Morningstar Direct (paid) | **NO free route** | - | - | - | - | Direxion publishes no history | MEDIUM | LOW | **G-2: broad-scope footprint not reconstructible free** |
| 18 | non-US NDX LETF daily assets | only under the broad scope | issuer-specific, unassessed | **UNASSESSED** | - | - | - | - | - | - | - | G-2 |
| 19 | actual intraday rebalance timing | **not obtainable in principle** | - | **NO** | - | - | - | - | swap counterparty hedging is unobservable | - | - | **a declared S1 modelling assumption, never a measurement** |

---

## 9. FOOTPRINT_IDENTIFIABILITY_BEYOND_RETURN

```
FOOTPRINT_IDENTIFIABLE_BEYOND_RETURN = CONDITIONAL
```

This is a **signal-identifiability** question only. No predictive correlation, no
regression against any future return, and no NQ outcome of any kind was computed. The
measurements below use **fund data only** - the five ProShares AUM series and the
leverage multiples. No NQ file was opened.

### 9.1  Why the answer cannot be an unqualified YES

Section 2's equation factorizes exactly over a single-benchmark universe:

```
    F_t = K_t * r_pre_t        =>        sign( F_t ) == sign( r_pre_t )   ALWAYS
```

Every NDX fund shares one benchmark, so `r_pre_t` factors straight out of the
cross-sectional sum and the *direction* of the footprint is the direction of the
same-day return, by construction and with no exceptions. **The sign channel is
therefore exactly the forbidden generic rule and carries no R2 content whatsoever.**
Any R2 design that ends up trading the sign of `F_t` has trivially reduced to
"positive day -> buy late", which the task and `R2_S0_PROVENANCE.md` section 2 both
declare invalid.

### 9.2  Why the answer is not NO either - the measured modulation

All beyond-return content lives in the scalar `K_t / L_t`. Measured for
`K_t = SUM_i m_i(m_i-1) A_{i,t-1}` over the five funds:

**Window 2010-06-07 -> 2021-12-31 (matching the local NQ archive), n = 2915 days:**

```
K_t            min $6.99bn   median $17.75bn   max $161.69bn     max/min = 23.1x
daily log-change of K_t:  sd 1.65%,  p1 -4.91%,  p99 +4.72%
funds alive:   5 on every day of this window
inverse-fund share of K_t:   min 10.7%   median 44.6%   max 81.6%

composition of K_t at three dates:
  2010-06-07  K=$8.31bn   QID 68.7% | QLD 18.0% | PSQ  5.7% | SQQQ  4.3% | TQQQ  3.3%
  2016-03-21  K=$17.62bn  TQQQ 44.4% | SQQQ 27.6% | QID 12.5% | QLD 10.5% | PSQ  5.0%
  2021-12-31  K=$154.15bn TQQQ 79.0% | SQQQ 10.9% | QLD  8.4% | QID  1.1% | PSQ  0.6%
```

**Full available history 2006-06-19 -> 2026-09-16, n = 5093 days:**

```
K_t            min $0.125bn   median $18.04bn   max $302.84bn    max/min = 2431x
daily log-change of K_t:  sd 2.43%,  p1 -6.11%,  p99 +6.51%
funds alive:   2 funds on 15 days, 3 funds on 902 days, 5 funds on 4176 days
inverse-fund share of K_t:   min 8.6%   median 45.1%   max 97.4%
```

Read against the contract's `F-4` kill condition, `K_t` is emphatically **not**
degenerate. It moves 1.65% a day within the sample window, spans 23x, and its
*composition* inverts completely: the footprint was 69% driven by a `-2x` fund in
2010 and 79% by a `+3x` fund in 2021, with the inverse sleeve's weight ranging from
11% to 82%. Fund count changes from 2 to 3 to 5 across the full history, so launches
are a real source of variation too. Each of the legitimate cross-day variation
sources the task names is present and measurable: aggregate assets, launches,
changing relative weights across `+2x/+3x/-1x/-2x/-3x`, and point-in-time universe
composition. Mandate changes and benchmark heterogeneity are additionally available
from 2025-2026 via the NDXMEGA / NDX30P / NDXE funds, though outside any window the
local futures data can reach.

### 9.3  Why "CONDITIONAL" and not "YES" - the honest identification burden

Three mechanical reasons, none of which feasibility can dispose of:

1. **`K_t` is partly the index path in disguise.** `A_{i,t}` compounds at
   `m_i` times the benchmark return, so a large share of `K_t`'s *level* variation is
   mechanically generated by the cumulative benchmark path. `K_t` is `t-1`-measurable
   and therefore not a future outcome - but a low-frequency index-level proxy
   multiplied by `r_pre_t` is a *market-state-conditioned momentum signal*, which is
   not the same object as a *reset-capital* signal. S1 must separate them, and must
   pre-declare how.
2. **The clean beyond-return components are the compositional ones**, not the level.
   The inverse-share swing (11% -> 82%), the `+3x`-vs-`-2x` dominance inversion, and
   the creation/redemption flow implied by `A_{i,t} - A_{i,t-1}(1 + m_i r_t)` are
   **not** deterministic functions of the index path - they reflect investor flows,
   launches and mandate mix. These are where R2's distinct content actually lives.
3. **The denominator is a second independent channel, and it is currently
   unquantified.** `L_t` (NQ liquidity) varies for reasons unrelated to LETF capital,
   so `K_t / L_t` has more independent variation than `K_t` alone. That was not
   measured here, deliberately: quantifying it requires opening the NQ archive, over
   which R2 has no grant.

```
CONDITIONAL, precisely:  the obtainable data DO support constructing a footprint with
material variation beyond same-day return, but ONLY if the S1 design isolates the
K_t/L_t modulation from (a) sign(r_pre), (b) |r_pre|, and (c) the slow index-level
trend embedded in AUM. No S1 specification is chosen here, and choosing one is
explicitly out of scope.
```

If S1 cannot construct that separation, `F-4` fires and **R2 is parked, not replaced
by generic momentum.**

---

## 10. FEASIBILITY_CLASSIFICATION

```
R2_FEASIBILITY = B.  FEASIBLE_WITH_PUBLIC_ACQUISITION
```

**Scoped to the mechanism as R2 was framed**: the Nasdaq-100-benchmarked daily-reset
leveraged and inverse fund complex, transmitted to NQ.

Why B and not A: nothing R2 needs on the fund side exists locally. Every field has to
be collected - five history files snapshotted under provenance discipline, a
prospectus-dated mandate table read out of EDGAR documents, a survivorship-free
universe assembled from 15 annual SEC vintages with two file gaps to close, and a
publication-timing measurement run forward. That is real acquisition and
reconstruction work, and it is not yet done.

Why B and not C: **no paid licence is required.** The dominant, and by assets the
overwhelming, part of the NDX daily-reset complex is the five ProShares ETFs, and
their daily prior-close assets are free from inception, missingness-free, and
survivorship-inclusive. Leverage mandates and the point-in-time universe are free
from EDGAR with the strongest point-in-time property in the whole audit. The paid
options in section 6 are either redundant at this scope (ETF Global, Morningstar
Direct) or a bounding cross-check rather than a primary input (CRSP).

Why B and not D: the two real coverage gaps (section 11 G-1, G-2) are, respectively,
**boundable with free data** and **a consequence of a scope choice Aaron has not yet
made**. Neither is an unbounded or unknown-direction bias in the NDX-scoped
aggregate. G-1 is same-signed, modest, and measurable from free monthly and
semi-annual filings; G-2 does not affect the correctness of an NDX-defined footprint
at all.

Why B and not E: none of `F-1` through `F-5` fires at this scope. `F-1` is defeated by
the SEC series files plus a closed-fund-serving assets endpoint; `F-2` by the free
daily AUM column, subject to G-3; `F-3` by prospectus-dated mandates; `F-4` by the
measurements in section 9.2; `F-5` by the local NQ volume data, subject to the grant.

### 10.1  The classification that would apply under the alternative scope

```
IF Aaron's OD-2 scope decision is "all LETF rebalancing flow that reaches NQ"
   (adding technology / semiconductor / basket / single-stock leveraged ETFs and
   non-US-listed NDX products)
THEN  R2_FEASIBILITY = C.  FEASIBLE_WITH_PAID_DATA
```

because no free source supplies daily assets for non-ProShares issuers - Direxion
publishes no historical series, verified in-browser - and the only corroborated
multi-issuer daily-AUM-with-leverage-and-benchmark source is ETF Global. The
conditional purchase packet for that branch is section 12, OD-2.

### 10.2  What B does NOT mean

It does not mean an edge exists. It does not authorize S1. It does not authorize
reading the NQ archive. It is a statement about **data**, and only about data.

---

## 11. MATERIAL_GAPS

| id | gap | materiality | direction of error | how it closes | blocks S1? |
|---|---|---|---|---|---|
| **G-1** | daily assets for the daily-reset NDX **mutual funds** (ProFunds UOPIX/USPIX/SOPIX + VP clones; Rydex RYVYX/RYVNX/RYAIX families + VT clones) are unavailable at daily frequency from **any** source found, free or paid. Best is monthly (N-PORT 2019-10+, CRSP `mtna`) and semi-annual before 2018 | **MATERIAL but BOUNDABLE.** Their omission understates aggregate `K_t`, and understates it *more* early in the sample when ETF assets were small, so it is a slow drift rather than a random error | same-signed, one-directional (understates `K_t`) | bound the sleeve's share of `K_t` from free monthly/semi-annual filings and carry it as a pre-declared sensitivity. Note the countervailing argument: these funds strike at the 4pm NAV, so their rebalancing is a close-print rather than pre-close phenomenon, which S1 must argue explicitly rather than assume | **NO** - it is a declared sensitivity, not a blocker |
| **G-2** | daily assets for non-NDX but NDX-correlated LETFs, and for non-US-listed NDX LETFs, have no free route | **SCOPE-DEPENDENT.** Zero materiality for an NDX-defined footprint; high materiality for an "all flow reaching NQ" footprint | unknown at broad scope | Aaron's OD-2 scope decision; then either nothing, or the ETF Global / Morningstar path in section 12 | **NO** - it is an Owner scope decision |
| **G-3** | the exact publication time of the prior-close AUM row is bounded at **<= 15:58 ET on `t`**, not proven **<= 15:30 ET** | **MATERIAL to `tau`.** It sets a floor under how early a decision time can honestly claim the datum | would create look-ahead if `tau` were sealed earlier than the true publication time | timestamped poll of the five URLs over ~10 business days. Costs nothing | **YES for any `tau` earlier than the measured bound.** Must close before S1 seals `tau` |
| **G-4** | never-launched status of the Direxion NDX 3X pair, the three Rydex NDX ETFs and the three ProShares NDX Equal-Weighted series rests on **absence of annual-report filings**, which is suggestive, not conclusive | LOW and bounded: a never-launched fund enters with `A = 0`, so a misclassification can only understate `K_t` by that fund's actual assets | one-directional (understates `K_t`) | N-CSR / NSAR total-net-assets schedule or a "had not commenced operations" note, per trust | **NO** |
| **G-5** | SEC series/class annual files for **2016 and 2024** returned 404 under both published naming conventions tried | LOW - the surrounding vintages bracket any fund's lifetime to within two years instead of one | none directional | a different filename, or the EDGAR series browse | **NO** |
| **G-6** | the free AUM history is a single **current vintage**; a restatement of a past value would be invisible | LOW for a split-invariant assets figure | unknown but small | snapshot and hash forward from now; cross-check 2019-2022 against N-PORT net assets | **NO** |
| **G-7** | mandate-history table (`m_{i,t}` by prospectus date) **not yet built** - "no change found" in section 3.1 is a search result, not a certification | MEDIUM - it is contract section 2's core requirement | unknown | read the 485BPOS series per fund; it is labour, not a blocker | **NO** - but it is S1's first collection task |
| **G-8** | **no local NQ data after 2022-01-01**, and `NQ.v.0` is a vendor continuous stitch whose roll convention governs any volume denominator | MEDIUM - caps the sample and injects a vendor definition into `L_t` | none directional | Databento extension purchase (OD-3) for the window; declare the roll at S1 for the stitch | **NO** for a 2010-2022 sample |
| **G-9** | actual intraday rebalance timing, and swap-counterparty hedge timing, are **unobservable in principle** | STRUCTURAL | n/a | cannot be closed. Must be a **declared S1 modelling assumption**, never reported as a measurement | **NO**, but it must be stated in the prereg |

---

## 12. OWNER_DECISIONS_REQUIRED

Four bounded decisions. None is self-authorizable by any agent.

### OD-1  R2 data authority over the local NQ archive

```
DECISION   Does R2 receive a data grant over
           C:\Users\Aaron\quant-data\databento-archive\intraday-trend\
           development_signal\GLBX-20260727-DL3BEBCHJA  (NQ.v.0 ohlcv-1m,
           2010-06-06 -> 2022-01-01 exclusive, manifest
           d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8)?
WHY IT IS  The existing grant is explicitly "NQ Development OHLCV ... R1 only".
AN OWNER   R2 does not inherit it. Reading it without a grant would be exactly the
DECISION   self-escalation QUANT_WORKFLOW_VNEXT section 10 forbids.
CARRIES    the archive is ALSO the sample that already bears ITSF trial S0-T001 and
           R1. R2 use is a further trial on a reused sample, so this decision is
           simultaneously a TRIAL-ACCOUNTING decision. Aaron may wish to fix
           N_trials / the sample-reuse penalty in the same breath.
IF DECLINED  R2 cannot proceed to S1 at all: without `r_pre` and `L_t` the mechanism
           has no tradeable side. The fund side would remain fully reconstructible.
```

### OD-2  Footprint scope - and it is this decision that sets B vs C

```
DECISION   Is R2's footprint
             (a) NDX-BENCHMARKED daily-reset funds only, or
             (b) ALL leveraged-ETF rebalancing flow that plausibly reaches NQ
                 (technology / semiconductor / basket / single-stock leveraged ETFs,
                  and non-US-listed NDX products)?
CONSEQUENCE  (a) -> R2_FEASIBILITY = B. Free data. Proceed on OD-1 alone.
             (b) -> R2_FEASIBILITY = C. A paid licence becomes REQUIRED, because no
                 free source carries daily assets for non-ProShares issuers
                 (Direxion publishes no historical series - verified in-browser).
NOTE       (b) also BREAKS the exact factorization in section 2: multiple benchmarks
           mean `r_pre` no longer factors out, which strengthens
           beyond-return identifiability but makes the construction materially
           harder and needs index-constituent weights.
RECOMMEND  (a) for the first pass, on governance-budget grounds: it is free, it is
           the dominant mass of the NDX complex, and it answers the framed mechanism.
           (b) is a legitimate later extension, not a prerequisite.
```

### OD-3  Sample-window extension (conditional, no purchase authorized)

```
DECISION   Extend NQ coverage past 2022-01-01 via a Databento GLBX.MDP3 ohlcv-1m job?
NOT REQUIRED to answer R2 inside 2010-06-06 -> 2022-01-01.
CONSEQUENCE of declining: the sample ends 2022-01-01, which excludes the period in
           which TQQQ's assets - and therefore `K_t` - grew largest. That is a real
           limitation on external validity, and it should be disclosed rather than
           discovered later.
```

### OD-4  Conditional purchase packet, triggered only by OD-2 = (b)

```
R2_DATA_PURCHASE_DECISION  (CONDITIONAL - fires only if OD-2 = (b))

EXACT MISSING FIELDS
  daily prior-close assets under management, per fund, per date, for non-ProShares
  US-listed leveraged/inverse ETFs whose hedges land in NDX-correlated names; plus
  their point-in-time leverage multiple and benchmark index identity.

WHY PUBLIC / LOCAL ALTERNATIVES FAIL
  - Direxion, GraniteShares, Rex/T-Rex and the other issuers publish CURRENT
    snapshots only. Verified in-browser for Direxion: no historical NAV, net-assets
    or shares-outstanding download exists, and direxion.com returns HTTP 403 to
    non-browser clients.
  - N-PORT is monthly and starts 2019-10; CRSP MFDB has monthly `mtna` and no daily
    TNA table; Nasdaq NFN is CANDIDATE_UNVERIFIED for historical ETF coverage.
  - No local source contains any leveraged-ETF fund-level field whatsoever.

CANDIDATE VENDORS
  1. ETF Global - the ONLY source whose daily AUM, leverage amount and benchmark
     identity together are corroborated by a published research data section
     (Mathis & Moerke). PRIMARY candidate.
  2. Morningstar Direct - total net assets, NAV, shares outstanding, category
     (corroborated by Tuzun / Federal Reserve Board). Does NOT carry the mandate;
     leverage and target index still come from prospectuses.
  3. CRSP MFDB via WRDS - survivorship and gap-bounding cross-check, and the route
     to the G-1 mutual-fund sleeve. NOT a primary daily source.
  4. Bloomberg / FactSet / LSEG - plausible, deliberately UNASSESSED: no
     documentation was inspected, so no field is claimed.

ESTIMATED HISTORICAL COVERAGE
  ETF Global: >= 2012-2020 demonstrated; exact start unverified.
  Morningstar Direct: back to 2006-06-19, the first US equity LETF.
  CRSP: 1962-2008 start by item, monthly TNA.

EXPECTED COST
  NOT PUBLICLY LISTED for any of the four. No price is quoted, guessed or implied
  here. A quote would have to be requested.

SCIENTIFIC CONSEQUENCE OF DECLINING
  R2 remains fully answerable at the NDX-only scope (OD-2 = (a)) with free data.
  Declining forecloses only the broader "all flow reaching NQ" formulation. It is
  therefore a SCOPE cost, not a feasibility cost.

NOTHING IS PURCHASED. ANY PURCHASE REQUIRES SEPARATE AARON APPROVAL.
```

---

## 13. CREATED_ARTIFACTS

New project `Quant trade/nq-letf-rebalancing-research/`, labelled
`STAGE = S0 (DATA FEASIBILITY / PRE-S1)`:

| path | what |
|---|---|
| `PROJECT_STATE.md` | minimal state per `QUANT_WORKFLOW_VNEXT` section 9; records `DATA_GRANT = NONE`, `OUTCOME_EXPOSURE = ZERO`, two open blockers |
| `R2_S0_PROVENANCE.md` | where R2 came from; what this stage is and is not |
| `R2_MINIMUM_DATA_CONTRACT.md` | the prospective contract, written before availability was judged |
| `R2_DATA_SOURCE_AUDIT.md` | local / public / paid audit with per-source PIT, identity, missingness and limitation records |
| `R2_FEASIBILITY_REPORT.md` | this file |
| `data_probe/proshares_nav_2026-09-17/` | the five ProShares history files as retrieved, SHA-256 recorded in the audit Part D. **A feasibility probe, not a research dataset** |

**Deliberately NOT created**, because R2 has not reached S1: no
`SEALED_PREREGISTRATION`, no `TRIAL_REGISTRY`, no `RUN_STARTED`, no `PRIMARY_RESULT`,
no `OUTCOME_BUNDLE`, no exposure ledger, no reviewer packet.

**Nothing outside this new directory was modified.** The R1 project, the KB, the
workflow files and the ITSF trial registry were read only.

---

## 14. OUTCOME_BLINDNESS_AUDIT

| forbidden thing | done? | evidence |
|---|---|---|
| NQ return after a candidate decision time | **NO** | no NQ data file was decoded at any point. The `databento` decode path was never invoked |
| 15:30 -> close, 15:45 -> close, close -> next open returns | **NO** | as above; no return of any horizon was computed on any instrument |
| correlation between an ETF footprint and future NQ return | **NO** | `K_t` was computed from fund AUM and leverage multiples ONLY. `r_pre` never entered any computation |
| strategy P&L, Sharpe, hit rate | **NO** | none computed |
| event study | **NO** | none run |
| regression against a future return | **NO** | no regression of any kind was run |
| any plot with a future NQ price/return on the y-axis | **NO** | no plot was produced |
| opening the outcome portion of an existing R1-like performance file | **NO** | the R1 files read were `R1_S0_PROVENANCE.md`, the grant/trial lines of `R1_DELEGATED_OWNER_DECISIONS.md` and `R1_TRIAL_REGISTRY.md`, and the module docstring/schema constants of `r1/dev_adapter.py`. The KB finding file `finding.nq-event-diffusion.r1-*` was located by filename and **not opened** |
| final trading rule chosen | **NO** | no `tau`, exit, threshold, bucket, specification, scaling, cost rule, stop, normalization choice or hypothesis test appears anywhere. Section 7 and G-3 state only a *causal constraint* on how early `tau` may be, which the task explicitly permits |
| data purchased | **NO** | four candidate vendors described from documentation and published data sections; nothing bought, no account opened, no quote requested |
| R1 reopened | **NO** | no R1 outcome used, no R1 file modified, R1's disposition not used as a prior on R2 |
| generic momentum substituted | **NO** | section 9 states the opposite: `sign(F_t) == sign(r_pre_t)` by construction carries **no** R2 content, and if `K_t/L_t` cannot be isolated, `F-4` fires and **R2 is parked, not replaced** |
| project labelling | **DONE** | `STAGE = S0 (DATA FEASIBILITY / PRE-S1)` in `PROJECT_STATE.md`; every artifact carries the same banner |

**What market data was inspected, and only this**: file existence and counts; job
metadata (dataset, schema, symbol, start/end); `condition.json` availability flags;
manifest hashes; the declared record schema (`ts_event, open, high, low, close,
volume`) read from R1's adapter constants; and, on the fund side, the ProShares CSV
schema, row counts, date coverage, missingness and the internal `AUM` vs
`NAV x shares` consistency check. Nothing else.

---

## 15. FINAL_STATE

```
PROJECT     nq-letf-rebalancing-research   (new, no duplicate lineage)
STAGE       S0 / DATA FEASIBILITY - PRE-S1
DATA GRANT  NONE
TRIALS      none opened
OUTCOME EXPOSURE  ZERO
```

R2's fund side is reconstructible from free, survivorship-inclusive, missingness-free,
point-in-time-defensible sources: daily prior-close assets from fund inception for the
five Nasdaq-100 ProShares daily-reset ETFs, prospectus-dated leverage mandates from
EDGAR, and a survivorship-aware universe from the SEC annual series files. The reset
equation is verified against two independent credible derivations. The footprint is
**not** degenerate: the capital scalar `K_t` spans 23x within the local sample window,
moves 1.65% a day, and inverts its composition from 69% `-2x`-driven to 79%
`+3x`-driven.

But the sign channel is the forbidden generic rule by construction, so R2's whole
claim to distinctness rests on isolating the `K_t/L_t` modulation from the same-day
return and from the slow index-level trend embedded in AUM. That isolation is an S1
design burden this report does not attempt and must not prejudge.

Two things stand between here and S1, and both are Aaron's: R2 has **no data grant**
over the only NQ data on this machine, and the **footprint scope** is undecided, which
is what separates a free study from a paid one.

```
R2_FEASIBILITY = B
FOOTPRINT_IDENTIFIABLE_BEYOND_RETURN = CONDITIONAL
NQ_FUTURE_OUTCOME_INSPECTED = NO
R2_PNL_COMPUTED = NO
R2_FINAL_TRADING_RULE_CHOSEN = NO
DATA_PURCHASED = NO
R1_REOPENED = NO
R2_S1_AUTHORIZED = NO
```

---

# AMENDMENT — 2026-09-19 (G-3 closed; delegated Owner rulings recorded)

**The accepted body above is unchanged.** This block is authoritative where it and
the body disagree. Evidence: `R2_G3_PUBLICATION_TIMING_REPORT.md`; standard:
`R2_G3_ACCEPTANCE_CRITERIA.md`; current state: `PROJECT_STATE.md`.

## AM-1  Delegated Owner rulings — §12 OD-1 and OD-2 are decided

```
DELEGATED_OWNER_RULING
  DELEGATED_BY = Aaron   DECIDED_BY = Fable   ACCEPTED_BY = ChatGPT

  S0 DATA FEASIBILITY = PASS / CLOSED
  OD-1  = GRANT the existing local NQ Development archive to R2 under a NEW
          R2 lineage-specific grant.   (granted; NOT exercised as of 2026-09-19)
  OD-2  = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY — QLD, QID, PSQ, TQQQ, SQQQ
  R2_S1 = NOT AUTHORIZED       R2_OUTCOME_EXPOSURE = NONE
```

Recorded as delegated-and-decided through that chain — **not** as Aaron personally
selecting each ruling. Under OD-2 the report's §10.1 branch to classification **C**
does not fire, and `R2_FEASIBILITY = B` stands. §12 OD-4's conditional purchase
packet is **dormant**: its trigger was OD-2 = (b), which did not occur.

## AM-2  §11 row G-3 — CLOSED

```
G3_STATUS        = CLOSED_PASS
AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN   (09:30 ET on trading day t)
EVIDENCE_LEVEL   = B
S1_TAU_CONSTRAINT = tau > 09:30 ET on trading day t
G3_CLOSES_DATA_TIMING_BUT_CREATES_MECHANISM_TIMING_BLOCKER = NO
```

The `<= 15:58 ET` bound in §5.1(2), §7 and §8 row 7 is superseded. The endpoint's
Apache `Last-Modified` and `FileETag MTime Size` ETag agree to the second, the ETag
size field equals `Content-Length` exactly, 65 of 238 fund files have mtimes frozen
for years (so mtime is a real write, not a nightly touch), and the files are verified
append-only. All five R2 files carried `Last-Modified = 2026-09-18 21:00:56-21:01:12
ET` with newest row `09/18/2026`. Four batch observations spanning 2020, 2022 and
2026 put the evening batch at 19:25, 20:21 and 21:00-21:01 ET on the row's own date.
The bound is stated at the next trading day's open rather than at 21:01 ET on `t-1`
because the batch time has drifted later over six years and the multi-year sample is
selected on delisting dates — the tighter bound is available to a forward poll, and
S1 may not assume it.

`tau` is **not** chosen, here or anywhere.

## AM-3  §11 row G-1 — the attenuation and close-print arguments are WITHDRAWN

Accepted reservations now govern:

1. **Post-2022 is NOT assigned to Validation / Lockbox.** Its future sample tier is
   **UNASSIGNED**. This qualifies §12 OD-3 and §11 row G-8, neither of which may be
   read as assigning a tier.
2. **Missing mutual-fund reset flow is NOT assumed to create only attenuation.**
   Status: **KNOWN MEASUREMENT OMISSION / MAGNITUDE UNKNOWN**. The body's
   "same-signed, one-directional (understates `K_t`)" and "modest" characterisations
   are withdrawn.
3. **Mutual-fund flow is NOT assumed to occur only at the close**, and not assumed
   unable to matter pre-close. The body's countervailing argument — that the 4pm NAV
   strike makes the sleeve a close-print rather than pre-close phenomenon — is
   withdrawn as an assumption.

§3.3's parallel remark carries the same withdrawal. None of these three is resolved
here; they are carried forward as open reservations.

## AM-4  §11 row G-6 — partially and favourably tested

All **20,616 overlapping rows** across the five funds are byte-identical between the
2026-09-17 probe and the 2026-09-19 retrieval; each file gained exactly the two
intervening trading days. Zero restatements over the interval tested. Risk reduced,
not eliminated.

## AM-5  New non-blocking residual G-10

The ProShares endpoint exposes an open Apache directory index and serves plain files
with no cache headers. Nothing guarantees the URL pattern, the index, or the header
semantics persist. S1 acquisition must snapshot, hash and record response headers at
collection time. Partly offset by first-party documentation of the master file
(ProShares performance-and-pricing FAQ).

## AM-6  Pre-S1 readiness

```
R2_PRE_S1_BLOCKERS_REMAINING = NONE
R2_READY_FOR_S1_DESIGN       = YES
R2_S1_AUTHORIZED             = NO
```

G-3 was the last remaining pre-S1 blocker; OD-1 and OD-2 disposed of the other two.
Readiness is not authorization — a separate S1 design authorization from Aaron /
ChatGPT is still required.

---

# Correction of record 2026-10-02 — CP-AUDIT-01 (R2-G11, R2-G03)

Appended under delegate decision D-R2-2026-10-02-01 (`DECISION_LOG.md`); findings in
`audits/2026-10-01_CP-AUDIT-01/2026-10-01_CP-AUDIT-01_R2.md` §3. The body and the 2026-09-19
amendment above are **not edited**; where they disagree with this section, this section
governs. Current state: `PROJECT_STATE.md`.

## CR-1 — AM-2 is withdrawn as a full-sample claim

AM-2's `G3_STATUS = CLOSED_PASS`, `AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN`,
`EVIDENCE_LEVEL = B` and its unqualified `S1_TAU_CONSTRAINT`, and the extension of the bound
over "the multi-year sample", are **withdrawn as claims about the sample**, in the same way
as the 2026-09-19 HOLD in `R2_G3_PUBLICATION_TIMING_REPORT.md`:

- the modern-endpoint observations (2020, 2022, 2026 batch times; header semantics) stay
  accepted as observations of the modern endpoint;
- `EVIDENCE_LEVEL = B` and the "safe period" concept are withdrawn per D-R2-2026-10-01-01:
  `HISTORICAL_DAILY_PIT_SAFE_START = NOT_ESTABLISHED`, `FULL_SAMPLE_AUM_AVAILABLE_BY = UNKNOWN`;
- `S1_TAU_CONSTRAINT` applies only to dates a verified source proves eligible under OD-6.

The 2011 and 2012 captured vintages carry no AUM column
(`data_probe/g3_historical_pit_2026-09-19`, 44/44 verified). See
`R2_G3_HISTORICAL_PIT_AMENDMENT.md`.

## CR-2 — AM-6 is withdrawn outright

`R2_PRE_S1_BLOCKERS_REMAINING = NONE` and `R2_READY_FOR_S1_DESIGN = YES` are withdrawn. G-3
was not closed for the sample; the open pre-S1 blockers are those in `PROJECT_STATE.md`
OPEN_BLOCKERS (B-3, G-11). `R2_S1_AUTHORIZED = NO` is unchanged.

## CR-3 — row count (pointer)

Every "20,616" in this report (§5.1, §8 row 7, AM-4) should read **23,616**; the §5.1
SQQQ share wording and "agreeing to 1e-7" are also corrected. Erratum and figures:
`R2_DATA_SOURCE_AUDIT.md`, correction of record 2026-10-02, C-3.
