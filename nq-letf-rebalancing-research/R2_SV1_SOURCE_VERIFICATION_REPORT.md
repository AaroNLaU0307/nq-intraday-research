# R2_SV1_SOURCE_VERIFICATION_REPORT

```
RECORD_TYPE = SOURCE_VERIFICATION_REPORT
LINEAGE     = R2
TASK        = SV-1
CREATED     = 2026-09-19
STAGE       = S0 / PRE-S1
```

---

## 1. AUTHORITY_AND_SCOPE

**Workflow authority:** `../QUANT_WORKFLOW_VNEXT.md`. SV-1 is ordinary S0 builder work —
no reviewer seat, no review packet, no hashed transport, no gate consumed.

**Read before any source judgment was made:** `QUANT_WORKFLOW_VNEXT.md` ·
`PROJECT_STATE.md` · `R2_MINIMUM_DATA_CONTRACT.md` (§3 prior-known fund size, §4 shares
and corporate actions, §6 causal timing) · `R2_DATA_SOURCE_AUDIT.md` (Parts B, C and the
2026-09-19 amendment) · `R2_FEASIBILITY_REPORT.md` (§3.1 universe, §3.2 never-launched
guard, §6 paid options) · `R2_G3_PUBLICATION_TIMING_REPORT.md` ·
`R2_G3_HISTORICAL_PIT_AMENDMENT.md` · `R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md` ·
`R2_G3_ACCEPTANCE_CRITERIA.md`.

**Governing rulings carried into this task:**
```
R2_FUND_SIZE_PATH                   = PATH_A_TRUE_PIT_DAILY
R2_STALENESS_POLICY                 = PROVEN_PUBLICATION_ONLY_ZERO_CARRY
R2_S1_AUTHORIZED                    = NO
R2_OUTCOME_EXPOSURE                 = NONE
R2_SAMPLE_EXTENSION_DECISION        = DEFERRED
POST_2022_SAMPLE_TIER               = UNASSIGNED
GENERIC_MOMENTUM_SUBSTITUTE_ALLOWED = NO
```

**No accepted OD-5 / OD-6 record exists on disk in this project.** `PROJECT_STATE.md`
still lists both as `NEXT_OWNER_DECISION`, and a workspace-wide search found no persisted
R2 OD-5/OD-6 ruling. The two rulings above were supplied in the SV-1 brief and are
treated as authoritative for this task; **persisting them is an Owner act and SV-1 has
not performed it.** Flagged in §14.

**What SV-1 is not.** Not alpha research, not S1 design, not authorization to buy data,
not authorization to contact vendors. Nothing was sent, no trial started, no account
created, no quote requested, nothing purchased. Where a source required credentials not
already granted, it is recorded `AUTHENTICATED_ACCESS_REQUIRED` and was not used.

**The question SV-1 answers.** Not "does historical AUM exist" — it does, completely, in
a free file. The question is whether an obtainable source can establish **what fund-size
value was actually available, and when**, for each historical date, for QLD/QID/PSQ/
TQQQ/SQQQ over 2010-06-06 → 2021-12-31. SV-1 does **not** build the OD-6 eligibility
table; it determines only whether a source capable of building it exists.

---

## 2. SV1_ACCEPTANCE_STANDARD

Written **before** any candidate was investigated, in
`R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md`: nine requirements R1-R9 (field identity · daily
frequency · full historical coverage · **point-in-time availability** · original vintage /
restatement · the 2016 acid test · survivorship · historical identifiers · obtainability),
four classifications, and a five-level evidence ladder E-A…E-E.

Three rules in that standard did the most work:

- **R4 is decisive.** A generic `As Of Date` is not enough; VALUE DATE and AVAILABILITY
  DATE must be distinguishable. Failing R4 caps a candidate at `PLAUSIBLE_UNVERIFIED`, or
  `REJECTED` where documentation establishes the capability is absent.
