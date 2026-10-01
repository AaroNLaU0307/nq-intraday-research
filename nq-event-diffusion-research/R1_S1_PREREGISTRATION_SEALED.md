# R1 — SCHEDULED-RELEASE INFORMATION-DIFFUSION CONTINUATION
## S1 DESIGN / PREREGISTRATION — **SEALED · AUTHORITATIVE · S2 NOT AUTHORIZED**

```
STATUS               = SEALED / AUTHORITATIVE
REVISION             = r4  (the ACCEPTED design, sealed unchanged. The seal
                       added status metadata and section T, nothing else.)
STAGE                = S1 SEALED
LINEAGE              = R1 (new lineage; NOT a continuation of ITSF-S0)
AUTHORED_BY          = Claude Opus 5 (Main Agent / builder seat), 2026-09-17
WORKFLOW_AUTHORITY   = QUANT_WORKFLOW_VNEXT.md (cutover 2026-09-12)
PREREG_SEALED        = YES
SEALED_BY            = Aaron (Owner)
SEAL_EXECUTED_BY     = Claude Opus (Main Agent), acting under explicit Aaron
                       authorization dated 2026-09-17
SEAL_DATE            = 2026-09-17
SEAL_IDENTITY        = R1_S1_SEAL_ATTESTATION.json (CONTENT_COMMIT + digests)
S2_AUTHORIZED        = NO
PSMV                 = COMPLETE 2026-09-17 (structural only, invariant L-13)
EXPERIMENTS_RUN      = NO
BACKTEST_RUN         = NO
R1_OUTCOME_INSPECTED = NO
```

**Operative delegated Owner ruling (2026-09-17).** `DECISION_TYPE =
DELEGATED_OWNER_RULING` · `DELEGATED_BY = Aaron` · `DECIDED_BY = Fable 5.1` ·
`ACCEPTED_BY = ChatGPT`. These are **not** Aaron personally authoring each
scientific selection, and Aaron retains override authority. Full record:
`R1_DELEGATED_OWNER_DECISIONS.md`.

```
OD-1 DATA AUTHORITY  = GRANT  (NQ Development OHLCV + frozen F10 CPI/NFP
                       calendar + derived spread-cost table; R1 only.
                       NOT Internal Validation, NOT Lockbox, NOT protected
                       ITSF outcome artifacts)
OD-2 SECOND TRIAL    = ACCEPT, separate R1 lineage / separate R1 registry
OD-3 POWER GATE      = ACCEPT  (future sealed protocol; NOT run at PSMV)
OD-4 MATERIALITY     = k = 1  ->  M = 1 x C_base_RT = $3.99 per event per MNQ
OD-5 PROJECT HOME    = OPTION A, `nq-event-diffusion-research/`
OD-6 CROSS-ASSET     = DECLINE_PURCHASE (no cross-asset covariate enters R1)
OD-7 FOMC            = CONFIRM_DEFER -> UNRESOLVED / DEFERRED, never falsified
P-2  REACTION WINDOW = OPTION A (fixed; no alternative arm, no scan)
```

**Revision r4 — bounded record repair, 2026-09-17.** The r3 PSMV execution was
reviewed: `PSMV_SCIENTIFIC_INTEGRITY = PASS`, `PSMV_AUTHORITY_COMPLIANCE = HOLD /
BOUNDED_RECORD_REPAIR`. **Every structural PSMV fact stands and nothing was
re-run.** Three changes and nothing else: (1) the deterministic MDE
recalculation that exceeded the authorized PSMV output surface is removed from
the record, the prospective *form* and its declared assumptions are preserved,
and `PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF
REQUIRED` (§S.6, §I.4, §G.3); (2) **P-7 CLOSED** by a small structured companion
manifest that validates mechanically; (3) **P-8 CLOSED** by initialising the
project as its own local git repository. No design element was reopened, no data
process was re-run, and **no new MDE was computed**.

**Revision r3 — what changed.** r2 was ACCEPTED. Aaron delegated the remaining
bounded Owner-decision packet; Fable 5.1 decided it; ChatGPT accepted the
delegated ruling (`PASS / CLOSED`). r3 writes in the operative decisions and the
**measured** S1 pre-seal structural facts. **No design element was reopened.**
One bounded clarification was forced by purity and is flagged as
`PSMV_SCOPE_CONFLICT` in §S.3: the E4 no-direction test needs price values, so
the pre-seal funnel stops at E3 and `n` is now stated as two distinct quantities.

**Revision r2 — retained for lineage.** ChatGPT returned `HOLD / BOUNDED_REPAIR`
with four material pre-seal issues. All four were repaired in r2:

```
REPAIR 1  EXECUTION CAUSALITY   Primary entry moves O(08:32) -> O(08:33).
                                The 08:32 idealised arm is DROPPED entirely.
REPAIR 2  MATERIALITY ALGEBRA   k was misinterpreted. Corrected, and OD-4 now
                                presents k=1 and k=2 as an explicit Owner choice.
REPAIR 3  CLAIM vs MECHANISM    PRIMARY_PREDICTIVE_VERDICT is separated from
                                MECHANISM_SPECIFICITY_ASSESSMENT.
REPAIR 4  STAGE ORDER           The structural preflight is reclassified from
                                S2-1 to S1 PRE-SEAL MECHANICAL VALIDATION (PSMV).
```

Nothing else was reopened. The event family, the FOMC deferral, the no-consensus
design, the fixed universe, the single primary test, the exposure disclosure, the
outcome-blind power gate, the block-bootstrap concept, the four-way negative-result
semantics, the no-cross-asset default and the no-state-programme constraint all stand
as accepted in r1. **No robustness control was added.**

**This document authorizes nothing.** It creates no data grant, no trial, no run
authority and no claim. Every number is either a mechanically measured *calendar /
cost / structural* fact (sourced inline) or a declared planning assumption, marked as
such.

**What was read, and what was not.** Read: `QUANT_WORKFLOW_VNEXT.md`, workspace
`CLAUDE.md` / `AGENTS.md` / `WORKSPACE_MAP.md`; ITSF `PROJECT_STATE.md`,
`PROJECT_CHARTER.md`, `STUDY_0_PREREGISTRATION.md` (§0–§10.2), `DATA_QA_REPORT.md`,
`DATA_QA_ADDENDUM.md`, `S0_INPUT_PREFLIGHT_REPORT.md`, `IMPLEMENTATION_RESOLUTIONS.md`
(IR-17…IR-24), `purchase_plan.yaml`, `purchase_approval.yaml`,
`gate1/f10_event_calendar/*`, `gate1/platform_params.yaml`,
`gate1/symbology/nq_v0_mapping.csv`, `spread_cost_table.csv`, `src/itsf/data/roles.py`,
`src/itsf/s0/costs.py`, `src/itsf/contracts.py` (constants), `ops/BACKLOG.md` §1–§2,
the live trial registry at `C:\Users\Aaron\quant-data\itsf-registry`,
`ops/EXPOSURE_LEDGER.md`, `ops/OUTCOME_CARRYING_ARTIFACTS.json`, and the
**cell-identity keys only** of `ops/S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl`.

**Not opened:** every file listed in `ops/OUTCOME_CARRYING_ARTIFACTS.json`, the
`S0_T001_RESULT_*` artifacts, `ops/outcome_quarantine/`, and the repo-root
`EXPOSURE_LEDGER.md`. **No market-data file was decoded. No loader was run. No
statistic was computed on any price series, in r1 or in r2.**

---

## A. AUTHORITATIVE_STATE

### A.1 CURRENT_WORKFLOW_AUTHORITY, and R1's corrected stage order

`QUANT_WORKFLOW_VNEXT.md` (workspace root, cutover 2026-09-12). Astra is **not**
mandatory at S1 (trigger-only, vNext §4); none was called for this repair, and none is
proposed. QROS / L6 / A–L stages / Review Packets / reviewer seats are **historical**
and are not revived. `qros` was not run.

**REPAIR 4 — R1's stage order, stated once and enforced throughout this document:**

```
S0 FRAME                            CLOSED (Owner decision RESEARCH)
S1 DESIGN  (this document, r4)      DONE -- and now SEALED
   |
   +-- OD-1 GRANTED                 DONE 2026-09-17 (delegated ruling)
   |
   +-- S1 PRE-SEAL MECHANICAL       DONE 2026-09-17. Structure only --
   |   VALIDATION  (PSMV)           presence/absence, timestamps, identifiers,
   |                                NA reasons, roll flags. NO prices, returns,
   |                                signs, P&L or outcome distributions.
   |                                L-13 PASS, mutation-demonstrated. (section S)
   |
   +-- structural n + availability   DONE -- written into section D.3 and S
   |   table WRITTEN INTO this prereg
   |
   +-- ChatGPT / Aaron acceptance   DONE 2026-09-17.
   |                                CHATGPT FINAL PRE-SEAL ACCEPTANCE = PASS,
   |                                MATERIAL_BLOCKERS = 0
   |
   +-- AARON SEALS                  DONE 2026-09-17  <== WE ARE HERE
   |                                the seal is the boundary, and it is crossed
   |
S2 BUILD                            NOT STARTED, NOT AUTHORIZED
S3 RUN -> S4 VERDICT -> STOP
```

In r1 the structural preflight was labelled `S2-1`. That was wrong: S2 begins only
after the seal, yet the final `n` must be **inside** the sealed text (§R.3 item 8).
The work is unchanged; its stage label and its read-surface limits are now correct.

### A.2 CURRENT_PROJECT_STATE (ITSF — the named primary project)

```
ITSF STAGE                  = STOPPED / PARKED (Aaron, 2026-09-16)
ITSF FINAL_VERDICT          = INSUFFICIENT_EVIDENCE (KB term: `unresolved`)
ITSF HEAD                   = 11725fb, branch `master`, worktree clean
ITSF DATA_GRANT             = "the existing ITSF S0 grant only. No new grant."
ITSF OPEN_MATERIAL_BLOCKERS = NONE (parked, not blocked)
ITSF REAL_MC                = NOT AUTHORIZED; MC-R001 never completed
```

ITSF holds a **SEALED** `STUDY_0_PREREGISTRATION.md` (`prereg_sha256 =
6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132`) for a *different*
question — the 09:30–10:00 opening drive, a 10:00 decision, a 15:44 exit. Under vNext
§0 that seal binds **its own** research, not R1.

### A.3 R1's own S0 record — an absence, reported rather than assumed

R1's S0 frame, the Fable/Astra rounds, the ChatGPT synthesis and Aaron's `RESEARCH`
decision have **no artifact anywhere in this workspace**. A mechanical search of every
project `*.md` returned only the unrelated CTA-EDGE / PINS / MMV programme in
`multi-asset-tsmom-research`. An absent record does not contradict the task's statement
of the S0 outcome; it is logged as **PRE_SEAL_OPEN_ITEM P-1**.

```
HANDOFF_CONFLICT = NONE
```

---

## B. DATA_AND_AUTHORITY_INVENTORY

Everything below separates **EXISTS** from **AUTHORIZED FOR R1**.

### B.1 Inventory

| item | status | evidence |
|---|---|---|
| `NQ_DATA_COVERAGE` | `NQ.v.0 ohlcv-1m`, **2010-06-06 20:00 ET → 2021-12-31 16:59 ET**, 139 monthly files, **3,848,635 bars**, every file SHA-256-verified before decode, zero decode failures. **Full Globex session — the 08:30 ET release minute and the whole 08:29–09:29 window are inside the purchased data.** | `DATA_QA_ADDENDUM.md` A1 §1–2; manifest `d8d1edc7…3ae8` |
| `EVENT_CALENDAR_AVAILABLE` | **YES** (CPI/NFP) · **PARTIAL** (FOMC) | `gate1/f10_event_calendar/f10_events.csv`, sha256 `5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c`, 468 rows × 9 cols; IR-17 `APPROVED_BY_AARON 2026-07-29` |
| `EVENT_TYPES_CURRENTLY_PRESENT` | `CPI` 139 days · `NFP` 138 days · `FOMC` 96 statement days (92 scheduled + 4 unscheduled) | measured from the CSV |
| `EXACT_EVENT_TIMESTAMPS_AVAILABLE` | **PARTIAL.** CPI 139/139 and NFP 138/138 `official_time_recorded` at `08:30`. **FOMC: 45 of the 92 scheduled statement days — all of 2010–2015 — carry no official time**; IR-17 forbids backfilling and forbids time-level use of those rows. | CSV + `DECISION_PACKET_F10_D4A_FOMC_RELEASE_TIME.md` + IR-17 |
| `CONSENSUS_AND_ACTUAL_RELEASE_VALUES_AVAILABLE` | **NO** — date, type, official time, source id, source hash only. Under this design: **NOT_NEEDED** (§C.4). | CSV header |
| `RELATED_MARKET_INTRADAY_DATA_AVAILABLE` | **Effectively none.** No ES, ZN/ZB/ZF, 6E/6J, MES or MGC at any schema (`purchase_plan.yaml` `explicitly_not_purchased_now`). Only `trade log/` HistData M1 **spot FX/metals, 2015→2025**, retail-aggregator quotes on an EST-without-DST clock. | `purchase_plan.yaml`; KB `dataset.histdata-com.fx-metals-crude.yaml` |
| `COST_MODEL_AVAILABLE` | **YES.** `spread_cost_table.csv` — per-minute-of-day ET spread median / p90 / p95 in index points across all 1,380 session minutes, from MNQ `bbo-1s` 2025-01→2025-03 (4,947,392 rows; crossed-quote fraction 0.028 %). Four frozen scenarios and signed-`d` fill formulas implemented and tested in `src/itsf/s0/costs.py`. | `DATA_QA_REPORT.md`; `DATA_QA_ADDENDUM.md` A2; `costs.py` |
| `PROP_CONSTRAINT_MODEL_AVAILABLE` | **YES.** `gate1/platform_params.yaml` v0.6 FROZEN — Topstep 50k and LucidFlex 50k, trailing MLL with **real-time unrealized-inclusive** intraday breach, optional DLL ($1,000 at 50k), consistency rules, position caps. | `platform_params.yaml`; `src/itsf/mc/platforms/` |
| **`EXECUTION_LATENCY_EVIDENCE`** | **NONE EXISTS.** `PROJECT_CHARTER.md` Gate 2 (automation-channel PoC) has never been run — *"候选均未通过任何 Gate"* — and `platform_params.yaml` carries `actual_cost_status: unconfirmed_until_gate2_poc`. **This is the mechanical basis of REPAIR 1** (§E.2). | `PROJECT_CHARTER.md` §Gate; `platform_params.yaml` `gate2_cost_guard` |

