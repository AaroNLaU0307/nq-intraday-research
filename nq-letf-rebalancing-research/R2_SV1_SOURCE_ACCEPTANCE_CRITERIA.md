# R2_SV1_SOURCE_ACCEPTANCE_CRITERIA

```
RECORD_TYPE = SOURCE_ACCEPTANCE_STANDARD
LINEAGE     = R2
TASK        = SV-1 (source verification only)
CREATED     = 2026-09-19
STAGE       = S0 / PRE-S1.  SV-1 is NOT S1 design, NOT alpha research,
              NOT an acquisition, NOT a vendor contact.
WRITTEN     = BEFORE any candidate was investigated in this session.
```

**This file fixes the standard before the evidence exists.** It is the SV-1 analogue
of `R2_G3_ACCEPTANCE_CRITERIA.md`. Nothing below may be relaxed after a candidate is
inspected; if the standard is wrong, it is amended explicitly and the amendment is
dated, not silently reinterpreted.

---

## 0. Governing rulings this standard must serve

```
R2_FUND_SIZE_PATH               = PATH_A_TRUE_PIT_DAILY
R2_STALENESS_POLICY             = PROVEN_PUBLICATION_ONLY_ZERO_CARRY
R2_S1_AUTHORIZED                = NO
R2_OUTCOME_EXPOSURE             = NONE
R2_SAMPLE_EXTENSION_DECISION    = DEFERRED
POST_2022_SAMPLE_TIER           = UNASSIGNED
GENERIC_MOMENTUM_SUBSTITUTE_ALLOWED = NO
```

Under `PROVEN_PUBLICATION_ONLY_ZERO_CARRY`, for a future S1 decision date `t`, fund
`i` is eligible **only if the source proves the original-vintage value for `t-1` was
available before the eventual S1 decision time**. No proof => INELIGIBLE. Forbidden:
forward-fill, imputation, interpolation, neighbouring-date inference, partial-universe
`K_t`, and any assumption that publication was normal on a date not evidenced.

The consequence for source selection is the whole point of SV-1:

> A source that can tell us **what the fund size was** is not sufficient.
> R2 needs a source that can tell us **what fund-size value was actually available,
> and when**, for each historical date.

A source whose only historical claim is "the value for date D is X" — however
accurate, however daily, however deep — **cannot generate the eligibility table**
OD-6 requires, and therefore cannot on its own make R2 researchable.

---

## 1. The nine requirements