- **E-C can establish R1/R2/R3 but never R4.** Academic use of historical AUM proves the
  values are in the vendor's database *today*; it says nothing about historical
  availability. Papers narrow candidate products; they never promote a vendor.
- **E-D — marketing language — never supports any requirement.** "Point-in-time",
  "historical", "backtesting", "daily" count only when tied to the specific fund-size
  dataset.

---

## 3. CANDIDATES_INVESTIGATED

Twenty products across nine classes, including all eight the brief named:

1. Morningstar Direct
2. ETF Global — four access routes (direct, Massive REST API, Nasdaq Data Link, WRDS)
3. Bloomberg — Global ETP Flows Data Solution; and COFI Point-in-Time, separately
4. FactSet — ETF Profile & Prices API / ETF Standard DataFeed; and Fundamentals PIT
5. LSEG / Lipper — Fund Flows; and ETF Daily Holdings, separately
6. ProShares / ProFunds — published file (incumbent); and issuer archives / batch logs
7. Exchange reference-data archives — NYSE Arca EOD ETF Report; Nasdaq Fund Network
8. PCF / issuer-file archives — Ultumus / SIX (class exemplar)
9. Discovered during the audit — CRSP US Stock daily file; Internet Archive over
   ProShares CSVs; Internet Archive over etfdb.com / etf.com fund pages

A vendor is never credited for a property belonging to a different product of theirs;
Bloomberg and FactSet are therefore each assessed twice.

---

## 4. SOURCE_BY_SOURCE_FINDINGS

Full per-candidate evidence, with verbatim quotations and the exact missing facts, is in
**`R2_SV1_SOURCE_MATRIX.md` §2**. The findings that determine the outcome:

**ETF Global's fund-flow dataset is the only candidate with a documented availability
field.** Its API defines, per record, `effective_date` — *"the date showing when the
information was accurate or valid; some issuers, such as Vanguard, release their data on
a delay, so the effective_date can be several weeks earlier than the processed_date"* —
and `processed_date` — *"the date showing when ETF Global received and processed the
data"*. Both are stored and both are queryable filters, so the archive is indexed on
availability, not only on value date. `nav` and `shares_outstanding` give fund size under
R1(b). But: *"Records date back to April 3, 2017"*; `processed_date` is a **date, not a
time**, while R2 needs resolution against a `tau > 09:30 ET`; the feed's stated one-day
reporting lag implies `processed_date = t` for a `t-1` value, which is exactly the
unresolvable case; whether a corrected row keeps its **original** stamp is undocumented;
and whether `shares_outstanding` is split-unadjusted is undocumented, which
`R2_MINIMUM_DATA_CONTRACT` §4 requires.

**LSEG Lipper Fund Flows is the only candidate that spans the whole window** —
`Data Frequency: Daily`, *"assets under management at fund and share class level"*,
covering *"mutual funds and ETFs"*, with *"daily flow history available from August 1,
2012 for non-US funds and from 1992 for US funds"*, keyed on Lipper IDs plus ISIN, SEDOL
and CUSIP. It carries **no documented vintage, revision or receipt semantics whatsoever**.
This corrects the brief's LSEG lead: the late-starting coverage belongs to *ETF Daily
Holdings*, a different product.

**Bloomberg's ETP flows product advertises "revisions" back to 2007** — *"History includes
a comprehensive overview of historical flows and revisions dating back to 2007, enabling
clients to adjust analyses… reconstruct market conditions, and backtest models"* — but
never says whether a revision record is a **dated chain of successive values** or a
**corrected series with a note**. Only the first is point-in-time. And the brief's warning
holds exactly: Bloomberg's genuine, documented PIT product covers **85,000 companies** and
explicitly not funds.