### B.2 CURRENT_DATA_AUTHORITY_FOR_NEW_R1_LINEAGE — **NOT GRANTED**

* The A1 Development purchase was approved on 2026-07-27 **for Study 0**
  (`purchase_approval.yaml`: *"仅批准 A1 … 和 A2"*); `PROJECT_CHARTER.md` clause 14
  isolates data **by role and by purpose**.
* ITSF `PROJECT_STATE.md`: `DATA_GRANT = the existing ITSF S0 grant only. No new grant.`
* vNext §10 makes access beyond an existing grant Owner-only; §12: *prior data access ≠
  future execution or reveal authority*.

**OD-1 = GRANT (delegated ruling, 2026-09-17), for R1 only**, covering the NQ
Development OHLCV, the frozen F10 CPI/NFP calendar and the derived spread-cost
table. Under that grant PSMV performed the pre-seal structural read and nothing
else. Internal Validation, the Lockbox and the protected ITSF outcome artifacts
remain **NOT GRANTED** and were **not accessed**.

Internal Validation (2022-01-01 → 2025-07-01) and the Physical Lockbox are **not
purchased and do not exist on this machine**; `DataRole.INTERNAL_VALIDATION_SIGNAL` is
deliberately absent from `ROLE_WINDOWS` so any load attempt fails closed with a named
`RoleError`. R1 inherits that boundary unchanged.

### B.3 CURRENT_EXPOSURE / TRIAL_ACCOUNTING CONSTRAINT

```
ITSF cumulative researcher_exposure_count = 1575
source                                    = ONE ledger row, 2026-08-14,
                                            classification REVEALED_TARGET_METRIC
scope                                     = the SAME NQ Development sample R1 wants
formal_trial_count on that sample         = 1  (S0-T001, exposure_seq 1, CONSUMED)
builder outcome-blindness                 = LOST 2026-08-24 (ledger row 7)
```

Measured from the **cell identities only** of `ops/S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl`
— 1,575 lines, keys `cell, engine, family, path, scenario, slice, theta`; **the file
has no value field**, and no outcome artifact was opened:

| revealed family | cells | meaning for R1 |
|---|---|---|
| `stability` | 544 | per-year / epoch / leave-one-year-out / vol-tercile / by-direction stability of the **opening-drive Oracle** |
| `frequency` | 300 | continuation-event frequency at θ = 0.3 and 0.5 |
| `bootstrap_*` | 288 | interval, seed and convergence accounting |
| `executable_pnl`, `executable_worst_day`, `e2_worst_day`, `theoretical_*` | 204 | cost-scenario P&L and worst-day cells for the 10:00 → 15:44 Oracle |
| `sizing_coverage`, `*_accounting`, `grid_*`, `oracle_universe`, `label_availability`, `sensitivity`, `direction_accounting` | 229 | structural / accounting |
| **`event_strata_counts`** | **10** | **event-day COUNTS only.** None of the 54 distinct `slice` values is an event-type conditional *performance* slice. |

**Both directions, honestly.** *For R1:* continuation performance conditioned on event
type was never revealed; every revealed object is anchored at 09:30 / 10:00 / 15:44,
and R1's `08:33 → 09:29` pre-open window **has never been an outcome on this sample**.
*Against R1:* the same 2,882-day sample already produced 1,575 revealed target cells
about intraday NQ directional continuation, and the builder seat has not been
outcome-blind since 2026-08-24. Charter clause 13 requires raw exposure to be carried
as a **conservative upper bound** into any formal multiple-testing correction. R1 may
not describe this sample as fresh. *One weak indirect exposure, disclosed:* ITSF's F6 /
F7 overnight-range features span `18:00 → 09:30` and therefore touch R1's window —
a prior about pre-open **range**, never about post-release **directional drift**.

R1 is a **second formal trial on an already-burned sample**. Legitimate under vNext §14
(a genuinely untested subspace, not a parameter tweak), and the reason §I fixes a
single primary test and states the falsifier against an economic materiality boundary
rather than against zero.

---

## C. PRIMARY_RESEARCH_CLAIM

### C.1 The claim — **predictive**, with the mechanism claim held separate (REPAIR 3)

> **R1-CLAIM (predictive).** Conditional on a **scheduled, externally calendared,
> Level-1 time-attested US macroeconomic data release** (the BLS 08:30 ET family: CPI
> and the Employment Situation), the **sign of NQ futures' own initial reaction over
> the two minutes immediately following the release instant** carries **economically
> material** predictive information for the **cost-adjusted, executable return of a
> position entered at `O(08:33)` — one full minute after the signal is complete at
> 08:32:00 ET — and closed by a pre-scheduled timed exit at `O(09:29)`, one minute
> before the cash-equity open** — where *economically material* means that the mean
> net USD result per event, per one MNQ contract, exceeds a **prospectively fixed
> multiple `k` of its own Base round-turn execution cost** (`k` set by Aaron at OD-4,
> §G.3), and where the direction traded is **continuation**, fixed in advance.

**What this claim is not.** It is a statement about **predictability**, not about
**cause**. The words *information diffusion* name the motivating mechanism; they are
not part of what the Primary test can establish. Whether the effect is *specific to
scheduled releases* — as opposed to generic matched-clock short-horizon continuation —
is decided by a **separate, non-confirmatory** assessment (§K.2, §L, §M.1), and the
verdict language in §M.2 is constructed so that a generic momentum effect can never be
silently upgraded into evidence for information diffusion.

| component | R1 definition |
|---|---|
| **EVENT** | A scheduled BLS release at 08:30 ET — CPI or Employment Situation — on the frozen, source-hashed F10 calendar with `release_time_status = official_time_recorded`; **not** coinciding with any FOMC calendar entry; **not** on an `is_roll_transition` session. |
| **INITIAL REACTION** | `R_init = C(08:31) − C(08:29)` — from the close of the last strictly pre-release 1-minute bar to the close of the second post-release bar. `d_event = sign(R_init)`. `R_init = 0` exactly → no direction; the event is excluded and counted separately (ITSF's frozen L82 convention). |
| **SIGNAL COMPLETE** | **08:32:00 ET** — the instant the 08:31 bar closes and `R_init` becomes knowable. |
| **DECISION POINT / ENTRY** | **`O(08:33)`** — the open of the 08:33 bar, giving a **full 60-second execution-latency budget** between signal completion and the booked fill. See §E.2 for why `O(08:32)` is not mechanically attainable. |
| **FUTURE RETURN OBJECT** | `Y_net` = cost-adjusted USD profit-and-loss per **one MNQ** contract of a single trade: enter `O(08:33)` in direction `d_event`, pre-scheduled timed exit at `O(09:29)`. One trade per event, **56 minutes**, never overnight, **no stop in the Primary**. |
| **EXPECTED DIRECTION** | **Continuation.** `d_event` is the traded direction; the predicted sign is **positive**, declared before any outcome exists. |
| **ECONOMIC MATERIALITY** | `mean(Y_net) ≥ M`, `M = k × C_base_RT`, `C_base_RT = $3.99` per 1 MNQ measured at R1's own entry and exit minutes (§G.2). **OD-4 ruled `k = 1`, so `M = $3.99` per event per 1 MNQ ( = 2.00 NQ index points)** — fixed before any PSMV output was interpreted, and never recomputable from data (§C.3, L-8). |

### C.2 Null, alternative, falsifier

```
H0  (PRIMARY NULL)         mean(Y_net) <= M     "no economically material
                                                 post-decision continuation"
H1  (PRIMARY ALTERNATIVE)  mean(Y_net) >  M     one-sided; sign declared in advance
```

* **Primary predictive effect supported** requires the 95 % **lower** bound of
  `mean(Y_net)` to exceed `M`, plus the guard conditions of §M.1.
* **Primary predictive effect excluded (falsified)** requires the 95 % **upper** bound
  to fall **below** `M`, **and** the realized CI half-width to be smaller than `M` —
  i.e. the design actually resolved the question rather than merely failing to reject.
* **INSUFFICIENT_EVIDENCE** is everything in between, including every case where the
  interval spans `M`.

The mapping from these to the two-part verdict (predictive × specificity) is §M.

### C.3 What would NOT count — stated in advance

Failure **may not** be reinterpreted as *"wrong window, try another."* The following
are prospectively **not** rescue paths and may not be executed under the R1 name after
a negative result:

* a different reaction window (1, 3, 5, 10 minutes) — R1 has exactly one;
* a different entry minute. **There is now exactly ONE entry time, `O(08:33)`.** The
  r1 "latency arm" is gone (it became the Primary), and **no new arm at 08:34 or
  anywhere else may be created** — that would be the entry-time scan this design
  exists to avoid;
* a different exit time, or a stop-optimised / trailing exit;
* a magnitude threshold on `|R_init|` used as an entry filter;
* re-splitting CPI and NFP and promoting whichever performed better;
* re-admitting FOMC after seeing the BLS result;
* re-running against the Internal Validation window (which does not exist on this
  machine; its access is a separate single-use Owner budget — *IV failure = hypothesis
  death* in the sealed ITSF data-role table);
* re-setting `k`. OD-4 fixed `k = 1` on 2026-09-17, before any PSMV output was
  interpreted and before any outcome exists. It may never be revisited from data.

Any of those is a **new lineage with a new preregistration and a new trial** (vNext §14).

### C.4 Why no consensus / surprise data is required — and what that costs

R1 conditions on **the market's own observed initial reaction**, not on the release
surprise. Three consequences, stated so this is not mistaken for an oversight:

1. **It removes a data dependency that does not exist here.** No consensus series is
   owned; a point-in-time-correct 2010–2021 consensus history is a purchase, a vintage
   problem and a new lineage risk.
2. **It keeps the information set strictly causal.** The reaction is observed by
   08:32:00; a revised consensus or revised print is not available as of `t`.
3. **It costs identification power, and R1 must not claim otherwise.** R1 cannot
   separate *"the market under-reacted to the number"* from *"the first move was noise
   that later mean-reverted"*. Carried into §M.3 as an explicit non-claim.

---

## D. RELEASE_UNIVERSE

*(Unchanged from r1 — not reopened. Only the E3 anchor list in §D.3 is updated for the
new entry minute.)*

### D.1 Candidate-by-candidate

| candidate | relevant to NQ? | schedule stability | timestamp quality | sample in Dev window | structural-break risk | consensus needed? | **verdict** |
|---|---|---|---|---|---|---|---|
| **CPI** (BLS) | **HIGH** — moves front-end and real-rate expectations; NQ is the longest-duration major US equity index | HIGH — monthly, 08:30 ET, scheduled a year ahead | **HIGH** — 139/139 `official_time_recorded` at `08:30` | **139** (121 after exclusion) | MEDIUM — the 2021 inflation-regime change is inside the window; a disclosed epoch, never a filter | NO | **KEEP** |
| **Employment Situation / NFP** (BLS) | **HIGH** — the other pillar of the Fed reaction function; identical transmission channel | HIGH — monthly, first Friday, 08:30 ET | **HIGH** — 138/138 `official_time_recorded` at `08:30` | **138** (137 after exclusion) | MEDIUM — same | NO | **KEEP** |
| **FOMC scheduled statement** | HIGH | HIGH (8/yr) | **LOW / PARTIAL — disqualifying.** 45 of 92 scheduled statement days (all of 2010–2015) carry no official time in any archived Fed source; IR-17 **forbids** backfilling and states that time-level diagnostics may not use those rows. | 47 usable, **all in 2016–2021** | **HIGH** — one monetary era; and the 14:30 press conference is a *second* scheduled release inside any plausible horizon | NO | **EXCLUDE from R1** |
| FOMC unscheduled actions (2019-10-11, 2020-03-03/03-15/03-23) | HIGH | **none — unscheduled** | 4/4 attested | 4 | n/a | n/a | **EXCLUDE** — R1 is about *scheduled* releases |
| PPI · retail sales · ISM · GDP · PCE · claims | plausible | high | **not in any owned calendar** | 0 | n/a | n/a | **EXCLUDE — no data** |

FOMC is recorded as **UNRESOLVED / DEFERRED for R1** — an availability decision, **not**
a negative finding about post-FOMC diffusion.

### D.2 The final release family, and why it pools

**R1 event family = {CPI, NFP}, pooled into ONE population.** Same issuer, same
08:30:00 ET clock, same pre-open session position and therefore the same event
microstructure; same duration transmission channel to NQ; the same diffusion story
stated at the level of *"a scheduled macro number"*; and measured, `CPI ∩ NFP = ∅`, so
pooling double-counts no day.

**Multiplicity consequence:** exactly **one** primary test. Event type is a descriptive
covariate (§H), never a second primary and never a promotion route. Sign disagreement
between CPI and NFP is a **reported heterogeneity finding**.

### D.3 Prespecified inclusion / exclusion — measured counts

Every exclusion is a pure function of the frozen calendar, the frozen symbology map and
pre-decision bar availability. **None may depend on any outcome.**

```
E0  CPI or NFP release day on the frozen F10 calendar            277   MEASURED
E1  minus days carrying ANY FOMC calendar entry                  -19   MEASURED
      (9 of the 19 are same-day statement days, i.e. a second
       scheduled release later the same session)
                                                                 258
E2  minus EXACT is_roll_transition sessions                       -0   MEASURED (PSMV-2)
    ------------------------------------------------------------------
    R1 EVENT UNIVERSE, pre-availability                          258   CPI 121 · NFP 137
E3  minus events missing any required structural anchor
      C(08:29), C(08:31), O(08:33), O(09:29), ADR14 availability  -6   MEASURED (PSMV-1)
    ==================================================================
    PRE_SEAL_STRUCTURAL_N                                        252   CPI 118 · NFP 134
E4  minus R_init == 0 exactly (no direction)              DEFERRED TO S2
      R_init == 0 is a comparison of two bar CLOSE PRICES. Establishing it
      pre-seal would require inspecting market values, which invariant L-13
      forbids. The pre-seal funnel therefore stops at E3 -- the deepest point
      decidable structurally. See section S.3 and section 6 below.
```

*Note on E2 — resolved.* The r2 figure was an approximation. PSMV recomputed it
with ITSF's own frozen `_roll_map` logic (`bisect_left` over the observed-RTH
day list, then the official-interval containment assertion): **47 intervals → 47
transitions → 47 distinct transition sessions, all inside their official
intervals, and EXACTLY ZERO coincide with a CPI or NFP release.** The
approximation was right, and is now measured. `is_roll_window` covers 235
sessions and remains a **disclosed flag**, not an exclusion.