A candidate is assessed against all nine. Requirement **R4 (PIT availability)** is
decisive: failing it caps the candidate at `PLAUSIBLE_UNVERIFIED` (if unknown) or
`REJECTED` (if the vendor's own documentation establishes the capability is absent),
regardless of how well the other eight are satisfied.

### R1 — FIELD IDENTITY
Provides either
(a) daily Total Net Assets / AUM for the fund; or
(b) daily NAV **and** contemporaneous **unadjusted** shares outstanding from which
fund assets can be safely constructed.
Must be known: exact field definition · units · split treatment · restatement policy ·
original-vintage vs current-vintage semantics.
Under (b), a retroactively split-adjusted NAV or share series fails
`R2_MINIMUM_DATA_CONTRACT` §4 — `A` must be split-invariant.

### R2 — DAILY FREQUENCY
One fund-size observation per relevant trading day. Monthly, quarterly, annual or
irregular fund size does **not** qualify. Month-end TNA with a daily NAV alongside
does not qualify unless daily unadjusted shares are also present (R1(b)).

### R3 — FULL HISTORICAL COVERAGE
All five funds — QLD (from 2006-06-19), QID (2006-07-11), PSQ (2006-06-19),
TQQQ (2010-02-09), SQQQ (2010-02-09) — over their active portions of
**2010-06-06 → 2021-12-31**. All five were live for the entire window, so the window
is fully covered for every fund; pre-window launch dates matter only as identity
anchors. Missing days must be **identifiable as missing**, not silently absent.

### R4 — POINT-IN-TIME AVAILABILITY  <-- DECISIVE
The source must retain at least one of:
- **A.** original per-record publication timestamp;
- **B.** vendor receipt / load timestamp for the historical value;
- **C.** an immutable daily vintage / snapshot archive with its own dated availability;
- **D.** another auditable mechanism proving when each historical value became available.

A generic `As Of Date` / `Effective Date` / `Data Date` is **NOT** sufficient. The
standard distinguishes:

```
VALUE DATE        the date the quantity describes        (e.g. AUM as of 2016-04-01)
AVAILABILITY DATE the date/time that value became usable (e.g. loaded 2016-04-04 03:11)
```

A source carrying only VALUE DATE fails R4. A source carrying a bitemporal pair, or
dated immutable snapshots, satisfies R4 **only for the period those snapshots actually
cover** — a bitemporal product whose archive begins in year Y proves nothing before Y.

### R5 — ORIGINAL VINTAGE / RESTATEMENT SEMANTICS
Determine whether historical values: preserve originally delivered values · are
retroactively corrected · are split-adjusted · are backfilled · can be requested
"as known on date X".
**Current-vintage-only => cannot satisfy OD-6**, unless separate historical snapshots
preserve the vintage (which is R4-C and must be evidenced independently).

### R6 — 2016 ACID TEST
Any candidate reaching VERIFIED or strong PLAUSIBLE status must be assessed against
the known ProShares stalled-batch episode:

```
2016-03-31 (Thu)  batch wrote 18:25:30 ET, row present
2016-04-01 (Fri)  NORMAL NYSE TRADING DAY — batch did not run
2016-04-04 (Mon)  00:19:39 ET: published file's newest row STILL 2016-03-31
                  => the 04/01 row was back-filled >= ~2.5 days late
2016-04-05 (Tue)
```

The question is **not** "what was AUM on 2016-04-01?" — every complete historical file
answers that. The question is:

> **When did the 2016-04-01 fund-size value become available for each of the five funds?**

```
2016_ACID_TEST = PASS    source demonstrably retains the information needed to answer it
               = FAIL    source demonstrably cannot answer it
               = UNKNOWN public evidence insufficient; the vendor must be asked
```

`PASS` requires actual source-capability evidence. It may **never** be inferred from
data completeness, from vendor marketing, or from the fact that the value exists.

### R7 — SURVIVORSHIP
Must not be a current-survivor-only database. Preferably verified against known
liquidated ProShares products. Note: the five R2 targets are all live, so survivorship
does not threaten the five directly — it threatens (i) the correctness of any
universe-completeness claim and (ii) `R2_FEASIBILITY_REPORT` §3.2's never-launched
guard. It remains a requirement because a survivor-only vendor cannot be trusted to
represent the historical universe.

### R8 — HISTORICAL IDENTIFIERS
The five funds must be linkable through stable historical identifiers (CUSIP, ISIN,
FIGI, vendor permanent id), not by current ticker alone.
The leverage multiple `m_i` remains sourced from contemporaneous SEC / prospectus
records (`R2_MINIMUM_DATA_CONTRACT` §2, backlog G-7) — **no vendor's leverage field
substitutes for that**, per Tuzun's own method.

### R9 — OBTAINABILITY
The product must actually be obtainable today. Record: commercial / free · delivery
mechanism · academic availability · trial or sample availability · licensing limits
relevant to research · and whether historical PIT access is **part of the standard
product** or a **custom request**.

---

## 2. Classification rules

```
VERIFIED_FULL
  ALL of R1..R9 satisfied on documentary evidence, including R4 with an identified
  timestamp/vintage mechanism covering 2010-06-06 -> 2021-12-31 for all five funds,
  and R6 = PASS.

VERIFIED_PARTIAL
  The SAME evidence standard is met, but scope is short:
    - PIT coverage begins later than 2010-06-06, and/or ends before 2021-12-31;
    - some target funds are missing;
    - only part of the period carries genuine PIT evidence.
  MUST record exactly:  PIT_COVERAGE_START · PIT_COVERAGE_END · FUNDS_COVERED
  Partial coverage is NEVER promoted to full. A VERIFIED_PARTIAL result requires a
  later Owner sample-boundary decision (OD-5 family) before it can be used.

PLAUSIBLE_UNVERIFIED
  The vendor appears technically capable, but public documentation does not establish
  one or more decisive properties. Typical missing facts: per-date timestamp
  retention · original vintage · exact historical start · five-fund coverage ·
  daily AUM rather than monthly TNA.
  EVERY PLAUSIBLE_UNVERIFIED candidate MUST carry the exact enquiry that would
  resolve it.

REJECTED
  Public evidence establishes the candidate CANNOT satisfy R2. Examples: monthly-only
  total net assets · history begins after the sample · current-vintage only with no
  archive · no fund-size field at all · vendor confirms no historical availability
  semantics exist.
  MUST state the exact rejection reason and the requirement number it fails.
```

**No candidate may be classified VERIFIED on an overall impression.** Each VERIFIED
row cites the specific document, schema, sample or manual that establishes each
requirement.

---

## 3. Evidence strength ladder (applies to every recorded fact)

```
E-A  PRIMARY VENDOR TECHNICAL DOCUMENTATION — data dictionary, schema, field list,
     technical manual, API reference, published product specification. Names the
     product AND the field AND the property.
E-B  PRIMARY VENDOR NON-TECHNICAL MATERIAL — product page, factsheet, brochure, FAQ.
     Establishes existence, rarely semantics.
E-C  INDEPENDENT SECONDARY — academic paper data section, third-party platform
     documentation (e.g. a WRDS wrapper), reputable technical write-up.
E-D  MARKETING LANGUAGE — "point-in-time", "historical", "backtesting", "daily",
     unattached to the specific fund-size dataset.
E-E  INFERENCE / PLAUSIBILITY — no document.
```

Hard rules:
- **E-D never supports any requirement.** The words "point-in-time" and "historical"
  in isolation are not evidence; they must be tied to the exact fund-size dataset.
- **E-C can establish R1/R2/R3 but NEVER R4.** Academic use of historical AUM proves
  the values exist in the vendor's database today. It says nothing about what was
  available on the historical date. A paper is used to *narrow candidate products*,
  never to promote a vendor.
- **R4 requires E-A or E-B minimum**, and E-B only where it names the archive or the
  timestamp mechanism explicitly.
- `VERIFIED_FULL` requires E-A for R4.

---

## 4. Conduct boundaries for SV-1 (binding on this task)

**Permitted:** public documentation · public samples · product schemas · technical
manuals · academic and vendor references · existing local R2 records · publicly
accessible archived material. Preparing exact vendor enquiry questions.

**Forbidden:** sending enquiries · starting trials · creating accounts · requesting
quotes · purchasing anything · using institutional access that requires credentials or
an authenticated session not already authorized (record
`AUTHENTICATED_ACCESS_REQUIRED` instead).

**Outcome boundary:** no NQ decode, no NQ prices, no NQ returns, no `L_t`, no `K_t`
test, no correlation, no P&L, no Sharpe, no tau/entry/exit/threshold/cost/regression
choice, no preregistration, no trial registry, no trial consumption.

**SV-1 does not create the OD-6 eligibility table.** It determines only whether a
source capable of creating it exists.

## 5. Permitted SV-1 outcomes

```
SV1_RESULT = VERIFIED_FULL_SOURCE_EXISTS
           | VERIFIED_PARTIAL_SOURCE_EXISTS
           | NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED
```

`NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED` means **public evidence was insufficient to
verify one**. It does NOT mean no source exists, and it is NOT by itself a PARK
trigger. PARK is triggered only if all credible candidates are REJECTED and no
plausible candidate remains.