**Ultumus / SIX proves the product class exists — and that it does not reach back.**
Verbatim: *"Achieve absolute point-in-time accuracy with complete version control and a
comprehensive 5-year historical lookback where every data point is fully traceable back to
its source file"*, alongside *"full version control and historical tracking of all ETF
provider file re-issues"* and retained *"raw, primary source ETF issuer files"*. That is
R4 satisfied at documentary level — over a **rolling** window reaching ~2021-09.

**Two candidates were killed by inspecting the schema rather than the description.** The
NYSE Arca EOD ETF Report is described in secondary prose as carrying "shares
outstanding… and the Net Asset Value"; its own free sample file's header carries neither,
nor any assets field — only identifiers, volumes, OHLC and 4PM quotes. And CRSP's daily
shares outstanding is *"taken directly from an annual or quarterly report… supplemented
with imputed shares observations"* — structurally unable to track daily
creation/redemption.

**A second, independent defeat for the whole exchange class: R2's universe straddles two
listing venues.** From the official Nasdaq symbol directory — `PSQ|…|P`, `QID|…|P`,
`QLD|…|P`, `SQQQ|…|Q`, `TQQQ|…|Q`. QLD, QID and PSQ are NYSE Arca; TQQQ and SQQQ are
Nasdaq. No single listing-venue product covers more than 3 of 5, and OD-6 forbids a
partial-universe `K_t`.

**The Internet Archive is back online** (`R2_DATA_SOURCE_AUDIT` A-6 recorded it offline
earlier on 2026-09-19). Re-tested: ProShares per-fund CSVs 2014-2019 have **zero**
status-200 captures for QLD, QID, PSQ and SQQQ, and two for TQQQ. Third-party aggregator
pages do carry an AUM figure but at 2-4% of trading days, with no as-of date and 0.1M
rounding. Useful as an audit instrument; not a source.

---

## 5. SOURCE_MATRIX

`R2_SV1_SOURCE_MATRIX.md` — twenty rows, fourteen columns, plus per-candidate decisive
evidence and missing facts, and the structural reading in its §3.

---

## 6. 2016_ACID_TEST_RESULTS

**The question.** Not "what was AUM on 2016-04-01" — every complete historical file
answers that. It is: *when did the 2016-04-01 fund-size value become available, for each
of the five funds?* On 2016-04-04 at 00:19:39 ET the published files' newest row was still
2016-03-31; the 04/01 row was back-filled at least ~2.5 days late.

| candidate | 2016_ACID_TEST | basis |
|---|---|---|
| ProShares published file | **FAIL** | current file preserves no per-row publication record |
| Internet Archive over ProShares CSVs | **FAIL** | re-tested today — no target-fund captures in the era |
| Internet Archive over aggregator pages | **FAIL** | TQQQ's 2016 captures are 03-18, 04-16, 04-21, 10-18, 12-11 — none inside 03-31→04-05 |
| ETF Global (Massive / Nasdaq Data Link) | **FAIL** | history begins 2017-04-03, after the test date |
| Ultumus / SIX | **FAIL** | 5-year rolling lookback excludes 2016 |
| NYSE Arca EOD ETF Report | **FAIL** | no fund-size field in the schema |
| Bloomberg COFI PIT · FactSet Fundamentals PIT | **FAIL** | company universes, no funds |
| CRSP (both databases) | **FAIL** | monthly TNA; reported-and-imputed shares |
| LSEG Lipper ETF Daily Holdings | **FAIL** | holdings, not fund size |
| **ETF Global (direct licence)** | **UNKNOWN** | pre-2017 depth and stamp authenticity undocumented |
| **LSEG Lipper Fund Flows** | **UNKNOWN** | covers the date; no documented availability semantics |
| **Bloomberg Global ETP Flows** | **UNKNOWN** | "revisions" to 2007; record contents undefined |
| **Morningstar Direct** | **UNKNOWN** | daily net-assets depth and restatement policy undocumented |
| **FactSet ETF Standard DataFeed** | **UNKNOWN** | institutional feed not publicly documented |
| **Nasdaq Fund Network** | **UNKNOWN** | carried from `R2_DATA_SOURCE_AUDIT` B-7 |
| **ProShares issuer archive / batch logs** | **UNKNOWN** | **the only party that can answer definitively — the stall was theirs** |