*Note on E3 — what the six removals actually are.* Five of the six are **Good
Friday**, and they split into two structurally different cases (full detail,
timestamps only, in `artifacts/PSMV_STRUCTURAL_REPORT.json`):

| date | type | what PSMV measured | reason code |
|---|---|---|---|
| 2010-06-17 | CPI | full session, but only **8** complete-390 RTH days precede it | `adr14_warmup_insufficient_prior_complete_days` |
| 2012-04-06 | NFP | Good Friday. Abbreviated CME session, **last bar 09:14 ET** — entry anchors exist, the 09:29 exit anchor does not | `anchor_missing_O_0929` |
| 2015-04-03 | NFP | Good Friday, abbreviated session, last bar 09:14 ET | `anchor_missing_O_0929` |
| 2017-04-14 | CPI | Good Friday. **Not a scheduled CME_Equity session; zero bars on the date** | `no_bars_on_date` |
| 2020-04-10 | CPI | Good Friday, not scheduled, zero bars | `no_bars_on_date` |
| 2021-04-02 | NFP | Good Friday, abbreviated session, last bar 09:14 ET | `anchor_missing_O_0929` |

The three abbreviated-session NFP days are a genuine **execution-feasibility**
finding, not a data defect: on a Good Friday with a payrolls release, CME runs a
shortened equity-futures session that **closes at 09:15 ET**, so R1's trade is
enterable but not exitable as specified. The prespecified anchor rule removes
them without any special case, and no price was read to discover it.

**Balance at `PRE_SEAL_STRUCTURAL_N = 252` (measured by PSMV):**

```
per event type  CPI 118    NFP 134
per epoch       2010-2013: 78    2014-2017: 84    2018-2021: 90
per year        11 / 24 / 23 / 20 / 20 / 21 / 23 / 20 / 23 / 22 / 22 / 23
micro-era       counterfactual_micro_execution (pre 2019-05-06): 194
                actual_micro_available_era      (>= 2019-05-06):  58
span            2010-06-17 .. 2021-12-10   (~11.5 years, ~21.9 events/yr)
```

Epoch balance is good; the **micro-era split is not**. MNQ began trading
2019-05-06, so **194 of 252 events are a counterfactual** — "if today's micro execution conditions had
existed then" — reported on its own axis and never described as historical micro
performance.

---

## E. REACTION_AND_DECISION_TIMING  *(REPAIR 1)*

### E.1 The repaired timeline

```
... 08:28 ] [ 08:29 ] | [ 08:30 ] [ 08:31 ] | [ 08:32 ] | [ 08:33 ] ... [ 09:29 ] | 09:30 RTH open
                      ^                      ^           ^                        ^
                 RELEASE 08:30:00      SIGNAL COMPLETE   ENTRY                  EXIT, then
                 (BLS, attested)       08:32:00 ET       O(08:33)           the cash open arrives
                                       |<-- 60 s -->|
                                       execution-latency budget

  P_pre  = C(08:29)          last bar close strictly BEFORE the release instant
  R_init = C(08:31) - P_pre  ANNOUNCEMENT WINDOW -- measured, NEVER credited as P&L
  d_event= sign(R_init)
  SIGNAL COMPLETE at 08:32:00.000; the whole 08:32 minute is the latency budget
  ENTRY  = O(08:33)          the booked fill; conservative (an order sent promptly
                             would in reality fill inside the 08:32 bar)
  EXIT   = O(09:29)          PRE-SCHEDULED timed exit -- requires no observation
  Y_gross= d_event * (O(09:29) - O(08:33))   THE ONLY RETURN R1 MAY CLAIM
  HOLDING PERIOD = 56 minutes, fixed clock time, identical for every event
```

### E.2 Why `O(08:32)` is not mechanically attainable, and why it is dropped

ChatGPT's finding is correct and is accepted in full. `C(08:31)` is knowable only once
the 08:31 bar has *ended* — at 08:32:00.000. `O(08:32)` is by definition the **first
transaction of that same minute**, which may occur at 08:32:00.000 or within
milliseconds of it. Booking a fill at `O(08:32)` on a signal finalized at 08:32:00.000
assumes an observe-decide-transmit-match round trip of essentially zero. r1 defended
this as *"sub-second / co-located-enough"*; that defence fails on two mechanical
grounds:

1. **No execution evidence exists.** `PROJECT_CHARTER.md` Gate 2 (the automation-channel
   PoC, including the post-disconnect resting-order test) has **never been run** —
   *"候选均未通过任何 Gate"* — and `gate1/platform_params.yaml` carries
   `actual_cost_status: unconfirmed_until_gate2_poc`. There is no measured
   order-to-fill latency anywhere in this project, for any platform. Under the
   project's own evidence hierarchy an unmeasured latency assumption is Level 4/5 and
   cannot support a Level-1 executability claim.
2. **S0 constraint 3 requires a *realistically executable* decision delay**, and R1's
   entire identification rests on that word. A design whose fill is not mechanically
   guaranteed from 1-minute OHLCV does not satisfy it, whatever the returns say.

**Resolution.** `PRIMARY_ENTRY = O(08:33)`, giving a **full 60-second budget**. Any
order despatched at any point in `[08:32:00, 08:32:59]` is in the book before the 08:33
bar's first print, so the booked fill is not merely attainable but **conservative**.

**`O(08:32)` is DROPPED ENTIRELY.** It is not retained as an idealised upper-bound
diagnostic. It would add no scientific value the design does not already have —
auxiliary A1 (§L) already separates "is the effect only the jump?" — and retaining a
non-executable number invites exactly the misreading this repair exists to prevent.

**The r1 latency arm is likewise gone**: `O(08:33)` *is* the Primary, so there is no
alternative entry minute, and §C.3 forbids creating one.

### E.3 Why a two-bar reaction window — unchanged, and reinforced by the cost table

One fixed choice from microstructure and the project's own measured cost table — never
from an outcome, never from a scanned set. Measured from `spread_cost_table.csv` (MNQ
full bid-ask width, index points):

| minute (ET) | median | p90 | p95 | note |
|---|---|---|---|---|
| 08:29 | 0.75 | **2.00** | **2.75** | the book thins *before* the release too |
| **08:30** | 0.75 | **2.25** | **4.00** | release minute — p95 is **8× the RTH norm** |
| 08:31 | 0.75 | 1.25 | 1.50 | still elevated |
| 08:32 | 0.75 | 1.00 | 1.50 | latency budget — not traded |
| **08:33** | **0.75** | **1.00** | **1.00** | **entry minute** — p95 fully normalised |
| **09:29** | **0.50** | **0.75** | **1.00** | **exit minute** |

A direction read from the 08:30 bar alone would be the noisiest possible read, and a
decision at 08:31 would execute into the widest book of the session. Two minutes is
short enough to be the *announcement* rather than the drift, and is the shortest window
spanning more than the single chaotic minute.

**An unexpected benefit of REPAIR 1, worth recording:** at 08:33 the p95 spread is
**1.00 point versus 1.50 at 08:32**, so moving the entry one minute later costs one
minute of potential drift and **buys a materially tighter worst-case execution** — the
Severe-scenario round-turn falls from $7.24 to **$6.74** (§G.2).

### E.4 The residual ambiguity — surfaced, not backtested away

One scientifically defensible alternative remains and is **not** resolvable by evidence
available at S1: a **three-bar** reaction window (08:30–08:32, signal complete 08:33,
entry `O(08:34)`). It trades a cleaner direction read against a smaller remaining drift,
and microstructure alone does not decide it. This draft resolves it by fiat in the
conservative direction — two bars, signal complete 08:32:00, entry `O(08:33)` — and
flags it as **PRE_SEAL_OPEN_ITEM P-2** for confirmation **before the seal**. It must not
be decided by trying both; doing so would be the entry-time scan §C.3 forbids.

---

## F. PRIMARY_OUTCOME

### F.1 The outcome object

```
PRIMARY   Y_net  = cost-adjusted USD P&L per 1 MNQ of the single trade
                   enter O(08:33) direction d_event, timed exit O(09:29)
                   Base cost scenario; one trade per event; no stop; no overnight
                   HOLDING PERIOD = 56 minutes

SECONDARY (descriptive, never a decision input)
          Y_norm = d_event * (O(09:29) - O(08:33)) / ADR14
                   the scale-free scientific object, comparable across eras
```

`ADR14` is ITSF's frozen normalizer — the mean of `(RTH high − RTH low)` over the
previous 14 complete RTH trading days, **excluding the current day**. Already defined,
implemented, tested and causal; reusing it keeps R1 commensurable with the project's
existing cost and prop units rather than inventing a second scale.

### F.2 Why the horizon terminates at the cash open — and why that is not arbitrary

1. **The mechanism names the boundary.** The hypothesised channel is delayed
   incorporation by participants not yet present. At 09:30 the cash market opens, index
   arbitrage engages and the participant population changes wholesale — a change of
   régime, not a continuation of the same diffusion.
2. **It keeps R1 outside the already-revealed region.** ITSF's 1,575 revealed cells are
   anchored at 09:30 / 10:00 / 15:44; terminating before 09:30 keeps R1's outcome in a
   window that has never been an outcome on this sample.
3. **It avoids the opening auction.** Exiting into `O(09:30)` would price the trade at
   the highest-variance, highest-cost print of the morning.
4. **`09:29` is defined, not tuned** — *"the open of the last 1-minute bar that begins
   strictly before 09:30 ET"*. A boundary, not a parameter.
5. **The exit is mechanically attainable**, and REPAIR 1 does not touch it: a timed exit
   at a fixed clock time is **pre-scheduled** and requires no observation of any bar
   close, so no latency budget is needed on the exit side.

### F.3 No second horizon

The mechanism does not require one and the design philosophy forbids inventing one.
What *is* reported — because prop risk and cost feasibility need it, and because it
describes the *same* trade — is the **path**: per-minute mark-to-market close-path and
adverse-path, maximum favourable excursion, maximum adverse excursion and the time of
maximum adverse excursion. These feed §R.2 and are never a second outcome.

---

## G. COST_AND_MATERIALITY  *(REPAIR 2)*

### G.1 The measured cost environment at R1's repaired minutes

Entry minute is now **08:33** (median 0.75 / p90 1.00 / p95 1.00) and the exit minute
remains **09:29** (0.50 / 0.75 / 1.00). Full table in §E.3.

### G.2 Round-turn cost, by the four frozen scenarios — recomputed for `O(08:33)`

Using ITSF's frozen `S0 §6` grid and fill formulas (`spread/2` per side, plus slippage
in ticks per side, plus a one-time platform fee of `$1.74` per round turn — the
conservative Gate-1 choice; Topstep's all-in is `$1.22`). `MNQ_POINT_VALUE_USD = 2.0`,
`MNQ_TICK_POINTS = 0.25`.

