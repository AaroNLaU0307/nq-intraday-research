# R2_DELEGATED_OWNER_DECISIONS

```
RECORD_TYPE = OWNER_AUTHORITY_RECORD
LINEAGE     = R2  (nq-letf-rebalancing-research)
CREATED     = 2026-09-20
STATUS      = ACTIVE AUTHORITY FOR R2
```

**This file is the authority record for R2's Owner decisions.** `PROJECT_STATE.md`
records *state* and points here; where the two disagree about what was decided, this file
governs and `PROJECT_STATE.md` is the defect.

**Nothing here is new.** Every ruling below was decided and accepted before this file
existed. This file persists rulings that were already in force — OD-5 and OD-6 had been
ruled but were still marked pending on disk, which the SV-1 audit flagged. It creates no
decision, widens no scope, and adds no obligation.

**Workflow authority remains `../QUANT_WORKFLOW_VNEXT.md`.** This file sits at precedence
level 1 (explicit Owner decision) for the four rulings it records, and nowhere else.

---

## 0. Provenance and the delegation chain

```
DELEGATED_BY = Aaron       (Owner; delegated the decision, did not personally rule)
DECIDED_BY   = Fable       (delegated decision seat)
ACCEPTED_BY  = ChatGPT     (acceptance check)
```

This chain applies to **all four** rulings below. It is recorded as
*delegated-and-decided through that chain*, **not** as Aaron personally selecting each
ruling. `DECIDED_BY = Aaron` is not written anywhere in this file, because Aaron did not
personally make these specific rulings.

Aaron's Owner gates under `QUANT_WORKFLOW_VNEXT` §10 are untouched by this delegation: a
real run, data access beyond an existing grant, a statistical reveal, promotion /
falsification / retirement, a material methodology change, and git push / PR / merge
remain Aaron's alone.

---

## 1. OD-1 — DATA AUTHORITY

```
OD-1 = GRANT_EXISTING_NQ_DEVELOPMENT
```

A **new R2 lineage-specific grant** over the existing local NQ Development archive
(`GLBX-20260727-DL3BEBCHJA`, `NQ.v.0`, schema `ohlcv-1m`,
`2010-06-06 → 2022-01-01` exclusive).

```
GRANT_STATUS = GRANTED, NOT YET EXERCISED
```

No file in that archive has been decoded or inspected by R2. A grant is permission to
read, not permission to run, reveal, or extend: prior data access never implies future
execution or reveal authority.

---

## 2. OD-2 — FOOTPRINT SCOPE

```
OD-2 = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY
UNIVERSE = QLD, QID, PSQ, TQQQ, SQQQ
```

```
GENERIC_MOMENTUM_SUBSTITUTE = FORBIDDEN
```

R2's distinctness must come from `K_t` / `L_t` or an equivalent magnitude/composition
channel beyond return. If that cannot be established prospectively, **PARK R2**.

---

## 3. OD-5 — FUND SIZE PATH

```
OD-5                = DECIDED
R2_FUND_SIZE_PATH   = PATH_A_TRUE_PIT_DAILY
OD5_STATUS          = ACCEPTED_DELEGATED_OWNER_DECISION
```

### Meaning

R2 requires a **daily fund-size representation with true historical point-in-time
availability evidence**.

**Today's completed historical AUM file is insufficient as PIT proof.** The file is
complete and internally consistent now; that is a statement about the current artifact,
not about what was knowable on any historical date. It preserves no record of when each
row was added.

### Paths not selected

**PATH_B — slow causal state.** Not selected. Stated correctly: PATH_B would **materially
weaken daily creation/redemption and composition information and introduce substantial
stale/trend confounding**, so it was not selected for the first formal R2 lineage.

> Explicitly **not** persisted, and not to be reintroduced: any claim that PATH_B
> mathematically contains *zero* composition information. That overstatement is withdrawn.
> PATH_B is a weaker instrument, not an empty one, and it remains available to a later
> lineage should Aaron want it.

**PATH_C — PARK.** Remains the **fallback** if source verification is ultimately
exhausted unsuccessfully. See §5 for the trigger, which is evidentiary and not calendar-based.

### What OD-5 does *not* decide