```
2016_ACID_TEST_PASS_COUNT = 0
```

No candidate passes. `PASS` requires actual source-capability evidence and was never
inferred from data completeness or from the value's existence.

---

## 7. VERIFIED_SOURCE_RESULT

```
SV1_RESULT = NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED
```

No candidate reaches `VERIFIED_FULL`. No candidate reaches `VERIFIED_PARTIAL` either —
including ETF Global, which came closest. Under §2 of the standard, `VERIFIED_PARTIAL`
requires the **same** evidence standard met with shorter scope; ETF Global's R4 mechanism
is documented at E-A, but R1 (split treatment), R3 (five-fund coverage), R5 (whether a
corrected row keeps its original stamp) and the date-versus-time granularity of
`processed_date` are all unestablished. Promoting it would be the "overall impression"
the standard forbids.

**This does not mean no source exists.** It means public evidence was insufficient to
verify one. Six vendors hold the answers and have not been asked.

**What is now settled negatively, and will not need reopening:** the incumbent free
ProShares file as a PIT source · the Internet Archive as a daily source, on either route ·
single-listing-venue exchange reference data, on two independent grounds · CRSP on both
databases · the two genuine PIT products (Bloomberg COFI, FactSet Fundamentals PIT), which
are company-universe products · Ultumus/SIX for the 2010-2021 era.

---

## 8. PLAUSIBLE_UNVERIFIED_SOURCES

Six, each with its exact missing facts and its enquiry drafted:

| candidate | what is established | what is missing |
|---|---|---|
| **ETF Global** (direct; Massive; NDL; WRDS) | E-A: daily `nav` + `shares_outstanding`, and a stored, queryable `processed_date` = receipt date. History 2017-04-03 in redistributed form; 2012-2020 daily AUM in academic use | original-stamp retention on correction · date-vs-time granularity · split-unadjusted shares · five-fund coverage · **whether pre-2017 rows are genuine or backfilled** (firm founded 2011; WRDS shows a 1993 start) |
| **LSEG Lipper Fund Flows** | E-A: daily; AUM at fund and share-class level; US history from 1992; ETFs covered; ISIN/SEDOL/CUSIP | **all** vintage, revision and receipt semantics · whether the daily *AUM* series (not just flows) reaches 1992 for these five funds |
| **Bloomberg Global ETP Flows** | E-B: "flows and revisions dating back to 2007"; flows from NAV and shares-outstanding changes | what a revision record contains · whether the 2007-2025 history is a retained archive or a 2025 reconstruction · whether NAV and shares are stored separately |
| **Morningstar Direct** | E-A: `Net Assets – Share Class (Daily)` and `Fund Size (Surveyed-Daily)` exist under Historical Cash Flow Data | history depth of the daily variant · five-fund coverage · restatement policy · any availability stamp (`Net Assets Date` is a VALUE date) |
| **FactSet ETF Standard DataFeed** | public API has historical NAV and period flow aggregates | whether the institutional feed carries daily total net assets or daily shares outstanding at all |
| **Nasdaq Fund Network** | spec defines Total Net Assets and Total Shares Outstanding (Cat F Type J) | historical archive existence · ETF coverage of those fields · the TNA message is marked "As of TBD 2027" (carried from B-7) |

---

## 9. VENDOR_ENQUIRY_PACKET_STATUS

```
R2_SV1_VENDOR_ENQUIRY_PACKET.md  = CREATED
STATUS                           = PREPARED, NOT SENT, NOT AUTHORIZED TO SEND
VENDORS                          = 6, priority-ordered
```