```
                                                      r1 (O(08:32))   r2 (O(08:33))
Base          median spread + 1 tick/side
              entry (0.75/2 + 0.25) x $2 = $1.25
              exit  (0.50/2 + 0.25) x $2 = $1.00
              platform fee               = $1.74
              C_base_RT                                  $3.99          $3.99   unchanged
Conservative  p90 + 2 ticks/side                         $5.49          $5.49   unchanged
Stress        Base market friction x2, fee NOT doubled   $6.24          $6.24   unchanged
Severe        p95 + 3 ticks/side                         $7.24          $6.74   IMPROVED
```

**Declared proxy assumption, restated because it drives OD-4.** The spread distribution
is 2025-Q1 MNQ applied to 2010–2021. For ITSF the traded minutes were RTH, where the
spread is stable at one tick. For R1 the entry minute is an **event-adjacent pre-open
minute**, where the spread is regime- and era-dependent, and 2010–2013 NQ pre-open
liquidity was materially thinner than 2025's. **This is the largest single uncertainty
in R1's economics.**

### G.3 The materiality rule — corrected algebra, and the OD-4 choice

**The r1 interpretation was wrong.** With

```
Y_net_base = gross - C_base_RT        and        M = k x C_base_RT
```

the condition `Y_net_base >= k x C_base_RT` is equivalent to

```
gross >= (k + 1) x C_base_RT
```

so if the *true* total round-turn cost turns out to be `m x C_base_RT`, the true net is

```
true_net = gross - m x C_base_RT  >=  (k + 1 - m) x C_base_RT
true_net >= 0   <=>   m <= k + 1
```

**Therefore `k` buys break-even tolerance up to `(k+1)x` Base cost, not `k x`.** r1
claimed `k = 2` protected against a 2× cost error; it in fact protects against 3×, and
it was `k = 1` that corresponded to 2×. The constant is not wrong — its stated meaning
was. Corrected below, with both options presented so Aaron's OD-4 choice is explicit.

**OD-4 RULED: OPTION A, `k = 1`, so `M = $3.99` per event per 1 MNQ.** Recorded
before any PSMV output was interpreted. Both options are retained below so the
decision stays auditable; only OPTION A is operative.

```
OPTION A   k = 1     M = $3.99 per event per 1 MNQ   ( = 2.00 NQ index points )
           *** OPERATIVE (OD-4, delegated ruling 2026-09-17) ***
  MEANING           gross must be >= 2 x C_base_RT ; the edge must be at least as
                    large as one further Base round turn AFTER paying the first.
  COST ROBUSTNESS   break-even if the true round-turn cost is up to 2 x Base.
  ANNUAL AT M       ~21.9 events/yr x $3.99  =  ~$88 per year per 1 MNQ.
  DETECTION FLOOR   M enters the floor one-for-one; see the section I.4 form.
                    No numeric floor is carried in the pre-seal record:
                    PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV /
                    BEFORE_SEAL IF REQUIRED.
  CHARACTER         a DETECTION threshold. Answers "is there a real, cost-surviving
                    effect here at all?"

OPTION B   k = 2     M = $7.98 per event per 1 MNQ   ( = 3.99 NQ index points )
  MEANING           gross must be >= 3 x C_base_RT.
  COST ROBUSTNESS   break-even if the true round-turn cost is up to 3 x Base.
  ANNUAL AT M       ~21.9 events/yr x $7.98  =  ~$175 per year per 1 MNQ.
  DETECTION FLOOR   exactly $3.99 higher than OPTION A by construction, since M
                    is an additive term in the floor. NOT OPERATIVE, and no
                    numeric floor is carried (see PLANNING_POWER_TABLE above).
  CHARACTER         a ROBUSTNESS-LOADED threshold. Answers "is there an effect that
                    survives a cost model that is wrong by a factor of three?"
```

**The unavoidable trade-off, stated before any outcome exists.** `M` enters the
detection floor one-for-one (§I.4): every dollar added to `M` is a dollar added to the
MDE. Raising `k` from 1 to 2 therefore raises `MDE_80` by exactly **$3.99**, whatever
`n` is and whatever dispersion is assumed — that is algebra from the definition, not a
power calculation. `k` trades **statistical resolvability** against **robustness to
cost-model error**, and the two pull in opposite directions.

**This was the builder recommendation, and it is the ruling. `k = 1` (OPTION A),
for two reasons that do not depend on any R1 result:**

1. **Cost robustness is already carried elsewhere, and `k = 2` double-counts it.** The
   four-scenario grid independently spans Base → Severe = $3.99 → $6.74, i.e. ~1.7×
   Base *within a single era*, and the mandatory Conservative-survival condition below
   already forces the point estimate to remain positive at ~1.4× Base. Loading a
   further 3× tolerance into `k` applies the same protection twice.
2. **`k = 2` makes `INSUFFICIENT_EVIDENCE` close to certain.** The accepted r2
   planning basis (§I.4) already established that this design is adequately powered
   only for a large effect, and `k = 2` adds a further **$3.99** to the floor before
   the test can resolve anything. No refreshed numeric floor is quoted here.

`k = 2` would have been the correct choice for a *commercial* rather than a
*detection* threshold, at the price of making `INSUFFICIENT_EVIDENCE` close to
certain. It was not chosen. **`k = 1` is fixed and may never be derived from, or
revised after, any R1 outcome** (§C.3, invariant L-8). Aaron retains override
authority over the ruling, but only before the seal.

**The second, non-negotiable component — scenario survival — is unchanged by REPAIR 2:**

```
MATERIALITY = ( mean(Y_net) >= M  under Base )
              AND ( point estimate of mean(Y_net) > 0 under Conservative )
              AND ( all four scenarios reported; Stress and Severe disclosed )
Severe may be <= 0 without failing, provided it is stated.
```

### G.4 The commercial honesty check, stated before the result

At the operative threshold, with 252 events over ~11.5 years (~21.9 per year):

```
k = 1, M = $3.99   ~$88 per year per 1 MNQ    ~$880/yr on 10 MNQ
```

**A "material" R1 effect at this threshold is a small standalone business.** It
becomes commercially interesting only at size, or as one component of a portfolio of
event-driven trades. Said now, before any result, so that a supported verdict cannot
later be oversold and an excluded one cannot later be described as the loss of
something large.

### G.5 Statistical significance versus economic materiality — kept separate

```
STATISTICAL SIGNIFICANCE  is the interval's position relative to M
ECONOMIC MATERIALITY      is the value of M itself, and G.4's commercial reading
```

Never conflated. A statistically clean `mean(Y_net) = $2.10 ± $0.90` is **not** support
under R1: it is an effect that exists and does not matter, recorded as *excluded at
materiality M* with the point estimate disclosed. Conversely a large point estimate
with an interval spanning `M` is `INSUFFICIENT_EVIDENCE`, not a near-miss to be rescued.

---

## H. COVARIATES

*(Unchanged from r1 except that every timing reference now reads `O(08:33) → O(09:29)`.)*

### H.1 The claim variable, and only it

```
PRIMARY_CLAIM_VARIABLES
  d_event = sign( C(08:31) - C(08:29) )      -- the ONLY variable in the claim
  membership in the fixed {CPI, NFP} family  -- fixed by the calendar, not estimated
```

No interaction term, no threshold, no conditioning and no state gate enters the Primary.

### H.2 Context / feasibility covariates — four, all reported, none a gate

| covariate | definition | causal? | job | forbidden use |
|---|---|---|---|---|
| `vol_state` | tercile of `ADR14`, boundaries from the **trailing 250 event-eligible sessions only** | yes — trailing-only | execution feasibility; the honest stratification in control C2 | may not select events; full-sample terciles are a look-ahead, banned by L-5 |
| `event_type` | `CPI` or `NFP` | yes | tests the §D.2 pooling assumption | may not produce a second primary or a promotion |
| `era` | `2010-2013` / `2014-2017` / `2018-2021` (ITSF's frozen epochs) | yes | regime-dependence disclosure (S0 constraint 11) | may not select an era |
| `pre_release_participation` | total volume 08:00–08:29 ÷ its own trailing 60-event median | yes | one liquidity / participation proxy, for interpreting execution feasibility and the §G.2 proxy risk | may not condition the Primary |

**No state × signal grid. No regime search. No additional volatility definition.**
Invariant L-8 forbids any loop over alternative state definitions in the primary path.

### H.3 Covariates deliberately not included

Path-efficiency, retracement, gap, overnight-range and open-location measures all exist
in ITSF and are **excluded**: they are opening-drive features whose relationships to
ITSF labels are part of the 1,575 revealed cells, and importing them would import that
exposure into R1's design freedom.

---

## I. STATISTICAL_AND_MULTIPLICITY_PLAN

### I.1 Unit, estimand, estimator

```
UNIT       one release event (CPI or NFP); PRE_SEAL_STRUCTURAL_N = 252
ESTIMAND   mu = E[ Y_net ]   population mean net USD per 1 MNQ per event
ESTIMATOR  the sample mean over the pooled family
INTERVAL   stationary bootstrap over the EVENT SEQUENCE in calendar order
             expected block length   5 events   (~2.5 months of CPI+NFP)
             resamples               10,000
             seeds                   {7, 13, 31}
             method                  percentile, 95 %
           SENSITIVITY: expected block length 10 events (~5 months), reported
TEST       one-sided, H1: mu > M, direction declared in C.1
```

**Why a block bootstrap on events.** S0 constraint 11 is correct: 100 releases are not
100 independent pieces of evidence. Releases cluster inside macro regimes — consecutive
2021 CPI prints share an inflation regime, consecutive 2012 prints share a ZIRP regime.
Blocking in **event order** with an expected block of 5 keeps within-regime dependence
inside the resampled blocks. The convention is reused verbatim from ITSF's frozen §9
rather than re-invented, so it cannot be tuned to R1.

**Why no overlapping-observation correction is needed.** Holding periods are 56 minutes,
one per event, and the shortest gap between two R1 events is one calendar day. **No two
R1 trades ever overlap in time.** A genuine simplification, not an assumption.

### I.2 Multiplicity — the whole account, in one place  *(REPAIR 3 updated)*

```
CONFIRMATORY TESTS IN R1                              1
  the PRIMARY PREDICTIVE test of I.1: one pooled population, one entry time,
  one exit time, one direction rule, one materiality boundary, one side

NON-CONFIRMATORY, reported at nominal levels:
  MECHANISM_SPECIFICITY_ASSESSMENT  (event vs C2)     1   <- REPAIR 3
  CONTROL C1 (sign-randomized)                        1   (a BAR to support)
  AUXILIARY PREDICTIONS A1, A3                        2
  DESCRIPTIVE SPLITS (event type, era, vol tercile,
    micro-era)                                        reported

Nothing in the non-confirmatory block can create support. Only the single primary
test can move the verdict toward supported or excluded. The specificity assessment
CANNOT create support -- it only QUALIFIES THE VERDICT LANGUAGE (section M.2).
```

**Trial accounting.**

```
R1 consumes 1 formal trial on the NQ Development sample.
Prior formal trials on that sample : 1 (ITSF S0-T001, CONSUMED)
Prior researcher exposure on it    : 1575 revealed target cells (conservative
                                     upper bound; charter clause 13)
```

R1's write-up **must** carry that exposure figure as a conservative upper bound, must
**not** claim the sample is fresh, and must **not** attempt a deflated-Sharpe-style
correction against `N = 1`, which would be false comfort. The honest statement: *R1 is
one prespecified test on a sample already read once, at scale, for a related
phenomenon.*

### I.3 The pre-reveal power protocol — outcome-blind, and it gates the reveal

```
STEP 1 (S2, outcome-blind)
  Compute s_hat = the standard deviation of  d_ctrl * (O(09:29) - O(08:33))
  on NON-EVENT trading days at the SAME clock minutes, where d_ctrl is the
  same-construction sign of C(08:31) - C(08:29).
  This is CONTROL C2's dispersion. It is not the R1 outcome, and reading it
  exposes no R1 target metric.

STEP 2 (S2, outcome-blind)
  SE_hat   = s_hat / sqrt(n_final)
  MDE_80   = M + 2.486 * SE_hat        (one-sided 95%, 80% power)
  MDE_50   = M + 1.645 * SE_hat

STEP 3 (Owner gate, BEFORE any R1 outcome is computed or read)
  Report M, s_hat, SE_hat, MDE_80 and MDE_50 to Aaron.
  Aaron decides: PROCEED TO REVEAL | PARK FOR INSUFFICIENT POWER.
  If the CI half-width would exceed M, the design cannot distinguish supported
  from excluded, and the only honest outcomes are INSUFFICIENT_EVIDENCE or
  PARKED. Saying so before the reveal costs nothing; saying it after is a
  rationalisation.
```

Note the ordering under REPAIR 4: this protocol sits in **S2**, after the seal. It is
not PSMV. PSMV establishes `n_final` structurally *before* the seal; the power
computation consumes `n_final` and the control dispersion *after* it.

### I.4 Planning arithmetic, with its assumption named

**Not a measurement — and, after the record repair of 2026-09-17, not a number
either.** The prospective planning *form* is preserved here; the numeric table is not
carried in the pre-seal record.

```
PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED

FORM (unchanged, and identical to the section I.3 gate)
    SE      = s / sqrt(n)
    MDE_50  = M + 1.645 * SE
    MDE_80  = M + 2.486 * SE
DECLARED ASSUMPTIONS (assumptions, never measurements)
    s   a DECLARED dispersion in USD per 1 MNQ, spanning a low / mid / high
        case, to be replaced by the outcome-blind s_hat of section I.3
    n   PRE_SEAL_STRUCTURAL_N (section J), measured structurally by PSMV
    M   $3.99  (OD-4, k = 1)
```

**Why no table is printed here.** The PSMV authorization permitted structural facts
only and explicitly prohibited computing or exposing MDE. A deterministic planning
recalculation at the measured `n` was nevertheless carried in the PSMV record. It
exposed no R1 outcome, but it exceeded the authorized output surface, and the record
has been repaired rather than defended (§S.6). Refreshing the table is an ordinary
pre-seal act **outside** PSMV if Aaron wants it before sealing; either way the
authoritative power statement is the §I.3 gate, which uses a measured `s_hat` instead
of an assumption and is **post-seal and not run**.

**Carried forward from the accepted r2 planning basis and not re-derived here: R1 is
plausibly underpowered for a modest true effect and is adequately powered only for a
large one.** The only honest levers are more events (a
calendar extension → a new data decision) or a larger unit of account (NQ minis rather
than micros → a different prop and risk problem). Neither may be pulled after seeing a
result.

### I.5 Equivalence / exclusion logic

```
PRIMARY EFFECT EXCLUDED  <=>  CI_upper(mu) < M   AND   CI half-width < M
```

The second condition prevents a wide, uninformative interval from being read as
evidence of absence. If it fails, the record is `INSUFFICIENT_EVIDENCE`, whatever the
point estimate.

---

## J. SAMPLE_SUFFICIENCY

```
PRE_SEAL_STRUCTURAL_N      252 (MEASURED by PSMV, 2026-09-17)
POST_SEAL_SIGNAL_DEFINED_N to be determined in S2 (E4; see section S.3)
EVENTS PER YEAR            ~21.9
EPOCH BALANCE              78 / 84 / 90                                   GOOD
EVENT-TYPE BALANCE         CPI 118 / NFP 134                              GOOD
MICRO-ERA BALANCE          194 counterfactual / 58 actual                 POOR, disclosed
INDEPENDENT EPISODES       fewer than 258 -- see below
POWER FOR A LARGE EFFECT   adequate
POWER FOR A MODEST EFFECT  LIKELY INADEQUATE -- declared in I.4, measured in I.3
```

**Effective independence, counted honestly.** 252 events span 11.5 years and roughly
three or four distinguishable macro regimes (post-GFC ZIRP · taper / normalisation ·
2018 tightening and reversal · COVID and the 2021 inflation impulse). If the diffusion
mechanism is itself regime-dependent — and there is no reason to assume it is not — the
*effective* number of independent observations of the mechanism is closer to the number
of regimes than to 252. The block bootstrap addresses serial dependence within the
estimator; it does **not** manufacture regime diversity. The `era` covariate exists so
this is reported rather than assumed away.

---

## K. CONTROLS  *(timing repaired; C2 gains a prespecified specificity criterion)*

Two controls. Each answers one concrete confound. Neither exists for completeness, and
**no third control was added in this repair round.**

### K.1 C1 — sign-randomized control (same days, same minutes)

```
CONSTRUCTION  identical entry O(08:33), exit O(09:29), identical cost model,
              on the identical event set; direction drawn at random (fair coin,
              seeded, 10,000 draws) instead of d_event
ANSWERS       "is there simply a drift or a cost artefact in this window on these
              days, regardless of the reaction direction?"
DECISION ROLE a GUARD CONDITION on the primary predictive verdict (M.1): if C1
              also clears M, the effect is not attributable to the reaction
              direction and R1's primary effect is NOT supported
```

ITSF's own frozen null-benchmark family (*"fixed time random direction"*, charter
clause 6), reused rather than reinvented.