OD-5 fixes the **kind of fund-size representation R2 requires**. It does not fix the
sample boundary. If future source verification yields only **partial** PIT coverage, an
**additional explicit S1 SAMPLE-ELIGIBILITY / SAMPLE-BOUNDARY rule will be required under
OD-5**. That is a rule made *under* this decision, not a reopening of it.

```
OD-5 IS DECIDED AND IS NOT TO BE REOPENED.
SAMPLE WINDOW UNCHANGED: 2010-06-06 -> 2022-01-01 exclusive.
R2_SAMPLE_EXTENSION_DECISION = DEFERRED
POST_2022_SAMPLE_TIER        = UNASSIGNED
```

---

## 4. OD-6 — STALENESS POLICY

```
OD-6                 = DECIDED
R2_STALENESS_POLICY  = PROVEN_PUBLICATION_ONLY_ZERO_CARRY
OD6_STATUS           = ACCEPTED_DELEGATED_OWNER_DECISION
```

### The eligibility rule

For a future S1 decision date `t`, fund `i` is eligible **only if the source proves the
original-vintage value for `t-1` was available before the eventual S1 decision time**.

**No proof ⇒ INELIGIBLE.**

### Core rules — all ten binding

```
 1. UNPROVEN availability = INELIGIBLE.
 2. No forward-fill.
 3. No interpolation.
 4. No imputation.
 5. No neighbouring-date inference.
 6. No partial-universe K_t.
 7. All point-in-time universe members required.
 8. A row published too late for date t does not enter date t.
 9. A later backfill does not retroactively make date t eligible.
10. The eligibility table must be built and FROZEN **before** any NQ outcome decode.
```

### Notes that are part of the ruling

- Rules 6 and 7 together mean a date on which **any one** of the five funds lacks proven
  availability yields **no `K_t` at all** for that date. There is no reduced-universe
  fallback.
- Rule 9 is what the observed **2016-04-01** episode requires: the published batch did not
  run that day, and the row was back-filled at least ~2.5 days later. Today's file carries
  that row; under rule 9 it does **not** thereby become eligible for 2016-04-01.
- Rule 10 is an outcome-blindness invariant, not a convenience. The eligibility table is
  frozen first; the NQ archive is decoded after.

### What OD-6 does not do

OD-6 is the **rule**. It is not the table. No eligibility table exists, and building one
requires a source that can evidence availability — which SV-1 found is not yet verified.

---

## 5. PATH_C PARK — the trigger, stated correctly

```
PATH_C_PARK_TRIGGER = NO      (current state)
```

**The trigger is evidentiary:**

> If the bounded source-verification / enquiry process is **CLOSED** with **no qualifying
> source** and **no material candidate remaining**, then `PATH_C_PARK_TRIGGER = YES`.

A project-management deadline may exist operationally, but **it is not scientific
evidence** and does not by itself trigger PARK. An arbitrary calendar date is not a
finding.

At present the process is **open**: several `PLAUSIBLE_UNVERIFIED` candidates remain and
none has been asked. See `R2_SV1_SOURCE_VERIFICATION_REPORT.md` and
`R2_SV1_VENDOR_ENQUIRY_PACKET.md`.

---

## 6. Current authority summary

| ruling | value | status |
|---|---|---|
| OD-1 | `GRANT_EXISTING_NQ_DEVELOPMENT` | ACCEPTED — granted, not exercised |
| OD-2 | `NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY` | ACCEPTED |
| OD-5 | `PATH_A_TRUE_PIT_DAILY` | **ACCEPTED_DELEGATED_OWNER_DECISION** |
| OD-6 | `PROVEN_PUBLICATION_ONLY_ZERO_CARRY` | **ACCEPTED_DELEGATED_OWNER_DECISION** |

```
R2_S0_DATA_FEASIBILITY = CLOSED
R2_S1_AUTHORIZED       = NO
R2_OUTCOME_EXPOSURE    = NONE
TRIAL_CONSUMED         = NO
R2_DATA_ACQUISITION_DECISION_REQUIRED = YES
PAID_PURCHASE_REQUIRED                = UNKNOWN / CONDITIONAL
```

**A separate S1 DESIGN authorization has not been issued and is not implied by anything
in this file.** OD-3 and OD-4, as drafted in `R2_FEASIBILITY_REPORT.md` §12, are not
recorded here because they were not ruled; OD-4 in particular was conditional on
`OD-2 = (b)`, which was not selected.