Carries the nine standard questions plus vendor-specific additions, a binding disclosure
boundary (use case described only as *"historical point-in-time ETF fund-size research"*;
no mechanism, no hypothesis, no NQ side, no timing parameter), and a table of what each
possible answer would do to R2's state. Sending any of it is an Aaron decision.

---

## 10. ACQUISITION_DECISION_READINESS

```
R2_ACQUISITION_DECISION_READY = NO
R2_VENDOR_ENQUIRY_REQUIRED    = YES
R2_PATH_C_PARK_TRIGGER        = NO
```

No product can be named for purchase, because for every one of them the decisive property
is unestablished. Buying LSEG Lipper on its coverage, or ETF Global on its
`processed_date` field, would be buying on exactly the untested assumption OD-6 exists to
forbid.

**PARK is not triggered.** The trigger requires all credible candidates REJECTED with no
plausible candidate remaining; six plausible candidates remain, unasked. **R2 state has
not been changed to PARKED.**

**The realistic ceiling, stated plainly.** Even the best plausible outcome is unlikely to
reach 2010-06-06. ETF Global's documented history begins 2017-04-03; Ultumus retains ~5
years; the one candidate reaching 1992 has no vintage semantics at all; and G-3 already
established the AUM field did not exist in the published artifact before ~2013. If the
enquiries succeed, the likely shape is `VERIFIED_PARTIAL` with a PIT coverage start well
inside the sample — which makes **OD-5 (sample boundary) unavoidable**, and it is Aaron's.

---

## 11. FORWARD_PIT_COLLECTION_OPTION

```
FORWARD_PIT_COLLECTION_RECOMMENDATION = YES
STATUS                                = RECOMMENDED, NOT STARTED
```

**Rationale.**

1. **SV-1 found the reason the 2010-2021 problem is hard, and it is a retention problem,
   not a data problem.** The one vendor class that keeps genuine ETF fund-size vintages
   keeps them about five years, because the need it serves is operational, not historical.
   Deep vintages are not sold because nobody kept them. The only way to have a deep
   vintage archive later is to begin one now.
2. **It costs almost nothing** — five files plus response headers per trading day, against
   an endpoint already characterised in `R2_G3_PUBLICATION_TIMING_REPORT.md` as returning
   a meaningful `Last-Modified` and a `FileETag MTime Size` ETag whose size component
   equals `Content-Length` and whose decoded mtime matches `Last-Modified` to the second.
3. **It produces exactly the evidence R2 lacks**, as
   `DIRECT_CONTEMPORANEOUS_PIT_CAPTURE_EVIDENCE` rather than archival inference: a
   contemporaneous record of when each row appeared, including any repeat of the
   2016-04-01 stall, which G-11 says can recur and which cannot be detected retrospectively.
4. **It retires backlog item G-10** — endpoint stability — by snapshotting and hashing at
   collection time, which the existing record already says to do.
5. It is **free** and needs no vendor, no licence and no Owner data-access decision beyond
   starting it.

**What it explicitly does not do:** it does **not** repair 2010-2021; it does **not**
assign post-2022 to Development, Validation or Lockbox (`POST_2022_SAMPLE_TIER` stays
`UNASSIGNED`); it does **not** change any sample boundary; and it creates no research
claim. It is evidence infrastructure for future dates only.

**Not started.** No collector was written or run.

---

## 12. UPDATED_ARTIFACTS

| file | status |
|---|---|
| `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md` | **created** — written before any candidate was judged |
| `R2_SV1_SOURCE_MATRIX.md` | **created** — 20 candidates, evidence and missing facts |
| `R2_SV1_SOURCE_VERIFICATION_REPORT.md` | **created** — this file |
| `R2_SV1_VENDOR_ENQUIRY_PACKET.md` | **created** — prepared, not sent |
| `PROJECT_STATE.md` | **amended** — SV-1 status, source classifications, remaining blocker only |