### K.2 C2 — non-event matched-clock control, and the specificity criterion  *(REPAIR 3)*

```
CONSTRUCTION  the same O(08:33) -> O(09:29) trade on NON-EVENT trading days
              (no CPI, no NFP, no FOMC calendar entry), direction = the same
              construction sign of C(08:31) - C(08:29)
ANSWERS       "is short-horizon matched-clock continuation generically present at
              this time of morning, or is it specific to a scheduled release?"
REPORTING     unmatched AND stratified by the SAME trailing vol tercile as H.2,
              because event days are systematically higher-volatility and an
              unmatched comparison is not like-for-like

PRESPECIFIED SPECIFICITY CRITERION  (single criterion; no new constant)
  D = mean(Y_net | event) - mean(Y_net | C2, vol-tercile-weighted)
  MECHANISM_SPECIFICITY_ESTABLISHED  <=>  95% lower bound of D  >  0
  Interval by the SAME bootstrap convention as I.1.

STATUS        NON-CONFIRMATORY. Nominal level, not corrected, and it CANNOT create
              support. Its only effect is on VERDICT LANGUAGE (section M.2).
CAUSALITY     Even when established, D > 0 does NOT demonstrate causation. It shows
              the effect is larger on release days than on matched non-release days
              -- which is consistent with information diffusion and with other
              explanations (event-day volatility, event-day participant mix,
              event-day liquidity provision). R1 may never claim more.
```

### K.3 Controls deliberately not built

A separately matched-sampling volatility control, a date-permutation control, a
regime-matched control and a bare-momentum benchmark are **not** built. The vol
stratification inside C2 covers the volatility confound at a fraction of the
complexity, and the rest answer no confound C1 and C2 leave open (vNext §8).

---

## L. AUXILIARY_PREDICTIONS  *(A2 restated under REPAIR 3; A3 restated under REPAIR 1)*

Two auxiliaries plus the specificity assessment. All **non-confirmatory** — none can
create support, and a failing auxiliary does not by itself exclude the effect.

```
A1  THE EFFECT IS NOT JUST THE ANNOUNCEMENT JUMP
    Prediction: restricted to the LOWER HALF of |R_init| (median split on a
    causally computable, ADR14-normalized quantity, computed within trailing
    information only), the primary estimate retains the SAME SIGN.
    Discriminates: genuine post-decision diffusion vs an artefact of large jumps
    and their microstructure. If the effect lives only in the largest jumps that
    is a different -- and far less tradeable -- phenomenon, and the write-up must
    say so.
    NOTE: A1 is now the ONLY instrument for this question, because the r1 idealised
    O(08:32) arm was dropped (E.2). It is sufficient for it.

A2  MECHANISM SPECIFICITY  -- promoted to a NAMED VERDICT AXIS, not a footnote
    This is no longer phrased as a prediction that quietly supports the mechanism.
    It is the MECHANISM_SPECIFICITY_ASSESSMENT of K.2, evaluated against the
    prespecified criterion (95% lower bound of D > 0), and its ONLY function is
    to select between the verdict labels in M.2. It can neither create nor
    destroy the primary predictive verdict.

A3  THE EFFECT SURVIVES REALISTIC EXECUTION
    Prediction: the point estimate remains positive under the Conservative cost
    scenario ($5.49 round turn, ~1.4x Base).
    REPAIR 1 NOTE: the r1 "08:33 latency-stress arm" is GONE -- O(08:33) is the
    Primary, and the 60-second latency budget is now built into the design rather
    than tested as a variant. A3 is therefore a COST-scenario test only, and no
    replacement latency arm may be created (C.3).
    If A3 fails while the Primary clears M under Base, the correct record is
    "effect present, execution-infeasible at this cost" -- NOT a supported
    strategy claim.
```

No fourth auxiliary. No cross-asset auxiliary (data absent, §O OD-6). No surprise-
magnitude auxiliary (data absent, §C.4).

---

## M. NEGATIVE_RESULT_SEMANTICS  *(REPAIR 3 — two verdict axes)*

### M.1 The two axes, defined prospectively

```
AXIS 1 -- PRIMARY_PREDICTIVE_VERDICT   (confirmatory; the ONLY axis that can be
                                        supported or excluded)

  PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE
    CI_lower( mean(Y_net) ) > M under Base
    AND control C1 (sign-randomized) does NOT clear M
    AND auxiliary A1 holds in sign
    AND the point estimate is positive under the Conservative scenario

  PREDICTIVE_EFFECT_EXCLUDED_AT_MATERIALITY_M
    CI_upper( mean(Y_net) ) < M   AND   CI half-width < M

  PREDICTIVE_EFFECT_UNRESOLVED
    the interval spans M, OR the pre-reveal power check (I.3) showed the design
    cannot resolve M, OR a data-availability exclusion materially shrank n

AXIS 2 -- MECHANISM_SPECIFICITY_ASSESSMENT   (non-confirmatory; language only)

  MECHANISM_SPECIFICITY_ESTABLISHED       95% lower bound of D > 0   (K.2)
  MECHANISM_SPECIFICITY_NOT_ESTABLISHED   otherwise
```

### M.2 The verdict matrix, and the exact allowed conclusion language

| Axis 1 | Axis 2 | **allowed conclusion language** | forbidden |
|---|---|---|---|
| SUPPORTED | ESTABLISHED | `PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE` + `MECHANISM_SPECIFICITY_CONSISTENT_WITH_INFORMATION_DIFFUSION`. Wording: *"the effect is materially larger on scheduled-release days than on matched non-release days, which is **consistent with** delayed information incorporation."* | *"information diffusion demonstrated / confirmed / caused"*. **Causality is never claimed, even here.** |
| SUPPORTED | NOT ESTABLISHED | `PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE` + **`MECHANISM_SPECIFICITY_NOT_ESTABLISHED`**. Wording: *"a cost-surviving short-horizon continuation effect is present on release days at an executable decision point; it is **not distinguishable** from the same rule applied at the same clock minutes on non-release days. R1 provides **no evidence for information diffusion**."* | any sentence containing *information diffusion* as a supported finding; describing R1 as an event-driven edge; any KB Finding attributing the result to a release mechanism |
| EXCLUDED | either | `PREDICTIVE_EFFECT_EXCLUDED_AT_MATERIALITY_M`. Axis 2 is **reported but not interpreted** — there is no effect whose specificity could matter. | *"no effect"* (the claim is *no effect of size ≥ M*); any extrapolation to FOMC, other instruments or other horizons |
| UNRESOLVED | either | `INSUFFICIENT_EVIDENCE` (KB: `unresolved`). Axis 2 reported as a descriptive number only. | treating a large point estimate as a near-miss; using Axis 2 to argue the mechanism is "probably there" |
| any | any | `PARKED` where a data-integrity, authority or feasibility blocker prevented the test — including Aaron declining OD-1 or the OD-3 power gate | describing PARKED as a negative result |

**The point of REPAIR 3, in one sentence:** the Primary can establish that a *rule*
predicts; only Axis 2 can say the rule's information is *specific to the release*; and
no combination of the two may be written as a causal mechanism claim.

### M.3 Forbidden collapses

```
"not significant"                      -> is NOT exclusion
low power                              -> is NOT exclusion
a failing auxiliary alone              -> is NOT exclusion
C1 clearing M                          -> IS a bar to support
Axis 2 established, Axis 1 unresolved  -> is NOT support of any kind
Axis 1 supported, Axis 2 not           -> is NOT evidence for information diffusion
Axis 2 established                     -> is NOT a causal finding
a positive Primary that fails A3       -> is NOT a deployable strategy claim
EXCLUDED on BLS 08:30 releases         -> says NOTHING about FOMC, PPI, ISM, other
                                          instruments or other horizons
```

### M.4 Explicit non-claims, carried into the verdict whatever it is

R1 cannot and will not claim: that the result generalises out of sample; that it
separates under-reaction from noise-plus-reversal (§C.4); that it holds for FOMC
(excluded on data quality, §D.1); that any Axis-2 outcome is causal (§K.2); that it is
deployable on a prop account without the separate MC work (§R.2); or that
infrastructure readiness is alpha.

---

## N. LEAKAGE_AND_CAUSALITY_INVARIANTS

Machine-checkable. These become **S2 acceptance targets** (L-1 … L-12) plus one
pre-seal invariant (L-13). **None is implemented here.**