No S1 artifact was created. No sample boundary was changed. No existing R2 record was
rewritten — the two corrections SV-1 produced (the LSEG lead, and Internet Archive
availability) are recorded here as new findings, not as edits to the documents that
carried the earlier statements.

---

## 13. OUTCOME_BLINDNESS_AUDIT

```
NQ_DATA_DECODED                = NO      NQ_PRICES_INSPECTED        = NO
NQ_RETURN_COMPUTED             = NO      L_t CONSTRUCTED            = NO
K_t TESTED                     = NO      CORRELATION_TESTED         = NO
R2_PNL_COMPUTED                = NO      SHARPE_COMPUTED            = NO
TAU_CHOSEN                     = NO      ENTRY/EXIT/THRESHOLD_CHOSEN= NO
COST_MODEL_CHOSEN              = NO      REGRESSION_CHOSEN          = NO
PREREGISTRATION_CREATED        = NO      TRIAL_REGISTRY_CREATED     = NO
TRIAL_CONSUMED                 = NO      R2_S1_AUTHORIZED           = NO
PREDICTIVE_RELATIONSHIP_TESTED = NO      VOLUME/LIQUIDITY_STAT      = NO
```

The OD-1 grant over the local NQ Development archive exists and was **not exercised**; no
file in it was opened. Everything inspected was vendor product documentation, API
schemas, a free exchange sample file, the official Nasdaq symbol directory, two
Morningstar PDFs, Internet Archive CDX indexes and one archived third-party fund page, and
the existing local R2 records.

**One ordering note, for the record.** No fund-size value, level or series was read,
compared or ranked in reaching any classification here. The `AUM: $1,328.1 M` figure
quoted in the matrix is quoted to demonstrate that the field exists on an archived page
and is unusable for R2 — it is a source-property observation, not a measurement, and no
R2 quantity was derived from it.

**Sample-boundary discipline, restated.** SV-1 assessed sources only. Where a candidate's
coverage begins later than 2010-06-06, that is recorded as a source property and referred
to OD-5. No period was preferred, and nothing about R2's signal was consulted in
assessing any source.

---

## 14. FINAL_STATE

**R2 remains PRE-S1 with an open material blocker.** B-3 stands; SV-1 has not closed it,
and was not empowered to. What SV-1 changes is that the blocker is now **bounded and
actionable**: the retrospective candidate set is mapped, most of it is closed negatively
on documentary evidence, and what remains is six specific questions to six specific
vendors, already drafted.

**Three findings Aaron should carry forward:**

1. **The industry built point-in-time for company fundamentals, not for fund size.** Both
   genuine PIT products found (Bloomberg COFI, FactSet Fundamentals PIT) are
   company-universe products. Vendor PIT reputation does not transfer to ETP AUM, and the
   task's warning about Bloomberg was exactly right.
2. **Deep history and availability evidence are inversely distributed.** Lipper reaches
   1992 with no vintage semantics; ETF Global documents an availability field from
   2017-04-03; Ultumus documents true vintages over a rolling five years. Nothing found
   has both.
3. **Vendors younger than the sample must have backfilled it.** ETF Global was founded in
   2011 and WRDS lists its fund-flow coverage from 1993-01-25; Bloomberg announced
   2007-onward history in December 2025. A reconstructed row cannot carry an authentic
   availability stamp, and enquiry questions E4 and B3 exist to force that distinction.

**Open items for Aaron, none taken here:**

- whether to authorize any of the six enquiries, and through which channel — ProShares
  question P3 discloses that we noticed a specific operational failure of theirs;
- whether to start the free forward PIT collection (recommended, not started);
- **OD-5 sample boundary** — unavoidable if any enquiry succeeds with a late coverage
  start, and already pending independently;
- **persisting the OD-5 / OD-6 rulings.** `R2_FUND_SIZE_PATH = PATH_A_TRUE_PIT_DAILY` and
  `R2_STALENESS_POLICY = PROVEN_PUBLICATION_ONLY_ZERO_CARRY` were supplied in the SV-1
  brief and governed this work, but **no accepted record of either exists on disk**;
  `PROJECT_STATE.md` still lists both as pending. Writing that record is an Owner act and
  SV-1 did not perform it.

```
SV1_RESULT                            = NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED
BEST_SOURCE                           = ETF Global daily fund-flow dataset
                                        (effective_date + processed_date)
BEST_SOURCE_CLASSIFICATION            = PLAUSIBLE_UNVERIFIED
R2_ACQUISITION_DECISION_READY         = NO
R2_VENDOR_ENQUIRY_REQUIRED            = YES
R2_PATH_C_PARK_TRIGGER                = NO
FORWARD_PIT_COLLECTION_RECOMMENDATION = YES
NQ_DATA_DECODED                       = NO
NQ_RETURN_COMPUTED                    = NO
R2_PNL_COMPUTED                       = NO
R2_S1_AUTHORIZED                      = NO
TRIAL_CONSUMED                        = NO
```


---

# AMENDMENT — 2026-09-20 (SV-1 accepted with bounded corrections)

```
RECORD_TYPE     = ACCEPTANCE_CORRECTION
SV1_DISPOSITION = ACCEPTED by ChatGPT with bounded corrections
APPLIES_TO      = this report and R2_SV1_SOURCE_MATRIX.md
```

**The body above is unchanged and is not to be read as though it had always been
correct.** It stands as the record of what SV-1 found on 2026-09-19. Four statements in
it are corrected below; this amendment is authoritative where it and the body disagree.
The SV-1 *result* is unchanged: `NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED`.

## C-1 — ETF Global is not "best source"

**Withdrawn:** `BEST_SOURCE = ETF Global daily fund-flow dataset` (§14 terminal block).

**Correct wording:**

```
SV1_VERIFIED_SOURCE = NONE
STRONGEST_PUBLICLY_DOCUMENTED_PIT_METADATA_CANDIDATE = ETF Global
                                                       (effective_date + processed_date)
```

This remains factually supported: ETF Global is the only candidate whose **public
documentation** defines a stored, queryable availability field. That is a statement about
*what is publicly documented*, not about what the vendors actually hold. Bloomberg, LSEG
Lipper, Morningstar and FactSet are all `PLAUSIBLE_UNVERIFIED` and **none has been
asked**; any of them may prove superior on enquiry. ETF Global is best-documented, not
known-best, and the two must not be conflated.

## C-2 — ProShares is not the only party who can answer the 2016 acid test

**Withdrawn:** "ProShares is the only party that can answer definitively — the stall was
theirs" (§6) and the equivalent phrasing in §4 and in the enquiry packet.

**Correct principle — these are two distinct facts, and both matter:**

| fact | who can establish it |
|---|---|
| **issuer-side publication / batch facts** — when the file was written, why the batch did not run on 2016-04-01, when the row was back-filled | ProShares |
| **user-side availability** — when *its users* received the value | any vendor holding genuine historical receipt / load logs |

OD-6 asks whether the value for `t-1` was available before the decision time. A vendor's
authentic receipt log answers that for that vendor's subscribers, independently of the
issuer. ProShares is uniquely placed on the first question only.

## C-3 — OD-5 is decided and is not reopened

**Withdrawn:** "OD-5 becomes unavoidable" (§10) and "OD-5 sample boundary" as a pending
item (§14).

**Correct wording:** OD-5 is **DECIDED** — `PATH_A_TRUE_PIT_DAILY` — and persisted at
`R2_DELEGATED_OWNER_DECISIONS.md` §3. If future source verification yields only **partial**
PIT coverage, an **additional explicit S1 SAMPLE-ELIGIBILITY / SAMPLE-BOUNDARY rule will
be required under OD-5**. That rule is made *under* the decision. **Do not reopen OD-5.**