| id | invariant | how it must be enforced |
|---|---|---|
| **L-1** | **Signal horizon.** No feature, filter or decision input may read any bar with `ts_event ≥ 08:32:00 ET` on the event day. *(Unchanged by REPAIR 1: the signal still completes at 08:32:00; only the fill moved.)* | runtime guard on the feature builder; a fixture mutating every post-08:31 bar must leave every signal byte-identical |
| **L-2** | **Level-1 attested timestamps only.** Every event row consumed must carry `release_time_status == official_time_recorded`. | loader refuses otherwise; test on a sentinel-carrying fixture row |
| **L-3** | **No release-time inference.** No default, fallback or "typical" release time exists anywhere in the code path. Encodes IR-17. | AST/grep scan for time literals in the event path; a test asserting an empty time column raises rather than defaults |
| **L-4** | **No pre-entry P&L.** *(REPAIR 1)* The P&L path begins at the entry fill at `O(08:33)`; **no bar with `ts_event < 08:33:00` contributes to `Y_net`** — this now covers the announcement window *and* the 08:32 latency minute. | assertion inside the P&L builder; a test perturbing `C(08:29)`, `O(08:30)`, `C(08:31)` and every 08:32 field, asserting `Y_net` unchanged |
| **L-5** | **Trailing-only baselines.** Every normalizer, percentile and tercile boundary (`ADR14`, `vol_state`, `pre_release_participation`, A1's median split, C2's vol weights) is computed from strictly prior observations. | a fixture randomising all future rows must leave every baseline unchanged |
| **L-6** | **Event set frozen before outcome.** The event-universe digest is recorded before any outcome computation; the runner refuses if it changes. | digest bound in the run identity, compared at run time — reuse ITSF's bundle-digest pattern |
| **L-7** | **No outcome-dependent inclusion.** The inclusion mask is a pure function of the frozen calendar, the frozen symbology map and pre-decision bar availability. | a test asserting the mask is invariant under arbitrary permutation of every `Y` |
| **L-8** | **No hidden parameter scan.** *(REPAIR 1 + REPAIR 2)* Exactly one reaction window, **exactly one entry minute `O(08:33)` with no alternative arm**, one exit minute, no threshold in the Primary, and **`k` read from the sealed prereg rather than computed**. | AST scan refusing any loop or comprehension over candidate times or thresholds in the primary path, and refusing any assignment to `k` outside the sealed-config loader |
| **L-9** | **Role boundary fail-closed.** Only `DEVELOPMENT_SIGNAL` may be loaded; IV and Lockbox raise `RoleError`. | reuse ITSF `roles.py` unchanged; regression test |
| **L-10** | **Cost-calibration isolation.** R1 reads only the derived `spread_cost_table`, never raw BBO. | reuse ITSF's `CostCalibrationLoader` boundary; AST test that no R1 module imports the raw decoder |
| **L-11** | **Calendar identity.** The event calendar's sha256 must equal the pinned `5e92ad00…5bb5e8c` (or a new separately attested digest bound in the prereg). | hash check at load; refuse on mismatch |
| **L-12** | **Anchor integrity.** *(REPAIR 1)* `C(08:29)` is the last bar close strictly before 08:30:00; the required anchor set is **`C(08:29)`, `C(08:31)`, `O(08:33)`, `O(09:29)`, `ADR14`**. No forward fill, no interpolation, no neighbouring-bar substitution — a missing anchor makes the event NA, excluded and counted. | reuse ITSF's IR-15 / IR-19 NA discipline; per-anchor availability table emitted by PSMV |
| **L-13** | **PSMV output purity.** *(REPAIR 4 — required by the new pre-seal stage, not an added robustness control.)* The pre-seal mechanical validation may emit only counts, booleans, timestamps, structural identifiers, NA reason codes and roll flags. **It must emit no price, no return, no signal sign, no P&L and no distribution of any kind.** | a machine-checked output-schema whitelist on the PSMV artifact, plus the ITSF-style guard test that scans the rendered artifact for numeric-value patterns before it may be written |

---

## O. OWNER_DECISIONS_REQUIRED — **ALL RULED 2026-09-17**

```
DECISION_TYPE = DELEGATED_OWNER_RULING
DELEGATED_BY  = Aaron        DECIDED_BY = Fable 5.1      ACCEPTED_BY = ChatGPT
PACKET_STATUS = PASS / CLOSED
FULL RECORD   = R1_DELEGATED_OWNER_DECISIONS.md
```

These are **not** Aaron personally authoring each scientific selection. **Aaron
retains override authority over every line**, until the seal.

| id | ruling | operative consequence in this document |
|---|---|---|
| **OD-1** DATA AUTHORITY | **GRANT** | NQ Development OHLCV + frozen F10 CPI/NFP calendar + derived spread-cost table, **R1 only**. Internal Validation, Lockbox and protected ITSF outcome artifacts remain NOT GRANTED and were not accessed. §B.2 |
| **OD-2** SECOND TRIAL | **ACCEPT** | Separate R1 lineage and separate R1 trial registry (`R1_TRIAL_REGISTRY.md`). `SAMPLE_FORMAL_TRIAL_ORDINAL = 2`; `INHERITED_RESEARCHER_EXPOSURE_COUNT = 1575` as the conservative disclosed upper bound; the ITSF registry is referenced by digest and **never mutated**. **No new multiple-testing correction was invented**: charter clause 13 is preserved exactly and the statistical adjustment stays with §I. |
| **OD-3** POWER GATE | **ACCEPT** | Part of the future **sealed** protocol. **Not run.** PSMV computed no control dispersion, no `s_hat`, no `SE_hat` and no MDE. §I.3 |
| **OD-4** MATERIALITY | **k = 1** | `M = 1 × C_base_RT = $3.99` per event per 1 MNQ ( = 2.00 NQ index points). Recorded **before** any PSMV output was interpreted; never recomputable from data. §G.3 |
| **OD-5** PROJECT HOME | **OPTION A** | `nq-event-diffusion-research/`, minimum vNext structure. ITSF governance not cloned, ITSF repository not modified, ITSF assets reused by digest-pinned read-only reference and ITSF frozen logic by transcription validated against ITSF's own published figures. |
| **OD-6** CROSS-ASSET | **DECLINE_PURCHASE** | No ES/rates purchase. **No cross-asset covariate enters R1.** §H.3 |
| **OD-7** FOMC | **CONFIRM_DEFER** | `FOMC = UNRESOLVED / DEFERRED`, reason: historical timestamp integrity / different event structure. **Never falsified, never rejected.** §D.1 |
| **P-2** REACTION WINDOW | **OPTION A** | `P_pre = C(08:29)` · `R_init = C(08:31) − C(08:29)` · `SIGNAL_COMPLETE = 08:32:00 ET` · `PRIMARY_ENTRY = O(08:33)` · `EXIT = O(09:29)`. No alternative timing arm, no scan. §E |

**The single Owner decision that remains:** *seal, or withhold the seal.* Nothing
else in this document awaits a ruling.

## P. PRE_SEAL_OPEN_ITEMS

```
P-1  S0 provenance                                          CLOSED 2026-09-17
     Persisted as R1_S0_PROVENANCE.md: the Fable -> ChatGPT -> Astra XHIGH ->
     Fable -> ChatGPT -> delegated-Owner chain, the R1 = RESEARCH outcome, the
     parallel dispositions (R2 = RESEARCH conditional on separate data
     feasibility; D3 = PARK with reserve rationale; D1/D5/D6 = PARK; THIRD SLOT
     = EMPTY) and the twelve binding S0 constraints with their §-pointers.

P-2  Reaction window / signal instant / entry minute          CLOSED 2026-09-17
     Ruled OPTION A. Two-bar window, SIGNAL_COMPLETE 08:32:00 ET, entry
     O(08:33), exit O(09:29). No alternative arm exists and none may be created.

P-3  Anchor availability                                      CLOSED 2026-09-17
     MEASURED by PSMV-1 under L-13. Per-anchor table in §S.1; six events removed
     at E3, five of them Good Friday. PRE_SEAL_STRUCTURAL_N = 252.

P-4  Exact roll overlap                                       CLOSED 2026-09-17
     MEASURED by PSMV-2 with ITSF's own frozen `_roll_map` logic: 47 intervals,
     47 transitions, 47 distinct transition sessions, all inside their official
     intervals, EXACTLY ZERO coinciding with a CPI or NFP release.

P-5  2025-Q1 spread proxy on 2010-2013 pre-open minutes              OPEN
     Unchanged and deliberately not closed. It is the largest economic
     uncertainty in R1 and it is what OD-4's k protects against. An additional
     early-era BBO probe is an Owner PURCHASE question, not a blocker; R1 is
     researchable without it under the four-scenario grid.            [cost]

P-6  KB cataloguing                                           NOT APPLICABLE YET
     Under the KB's standing rule R1 gets no card until it produces its first
     Finding. None is proposed.                              [governance]

P-7  Mechanical validation of the prereg format              CLOSED 2026-09-17
     Closed with the SMALLEST representation that permits mechanical checking,
     not a schema project: `R1_PREREG_MANIFEST.json`, a structured companion
     carrying only the fields that genuinely matter -- lineage identity, stage,
     event family, reaction timing, entry / exit, k, data grant, outcome-reveal
     authority, seal status, trial identity, structural n, and the E4 deferred
     status. `psmv/validate_prereg.py` checks the manifest against its required
     shape AND cross-checks every field against the prose preregistration,
     PROJECT_STATE.md, the decisions record, the trial registry and the PSMV
     artifact, so the companion cannot silently drift from the document it
     describes. The 1,300 lines of prose were deliberately NOT converted into a
     schema instance.                                         [mechanical]

P-8  Version control for the new project                     CLOSED 2026-09-17
     `nq-event-diffusion-research/` is now its own standalone local git
     repository -- no remote, nothing pushed -- created as ordinary technical
     implementation of OD-5 = OPTION A rather than as a new scientific
     decision. Generated caches and every market-data / archive extension are
     ignored; no market-data file, no protected outcome and no ITSF file is
     tracked; the parked ITSF repository was not touched. The sha256 pins in
     R1_TRIAL_REGISTRY.md remain, and now sit inside a committed history.
     PRE_SEAL_PROJECT_COMMIT is recorded in PROJECT_STATE.md and in
     R1_TRIAL_REGISTRY.md. It is **not** the sealed commit -- the seal remains
     an Aaron Owner act.                                  [reproducibility]
```

## Q. THE 24 REQUIRED SECTIONS, CONSOLIDATED

| # | section | where resolved | status |
|---|---|---|---|
| 1 | RESEARCH QUESTION | §C.1 — does economically meaningful directional adjustment remain after a realistically executable decision delay? | DRAFTED |
| 2 | MECHANISM | §D.2 — heterogeneous-speed incorporation of a scheduled macro number | DRAFTED |
| 3 | CLAIM | §C.1 — **predictive**; mechanism held separate (REPAIR 3) | **REPAIRED** |
| 4 | EVENT UNIVERSE | §D.2–D.3 — {CPI, NFP}; E0 277 → E1 258 → E2 258 → **E3 252**, all MEASURED | **PSMV-CLOSED**; E4 post-seal |
| 5 | DATA AUTHORITY | §B.2 — **OD-1 = GRANT**, R1 scope only; IV / Lockbox / protected ITSF outcomes NOT granted and not accessed | **RULED** |
| 6 | INFORMATION SET | §E.1, L-1, L-5 — signal horizon `ts_event < 08:32:00`; trailing-only baselines | DRAFTED |
| 7 | INITIAL REACTION | §E.1–E.3 — `C(08:31) − C(08:29)` | DRAFTED, P-2 |
| 8 | DECISION POINT | §E.1–E.2 — signal complete 08:32:00; **entry `O(08:33)`**, 60 s budget | **REPAIRED** |
| 9 | PRIMARY OUTCOME | §F — `Y_net`, USD per 1 MNQ, `O(08:33)` → `O(09:29)`, **56 minutes** | **REPAIRED** |
| 10 | MATERIALITY | §G.3 — **OD-4 ruled `k = 1`**, `M = $3.99` per event per 1 MNQ | **RULED** |
| 11 | STATE / COVARIATES | §H — one claim variable, four context covariates, no grid | DRAFTED |
| 12 | CONTROLS | §K — C1 bar-to-support; C2 + prespecified specificity criterion | **REPAIRED** |
| 13 | STATISTICAL PLAN | §I.1 — event-block stationary bootstrap, ITSF's frozen convention | DRAFTED |
| 14 | MULTIPLICITY | §I.2 — one confirmatory test; specificity non-confirmatory; exposure 1575 disclosed | **REPAIRED** |
| 15 | SAMPLE SUFFICIENCY / MDE | §I.3–I.4, §J — `n` MEASURED; `PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED`; the OD-3 power gate remains post-seal and was NOT run | **REPAIRED** (r4) |
| 16 | AUXILIARY PREDICTIONS | §L — A1, A2 (specificity axis), A3 (cost only) | **REPAIRED** |
| 17 | COST / EXECUTION | §G.1–G.2 — recomputed at 08:33; Severe improves to $6.74 | **REPAIRED** |
| 18 | PROP-CONSTRAINT TREATMENT | §R.2 | DRAFTED |
| 19 | NEGATIVE-RESULT SEMANTICS | §M — two axes, verdict matrix, forbidden collapses | **REPAIRED** |
| 20 | DATA-LEAKAGE INVARIANTS | §N — L-1 … L-13 | **REPAIRED** |
| 21 | IMPLEMENTATION REQUIREMENTS | §R.1 — **PSMV-1…4 (pre-seal)** then S2-1…S2-9 (post-seal) | **REPAIRED** |
| 22 | OWNER DECISIONS REQUIRED | §O — OD-1 … OD-7 and P-2, all ruled (delegated) | **CLOSED** |
| 23 | PRE-SEAL OPEN ITEMS | §P — P-1…P-4, P-7, P-8 CLOSED; P-5 open and non-blocking (cost residual); P-6 N/A | **CLOSED EXCEPT P-5** |
| 24 | SEAL CONDITIONS | §R.3 — 10 of 11 satisfied; only the seal itself remains | **UPDATED** (r4) |

### R.1 — §21 IMPLEMENTATION REQUIREMENTS, in the corrected stage order

```
=== S1 PRE-SEAL MECHANICAL VALIDATION (PSMV) ===
    Runs ONLY after OD-1. Structure only. Governed by invariant L-13.
    READ SURFACE: presence/absence, timestamps, structural identifiers,
                  NA reason codes, roll-transition flags.
    MUST NOT EXPOSE: prices, returns, signal signs, P&L, R1 outcome
                  distributions, or any statistic derived from them.

PSMV-1  DONE. Per-event anchor availability across the 258 events:
        C(08:29), C(08:31), O(08:33), O(09:29), ADR14 availability.
        Counts, booleans and NA reason codes ONLY.               closed P-3
PSMV-2  DONE. Exact is_roll_transition overlap using ITSF's own frozen logic
        and the frozen symbology map; is_roll_window counts.     closed P-4
PSMV-3  DONE. The E0..E3 funnel, reported CONSERVED at every level (parent =
        child + removed; removed sets mutually disjoint; no event vanishes
        unaccounted) -- the ITSF preflight funnel pattern, reused.
        E4 is NOT in the pre-seal funnel; see section S.3.
PSMV-4  DONE. PRE_SEAL_STRUCTURAL_N, the per-anchor availability table and the
        epoch / event-type / micro-era balance, WRITTEN INTO sections D.3
        and S.

    -->  ChatGPT / Aaron acceptance  -->  AARON SEALS  <--

=== S2 BUILD (only after the seal) ===
S2-1  Event loader over the frozen calendar, enforcing L-2, L-3, L-11.
S2-2  Signal builder enforcing L-1, L-5, L-12.
S2-3  Trade/P&L builder enforcing L-4 (no bar before 08:33:00 contributes),
      reusing src/itsf/s0/costs.py fill formulas and the four frozen scenarios
      UNCHANGED; per-minute close-path and adverse-path emitted for R.2.
S2-4  Inclusion mask as a pure function (L-7), reusing PSMV-3's funnel.
S2-5  Controls C1 and C2 built in the SAME code path as the Primary, so a
      divergence is impossible by construction; C2 carries the vol-tercile
      weighting and the D statistic of K.2.
S2-6  Bootstrap module reusing ITSF's frozen convention: block 5 events, 10,000
      resamples, seeds {7,13,31}, percentile 95%; sensitivity block 10.
S2-7  The I.3 pre-reveal power computation, emitted as its OWN artifact,
      computed and readable WITHOUT touching any R1 outcome.
S2-8  The L-1..L-12 invariant test suite, each invariant with a mutation test
      that must FAIL when the invariant is removed. A guard never proven able
      to fail is not a guard.
S2-9  Outcome sealing: R1 outcomes written to a run directory and NOT printed to
      console, so the OD-3 power gate is executable rather than notional.

NOT IN S2: no strategy build, no MC, no prop simulation beyond the path emission
      in S2-3, no parameter search of any kind.
```

### R.2 — §18 PROP-CONSTRAINT TREATMENT

R1 does **not** rebuild ITSF's Monte Carlo. It emits what a future prop assessment
would need and stops:

* **Per-trade minute-level paths**, both `close-path` and `adverse-path` (long uses
  minute low, short uses minute high), as ITSF's frozen §10.1 atomic record requires —
  because Topstep and Lucid both breach on **real-time equity including unrealized
  P&L**, so a day that closes green can still be a breach.
* **Event-day tail disclosure.** S0 constraint 10 is correct: the events most likely to
  produce delayed adjustment also produce the widest spreads and the largest
  excursions. R1 must report the distribution of maximum adverse excursion per event in
  USD per 1 MNQ, and the worst individual events, **as a feasibility fact**, not as a
  strategy result.
* **The no-stop Primary is deliberate and it has a cost.** A stop would introduce a
  parameter and a whole optimisation surface, so the Primary has none. The consequence —
  a naked 56-minute event position with unbounded intraday excursion against a $1,000
  DLL and a $2,000 trailing MLL — is a **real feasibility problem** reported as one. If
  the MAE distribution shows a meaningful fraction of events would breach a 50k account
  at one micro, then **R1 is not deployable on a prop account as specified**, whatever
  the Primary says. That is a finding, and R1 must state it rather than quietly adding
  a stop.
* **Position sizing is out of scope.** No risk-budget vector, no integer-contract
  policy, no account state machine — those belong to a future MC under a separate Owner
  decision.

### R.3 — §24 REVISED SEAL CONDITIONS  *(REPAIR 4)*

The preregistration may be sealed when, and only when, **all** of the following hold,
**in this order**:

```
 1.  OD-1 GRANTED    SATISFIED 2026-09-17 (delegated ruling; R1 scope only)
 2.  OD-2 RULED      SATISFIED -- ACCEPT, separate R1 lineage and registry
 3.  OD-4 FIXED      SATISFIED -- k = 1, recorded BEFORE any PSMV output was
                     interpreted and before any outcome exists
 4.  OD-5 DECIDED    SATISFIED -- OPTION A, `nq-event-diffusion-research/`
 5.  OD-7 CONFIRMED  SATISFIED -- FOMC = UNRESOLVED / DEFERRED
 6.  P-1 CLOSED      SATISFIED -- R1_S0_PROVENANCE.md
 7.  P-2 CONFIRMED   SATISFIED -- two-bar / 08:32:00 / O(08:33) / O(09:29)
 8.  PSMV EXECUTED   SATISFIED -- PSMV-1..PSMV-4 ran under L-13 (PASS, mutation
                     demonstrated), and PRE_SEAL_STRUCTURAL_N = 252, the
                     per-anchor availability table, the exact roll overlap and
                     the conserved **E0..E3** funnel are WRITTEN INTO this
                     preregistration (sections D.3 and S).
                     *** THIS MUST NOT BE WAIVED ***
                     AMENDED BY THE SCOPE FINDING IN SECTION S.3: the pre-seal
                     funnel is E0..E3, not E0..E4. E4 needs price values and is
                     deferred to S2. `n` is therefore sealed as
                     PRE_SEAL_STRUCTURAL_N, with POST_SEAL_SIGNAL_DEFINED_N
                     determined mechanically in S2.
 9.  P-7 CLOSED      SATISFIED 2026-09-17 -- R1_PREREG_MANIFEST.json, the
                     smallest structured companion that permits mechanical
                     validation, cross-checked against the prose, the project
                     state, the decisions record, the registry and the PSMV
                     artifact by psmv/validate_prereg.py.
10.  OD-3 ACCEPTED   SATISFIED -- the pre-reveal power protocol is in the text
                     (section I.3) and was NOT run at PSMV.
11.  AARON SEALS     SATISFIED 2026-09-17 -- Aaron authorized the S1 final
                     seal; Claude Opus executed it. Only S2 BUILD remains,
                     and it is NOT authorized by the seal.

STATUS: 11 of 11 satisfied. The seal was taken on 2026-09-17 and binds to a
committed state (section T.3). P-5 remains a disclosed, NON_BLOCKING_RESIDUAL
cost-model limitation and was deliberately NOT resolved by a purchase at seal
time.
```

**Why item 8 must not be waived, restated after REPAIR 4 — and now discharged.**
Sealing a preregistration whose sample size is unknown would leave §I.4's power
statement an assumption rather than a fact, and the §I.3 power gate would be gaming its
own input. PSMV read bar presence only and emitted no value (L-13 PASS, §S.4), so it
exposed no outcome and ran **before** the seal, exactly as required. `n` is now a
measured fact in the text rather than a promise — with the honest qualification of
§S.3 that it is the *structural* `n`, because the last funnel stage is not decidable
without prices.

**This document is SEALED (section T). Being sealed authorizes nothing by itself: not S2, not a run, not a reveal.**

---

## S. PSMV RESULTS — S1 PRE-SEAL MECHANICAL VALIDATION, 2026-09-17

```
AUTHORITY   OD-1 GRANT (delegated ruling). Structural read only.
ARTIFACT    artifacts/PSMV_STRUCTURAL_REPORT.json
            sha256 df0242bad6e2a1e2eb6ad1c412f91ffc1d9d421ef036ea802f7fd382e68aef47
ATTESTATION artifacts/PSMV_PURITY_ATTESTATION.json
            sha256 67e13b1770d1895084c2a989fb8c67e5692b1888f11d3c21cd464cdb7f546c7e
PURITY      L-13 PASS, mutation-demonstrated (S.4)
```

**Input identity, verified before any decode.** 139 `ohlcv-1m` files, each
SHA-256-checked against the vendor `manifest.json` (fail closed); digest roll-up
`320b12c4c376acd165f67176dcfb0dc03d2fbd6f74fd872dc3e6912c9577d7f1`.
`f10_events.csv` = `5e92ad00…5bb5e8c` (L-11 PASS). `nq_v0_mapping.csv` =
`85a32d44994b51e004e0c322510527aae18b70e1fadc70437e754253a2ac1850`.
3,848,635 bars decoded across 3,586 ET dates; **zero duplicate RTH minutes**.

**Transcription validated by reproduction.** R1 transcribes ITSF's frozen funnel,
ADR14 basis and roll mapping rather than importing ITSF code, so the parked
repository is never executed or dirtied. PSMV independently reproduced **13 of 13**
published ITSF preflight figures with zero discrepancies — 3,848,635 bars;
2,989 / 20 / 2,969 / 85 / 2,884 / 2 / 2,882 / 14 / 2,868; complete-390 = 2,870;
47 roll transitions; 235 roll-window days; no duplicate RTH minutes. Full table in
`R1_TRIAL_REGISTRY.md` §3. That is **mechanical evidence** the transcription
behaves identically to the frozen logic — not a builder claim, and not independent
verification of the frozen logic itself.

### S.1 — PSMV-1 anchor availability (population = E2, 258 events)

Presence/absence of the named **bar location** only. No value of any anchor bar
was read.

| anchor | minute-of-day ET | present | missing | missing dates |
|---|---|---|---|---|
| `C(08:29)` | 509 | 256 | 2 | 2017-04-14, 2020-04-10 |
| `C(08:31)` | 511 | 256 | 2 | 2017-04-14, 2020-04-10 |
| `O(08:33)` | 513 | 256 | 2 | 2017-04-14, 2020-04-10 |
| `O(09:29)` | 569 | **253** | **5** | 2012-04-06, 2015-04-03, 2017-04-14, 2020-04-10, 2021-04-02 |
| `ADR14` availability | — | 257 | 1 | 2010-06-17 |

`ADR14` is resolved as **availability only**: it exists iff ≥ 14 complete-390-bar
RTH days precede the event date. That is a bar count. The value was never computed.
2010-06-17 has **8** such days.

**Six distinct events are removed at E3, and five of them are Good Friday** — see
the table in §D.3. Three are NFP releases on a Good Friday when CME ran an
abbreviated equity-futures session that **closed at 09:15 ET**: the entry anchors
exist, the 09:29 exit anchor does not, so the R1 trade is *enterable but not
exitable*. Two are CPI releases on a Good Friday with no scheduled session and
zero bars. This is a genuine **execution-feasibility** finding, it was produced by
the prespecified anchor rule with no special case, and **no price was read to
discover it**.

### S.2 — PSMV-2 exact roll overlap

```
intervals in the frozen mapping            48
transitions (intervals after the first)    47
distinct RTH transition sessions           47
all_map_to_valid_rth_trading_day           TRUE
all_inside_official_interval               TRUE   (fail-closed assertion)
is_roll_window days (transition +- 2 RTH)  235
CPI/NFP events on a transition session     0      <- E2 removal = 0, EXACT
```

The r2 approximation was correct and is now measured with ITSF's own frozen
`_roll_map` logic. `is_roll_window` remains a **disclosed flag**, not an exclusion.

### S.3 — `PSMV_SCOPE_CONFLICT` (E4) and the bounded correction

```
PSMV_SCOPE_CONFLICT = The r2 seal condition 8 required "the conserved E0..E4
                      funnel" to be written into the preregistration before the
                      seal. Stage E4 removes events where R_init == 0 exactly.
                      R_init is the difference of two bar CLOSE PRICES, so
                      deciding E4 requires inspecting market values -- which
                      invariant L-13 forbids pre-seal, and which the PSMV
                      authorization explicitly prohibits. The two requirements
                      cannot both be met.

SAFE_RESOLUTION     = The pre-seal funnel stops at E3, the deepest point
                      decidable from structure alone. Seal condition 8 is
                      amended from "E0..E4" to "E0..E3". `n` is recorded as TWO
                      DISTINCT QUANTITIES, never conflated. NO PRICE WAS
                      INSPECTED TO CLOSE E4, and E4 remains open.
```

This is the smallest correction that preserves both purity and the substance of
seal condition 8 — which was that the sample size must be a **measured fact inside
the sealed text**, not a promise. It remains one.

```
PRE_SEAL_STRUCTURAL_N      = 252
  the structurally eligible event count after E0 -> E1 -> E2 -> E3.
  MEASURED. Sealed into this preregistration. This is the n that any
  planning-power arithmetic must use, once it is refreshed OUTSIDE PSMV
  (section I.4).

POST_SEAL_SIGNAL_DEFINED_N = to be determined mechanically in S2, when the
  signal may legally be computed. It equals PRE_SEAL_STRUCTURAL_N minus the
  E4 no-direction events (R_init == 0 exactly). It is expected to be 0 to 2
  smaller -- an EXPECTATION FROM THE ITSF L82 PRECEDENT (26 zero-direction days
  in 2,882), NOT a measurement, and it may not be reported as one.
```

Two consequences, stated so neither can be quietly ignored later:

1. **S2 must publish `POST_SEAL_SIGNAL_DEFINED_N` and the E4 removal count as its
   first outcome-adjacent act**, before the pre-reveal power gate consumes `n`.
2. **If E4 removes materially more than the ITSF precedent suggests, that is a
   finding about the data, not a licence to adjust anything.** The design is
   sealed by then.

### S.4 — PSMV-7 output purity (invariant L-13)

Three mechanical rules, each applied to the live artifact and then to a
deliberately poisoned fixture that it must refuse.

| rule | what it enforces | live | mutation fixture | refused? |
|---|---|---|---|---|
| **R1** `NO_FLOAT_LEAF` | every numeric leaf is an `int` — counts and minute indices are integers; a price, return, mean, standard deviation, dispersion or MDE is not | PASS | fabricated sentinel float `1.2345` | **YES** |
| **R2** `NO_FORBIDDEN_KEY` | no object key contains an outcome token, matched **token-wise** after splitting on every non-alphanumeric character | PASS | key `mean_return_per_event` | **YES** |
| **R3** `SOURCE_FIELD_SCAN` | the producing module holds no string literal naming a price/volume field, so it cannot have dereferenced one | PASS | literal `"close"` in a subscript | **YES** |

**L-13 is demonstrably capable of failing.** The first version of R2 used a
word-boundary regex, and `\bmean\b` does not match inside `mean_return_per_event`
because `_` is a word character — so the guard passed a poisoned fixture. Its own
mutation demonstration caught that, and the rule was rewritten to token matching.
A guard that had never been shown to fail would not have surfaced this.

Three keys trip token matching for declared, audited reasons and are allowlisted
individually rather than by loosening the pattern:
`E4_r_init_zero_no_direction` (names the **deferred** test; carries status and
rationale, no value) · `L1_minus_early_close_equals_L2` and
`minus_scheduled_early_close_days` (scheduled half-day **session structure**, ITSF
frozen L44, never a closing price).

**The strongest purity property is structural, not procedural:** the PSMV reader
names exactly **one** record field, `ts_event`. `open`, `high`, `low`, `close` and
`volume` are never selected, so no price could reach a variable, an artifact or
this document even by mistake.

### S.5 — what PSMV did NOT do

```
R_init / its sign                     NOT COMPUTED
any price, price difference or return NOT COMPUTED, NOT READ
P&L, outcome distribution, primary
  statistic                           NOT COMPUTED
control dispersion s_hat / SE / MDE   NOT COMPUTED  (OD-3 gate is post-seal)
the R1 outcome engine                 NOT BUILT
Internal Validation                   NOT ACCESSED (and not on this machine)
Physical Lockbox                      NOT ACCESSED (and not on this machine)
protected ITSF outcome artifacts      NOT ACCESSED
the ITSF repository                   NOT MODIFIED (clean at 11725fb)
the ITSF trial registry               NOT MODIFIED (sha256 b964b19a... unchanged)
the R1 trial                          NOT CONSUMED -- PSMV consumes no exposure
S1                                    NOT SEALED
S2                                    NOT STARTED
```

### S.6 — `PSMV_MDE_SCOPE_VIOLATION` and the bounded record repair

The PSMV execution was reviewed after the fact. The structural results were
accepted; the **record** was not, and it has been repaired rather than defended.

```
FINDING                    The PSMV authorization permitted structural facts
                           only and explicitly PROHIBITED computing or exposing
                           MDE. The PSMV record nevertheless carried a
                           deterministic planning recalculation of the detection
                           floor at the measured n, a derived per-contract /
                           index-point interpretation of it, and a conclusion
                           drawn from those numbers.

PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY
R1_OUTCOME_CONTAMINATION = NO
PSMV_RERUN_REQUIRED      = NO
```

**Why `NO` on contamination — stated precisely rather than reassuringly.** The
recalculation consumed exactly three inputs: the structurally measured `n`, the
ruled `M` (OD-4), and a **declared** dispersion assumption `s`. None of the three
is an R1 outcome. No price, return, sign, P&L or realised dispersion entered it;
no protected artifact was opened; the L-13 guard held throughout, and the PSMV
artifact never contained a float leaf at all (§S.4). The violation is one of
**authorized output surface**, not of outcome blindness — so it is repaired by
removing numbers from the record, not by re-running anything.

**What was removed.** The recalculated `MDE_50` / `MDE_80` table from §I.4; the
two numeric DETECTION FLOOR lines from §G.3; the derived per-contract and
index-point interpretation and every conclusion drawn from those values, in §I.4
and in the recommendation below. The prospective **form** and its declared
assumptions are preserved in §I.4.

```
PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED
```

The authoritative power statement was never this arithmetic in any case: it is
the **OD-3 pre-reveal gate** of §I.3, which uses actual non-event control
dispersion, sits in **post-seal S2**, and runs **before any R1 outcome is
revealed**. That gate was not run and is not authorized.

**Unchanged by this repair.** Every structural PSMV fact; both artifacts; both
digests. `artifacts/PSMV_STRUCTURAL_REPORT.json` and
`artifacts/PSMV_PURITY_ATTESTATION.json` were **not modified** — they never
contained an MDE, because a float leaf is exactly what L-13 forbids. The repair
touched prose only.

## R. RECOMMENDATION

*(Historical, and now discharged: this recommendation was accepted on 2026-09-17
and the seal was taken. Retained unaltered as part of the sealed record.)*

**Proceed to final acceptance, then to Aaron for the seal.** The delegated
Owner packet is closed, PSMV is complete and pure, `n` is a measured fact, the
PSMV record has been repaired to its authorized surface (§S.6), and the pre-seal
state is committed. **The only decision left is the seal itself.**

Three things should weigh on the Owner decision, together:

1. **The design survived contact with the data.** PSMV reproduced all 13 published
   ITSF preflight figures, found zero roll collisions, and cost only 6 of 258 events —
   2.3 % — at the anchor stage. The entry choice from REPAIR 1 also still looks right:
   08:33 has a **tighter worst-case spread** than 08:32 (p95 1.00 vs 1.50 points), so
   the Severe round turn is $6.74 rather than $7.24.
2. **Power remains the real risk, and PSMV did not improve it.** The accepted r2
   planning basis already concluded that this design is adequately powered only for a
   large effect; PSMV measured `n`, changed no design element, and removed 2.3 % of the
   events. **`INSUFFICIENT_EVIDENCE` remains the single most likely R1 verdict**, and
   the OD-3 pre-reveal power gate exists so that this is established before the outcome
   is read, not after. No refreshed detection floor is quoted here or anywhere in the
   pre-seal record: `PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL
   IF REQUIRED` (§S.6). If that would not be an acceptable spend, declining now still
   costs nothing.
3. **REPAIR 3 changed what a success would be worth, and that is a feature.** Under the
   r2 semantics, a Primary that clears `M` while the specificity assessment fails is
   recorded as *a matched-clock continuation effect that happens to be measured on
   release days*, with an explicit `MECHANISM_SPECIFICITY_NOT_ESTABLISHED` label and no
   information-diffusion claim at all. That is a materially weaker prize than r1's
   wording implied, and Aaron should decide to spend the trial knowing it.

One new thing for Aaron to weigh that did not exist before PSMV: **the Good Friday
finding**. Three of the five Good Friday events are NFP releases into an abbreviated
CME session that closes at 09:15 ET. R1's prespecified rule removes them cleanly, but
it is a reminder that the 09:29 exit is a real operational assumption about session
hours, not only a modelling choice — and that a live implementation would need the same
session check the preregistration now has.

---

```
EXPERIMENTS_RUN      = NO
BACKTEST_RUN         = NO
R1_OUTCOME_INSPECTED = NO
S1_SEALED            = YES   (2026-09-17; Aaron sealed, Claude Opus executed)
S2_STARTED           = NO
```


---

## T. S1 SEAL RECORD

```
PREREG_SEALED    = YES
SEALED_BY        = Aaron (Owner)
SEAL_EXECUTED_BY = Claude Opus (Main Agent), acting under explicit Aaron
                   authorization dated 2026-09-17
SEAL_DATE        = 2026-09-17
SEAL_SCOPE       = S1 FINAL SEAL ONLY
SEALED_DOCUMENT  = this file, revision r4 -- the accepted design, unchanged
FILENAME AT SEAL = R1_S1_PREREGISTRATION_SEALED.md
                   (renamed at seal from R1_S1_PREREGISTRATION_DRAFT_UNSEALED.md;
                    a sealed preregistration must not be called a draft. The
                    content, not the path, is what the seal binds.)
```

**Aaron sealed it; Claude Opus executed the seal.** Those are two different acts
and this record keeps them apart. The delegated Owner-decision packet that fixed
OD-1…OD-7 and P-2 was a third, earlier act, and its provenance is preserved
separately and unchanged:

```
DECISION_TYPE = DELEGATED_OWNER_RULING
DELEGATED_BY  = Aaron        DECIDED_BY = Fable 5.1      ACCEPTED_BY = ChatGPT
```

**Fable did not seal this preregistration.** Fable decided the delegated packet;
ChatGPT accepted it and returned `CHATGPT FINAL PRE-SEAL ACCEPTANCE = PASS`
with `MATERIAL_BLOCKERS = 0`; **Aaron** is the authority that authorized the
seal. Aaron retains override authority over everything the packet decided.

### T.1 What the seal fixes

The sealed operative design, as it stands in the sections that define it — each
line is mechanically cross-checked against those sections and against
`R1_PREREG_MANIFEST.json` by `psmv/validate_prereg.py`:

```
EVENT FAMILY              CPI + Employment Situation / NFP, POOLED     (D.2-D.3)
INITIAL REACTION          R_init = C(08:31) - C(08:29)                 (E.1)
SIGNAL COMPLETE           08:32:00 ET                                  (E.1)
PRIMARY ENTRY REFERENCE   O(08:33)                                     (E.1-E.2)
EXIT                      O(09:29)                                     (F.1-F.2)
HOLDING PERIOD            56 minutes                                   (F.1)
MATERIALITY               k = 1,  M = $3.99 per event per 1 MNQ        (G.3)
PRE_SEAL_STRUCTURAL_N     252   (CPI 118 / NFP 134)                    (J, S)
ROLL TRANSITION EXCL.     0, measured exactly                          (S.2)
E4                        DEFERRED TO POST-SEAL S2                     (S.3)
FOMC                      UNRESOLVED / DEFERRED, never falsified       (D.1)
CROSS-ASSET PURCHASE      DECLINED                                     (H.3)
PLANNING_POWER_TABLE      TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED
```

`E4` was **not** computed during sealing. Deciding it requires comparing two bar
close prices, and no price was read at any point in the seal.

### T.2 What the seal does NOT authorize

```
S2 implementation           NOT AUTHORIZED
R1 outcome computation      NOT AUTHORIZED
R1 outcome reveal           NOT AUTHORIZED
the OD-3 power gate         NOT AUTHORIZED (post-seal S2; still not run)
Internal Validation         NOT GRANTED
Lockbox                     NOT GRANTED
experiments / backtests     NOT AUTHORIZED
parameter changes           FORBIDDEN -- the design is sealed
prereg redesign             FORBIDDEN -- see below
```

Each needs its own Aaron authorization. A sealed preregistration may be
**superseded on the record**, never quietly edited: any future change requires a
new Owner act, a new revision and a new seal, with this one preserved intact.

### T.3 Seal identity — the two-layer pattern, stated honestly

A commit cannot contain its own SHA and a file cannot contain its own digest.
The seal therefore binds in two layers, and neither pretends otherwise:

```
CONTENT_COMMIT           the commit whose tree IS the sealed content
SEAL_ATTESTATION_COMMIT  its child, which adds R1_S1_SEAL_ATTESTATION.json --
                         the CONTENT_COMMIT SHA and the sha256 of every sealed
                         file -- and changes nothing else in the sealed set
TAG                      r1-s1-sealed, annotated, carrying both SHAs
                         (the earlier r1-pre-seal tag is left untouched)
```

Both SHAs and the full digest set live in `R1_S1_SEAL_ATTESTATION.json`.
`psmv/validate_prereg.py` recomputes every digest recorded there and fails if
any sealed file has moved by a single byte, so the seal is **checkable**, not
merely declared.

### T.4 State at the seal

```
S0 = CLOSED   S1 = SEALED   PSMV = COMPLETE   S2 = NOT STARTED / NOT AUTHORIZED

PSMV_COMPLETE            = YES
PSMV_RERUN               = NO
PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY
R1_OUTCOME_CONTAMINATION = NO
P-5                      = NON_BLOCKING_RESIDUAL -- the 2025-Q1 spread proxy
                           applied to earlier pre-open history remains a
                           DISCLOSED cost-model limitation. It was deliberately
                           not resolved by a purchase at seal time.
R1_OUTCOME_EXPOSURE      = NONE       R1_TRIAL_CONSUMED = NO
SAMPLE_FORMAL_TRIAL_ORDINAL = 2       INHERITED_RESEARCHER_EXPOSURE_COUNT = 1575
PRIOR_LINEAGE            = ITSF S0-T001 (referenced by digest; never mutated)
```

**No R1 outcome exists.** None was computed, inspected or revealed, at the seal
or before it. The next possible stage is S2 BUILD, and it is not authorized by
this seal.