## C-4 — the PARK trigger is evidentiary, not calendar-based

**Correct rule:**

> If the bounded source-verification / enquiry process is **CLOSED** with **no qualifying
> source** and **no material candidate remaining**, then `PATH_C_PARK_TRIGGER = YES`.

A project-management deadline may exist operationally, but **it is not scientific
evidence** and cannot by itself trigger PARK. The process is currently **open**.

## C-5 — acquisition wording

**Withdrawn:** `R2_ACQUISITION_DECISION_READY = NO` as the sole formulation, which reads
as though a purchase were established to be needed.

**Correct wording:**

```
R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
PAID_PURCHASE_REQUIRED                = UNKNOWN / CONDITIONAL
```

A paid purchase is **not yet known to be required**. Enquiry answers may reveal a free or
academic route, or that no qualifying product exists at any price.

## Corrected terminal block

```
SV1_RESULT = NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED
SV1_VERIFIED_SOURCE = NONE
STRONGEST_PUBLICLY_DOCUMENTED_PIT_METADATA_CANDIDATE = ETF Global
CANDIDATE_CLASSIFICATION = PLAUSIBLE_UNVERIFIED
R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
PAID_PURCHASE_REQUIRED = UNKNOWN / CONDITIONAL
R2_VENDOR_RESPONSE_REQUIRED = YES
R2_PATH_C_PARK_TRIGGER = NO      (evidentiary trigger, see C-4)
FORWARD_PIT_COLLECTION = AUTHORIZED AND BUILT  (see R2_FORWARD_PIT_COLLECTION.md)
NQ_DATA_DECODED = NO   NQ_RETURN_COMPUTED = NO   R2_PNL_COMPUTED = NO
R2_S1_AUTHORIZED = NO  TRIAL_CONSUMED = NO
```

---

# Correction of record 2026-10-02 — CP-AUDIT-01 (R2-G14)

Appended under delegate decision D-R2-2026-10-02-01 (`DECISION_LOG.md`, COR-R2-G14);
finding in `audits/2026-10-01_CP-AUDIT-01/2026-10-01_CP-AUDIT-01_R2.md` §3. The body and the
2026-09-20 amendment are **not edited**; this section governs where they disagree.

**Nasdaq Fund Network is REJECTED under R3.** Its only documented Total Net Assets message
is marked "As of TBD 2027", so any history begins after the sample. The NFN specification
bytes were never captured; this rests on the matrix's documentary note. No enquiry is made:
no vendor contact is authorized, and NFN cannot cover 2010-2021. `R2_SV1_SOURCE_MATRIX.md`
row 18 is corrected in that file's correction section.

**The hand-copied "six" is corrected.** A parse of the matrix gives 10 PLAUSIBLE_UNVERIFIED
rows from **seven** vendors as of 2026-09-19: ETF Global, LSEG / Lipper, Bloomberg,
Morningstar, FactSet, the ProShares issuer archive / batch logs (row 2), and Nasdaq Fund
Network. Six of them were enquired in Wave-1; NFN was not.

- §7 "Six vendors hold the answers and have not been asked" — as of 2026-09-19: seven
  plausible vendors, none asked.
- §8 "Six, each with its exact missing facts and its enquiry drafted" — seven were
  plausible; the table omits the ProShares issuer archive / batch logs (enquiry drafted:
  `vendor_outbound/05_proshares.md`), and no NFN enquiry was ever drafted.
- §10 "six plausible candidates remain, unasked" — seven, unasked, as of 2026-09-19.
- §14 "six specific questions to six specific vendors, already drafted" — six enquiries
  were drafted, to six of the seven plausible vendors (NFN had none).

With NFN now REJECTED, the plausible set is six vendors, all enquired in Wave-1
(`R2_VENDOR_RESPONSE_TRACKER.md`). `R2_PATH_C_PARK_TRIGGER = NO` is unchanged.
