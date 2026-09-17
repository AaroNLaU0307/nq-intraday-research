# R1 TRIAL REGISTRY

```
RECORD_TYPE = TRIAL_REGISTRY (append-only event chain)
LINEAGE     = R1 — Scheduled-Release Information-Diffusion Continuation
AUTHORITY   = OD-2 (delegated Owner ruling 2026-09-17): SEPARATE R1 LINEAGE /
              SEPARATE R1 TRIAL REGISTRY
```

**Rules, inherited unchanged from the existing workflow semantics.** Recorded
events are never edited or reordered; a state change is a NEW appended row with
its UTC time, actor and reason; trials are never reset, deleted or renumbered; a
failed trial is retained permanently. **Exposure is consumed at `RUN_STARTED`,
never earlier.**

---

## 1. Sample accounting — the permanent disclosures required by OD-2

```
SAMPLE                              NQ Development, 2010-06-06 -> 2022-01-01 excl
SAMPLE_FORMAL_TRIAL_ORDINAL         2
PRIOR_LINEAGE                       ITSF S0-T001
INHERITED_RESEARCHER_EXPOSURE_COUNT 1575
                                    conservative DISCLOSED UPPER BOUND, carried
                                    per PROJECT_CHARTER.md clause 13
R1_OUTCOME_EXPOSURE                 NONE
R1_TRIAL_CONSUMED                   NO
```

**No new multiple-testing correction was created here.** Clause 13 is preserved
exactly as written: raw exposure is reported in full as a conservative upper
bound; a correlation-adjusted `N_eff` derivation (or a correction suited to
correlated candidates) is to be **preregistered**; counting only the surviving
versions is forbidden. The raw facts are above. The statistical adjustment
belongs to the accepted preregistration and statistical plan, not to this file
and not to this task.

### The prior lineage, referenced by identity and never mutated

```
ITSF registry path   C:\Users\Aaron\quant-data\itsf-registry\ops\TRIAL_REGISTRY.md
ITSF registry sha256 b964b19a6b788bf9f47d1d24018dfc93836f74cbfd7ef69e4680471368d11fe9
                     VERIFIED UNCHANGED 2026-09-17 — identical to the value ITSF
                     PROJECT_STATE.md records at its park. R1 read it; R1 did not
                     write to it, and no R1 process opens it for writing.
ITSF repository      not modified by this project (worktree clean at 11725fb)
```

---

## 2. R1 event chain

| # | utc | event | actor | detail |
|---|---|---|---|---|
| 1 | 2026-09-17 | `TRIAL_REGISTERED` | main agent | `R1-T001` registered. Status `PREREG_DRAFT_UNSEALED`. Not authorized, not started, exposure NOT consumed. |
| 2 | 2026-09-17 | `DELEGATED_OWNER_PACKET_CLOSED` | Aaron (delegated) → Fable 5.1 (decided) → ChatGPT (accepted) | OD-1…OD-7 and P-2 ruled. See `R1_DELEGATED_OWNER_DECISIONS.md`. This row is **not** a run authorization. |
| 3 | 2026-09-17 | `PSMV_EXECUTED` | main agent | S1 pre-seal mechanical validation complete under invariant L-13. Structural read only. **Exposure NOT consumed; the R1 trial is NOT consumed by PSMV.** Artifacts and digests in §3. |
| 4 | 2026-09-17 | `PSMV_SCOPE_RECORD_REPAIR` | main agent, on review (`PSMV_SCIENTIFIC_INTEGRITY = PASS`, `PSMV_AUTHORITY_COMPLIANCE = HOLD / BOUNDED_RECORD_REPAIR`) | The PSMV record carried a deterministic MDE recalculation that exceeded the authorized PSMV output surface. Removed from the record. `PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY` · `R1_OUTCOME_CONTAMINATION = NO` · `PSMV_RERUN_REQUIRED = NO`. **No data process re-run, no artifact modified, no exposure consumed.** |
| 5 | 2026-09-17 | `PREREG_MANIFEST_ADDED` | main agent | P-7 closed: `R1_PREREG_MANIFEST.json`, the smallest structured companion that validates mechanically, cross-checked by `psmv/validate_prereg.py`. The manifest is **not** authoritative. |
| 6 | 2026-09-17 | `VERSION_CONTROL_INITIALISED` | main agent | P-8 closed: the project is now a standalone local git repository (OD-5 = OPTION A implementation; no remote, nothing pushed). `PRE_SEAL_PROJECT_COMMIT` in §4. **This is NOT a seal and NOT a sealed commit.** |

<!-- Append below this line only. Nothing above may be altered once committed. -->

**Still not appended, and each requires its own authority:** `PREREG_SEALED`
(Aaron only) · `S2_BUILD_STARTED` (after the seal) · `RUN_AUTHORIZED` (Aaron
only) · `RUN_STARTED` (**the row that consumes exposure**) · `POWER_GATE_REPORTED`
(OD-3) · `REVEAL_AUTHORIZED` (Aaron only) · `COMPLETED`.

---

## 3. PSMV artifact identities

```
PSMV_STRUCTURAL_REPORT.json   df0242bad6e2a1e2eb6ad1c412f91ffc1d9d421ef036ea802f7fd382e68aef47
PSMV_PURITY_ATTESTATION.json  67e13b1770d1895084c2a989fb8c67e5692b1888f11d3c21cd464cdb7f546c7e
psmv/psmv_structural.py       f3f582a19578ba8718f737ca1180971fb1b772a1de329467baa2889c9fcb2b9c
psmv/psmv_purity_guard.py     c53b4acc929acddfec0850e10115c2dfe4af21931afcd9b25e69a8e55ca44f2e
psmv/validate_prereg.py       7bb0a8b51fda041a86ef38560749cf4f4833029182d9e53bab4dea94a5fb75a0
```

### Input identities verified before use

```
NQ Development ohlcv-1m   139 files, each SHA-256-verified against the vendor
                          manifest.json before decode (fail closed)
files digest roll-up      320b12c4c376acd165f67176dcfb0dc03d2fbd6f74fd872dc3e6912c9577d7f1
f10_events.csv            5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c
nq_v0_mapping.csv         85a32d44994b51e004e0c322510527aae18b70e1fadc70437e754253a2ac1850
calendar source           pandas_market_calendars CME_Equity, 2010-06-06..2021-12-31
```

### Transcription validated by reproduction

R1 transcribes four pieces of ITSF frozen logic rather than importing ITSF code.
The transcription is not asserted — it is **checked by reproducing every
published figure** in ITSF's own `S0_INPUT_PREFLIGHT_REPORT.md` and
`DATA_QA_ADDENDUM.md`, from the data, independently:

| quantity | ITSF published | R1 PSMV measured | match |
|---|---|---|---|
| total 1-minute bars decoded | 3,848,635 | 3,848,635 | ✔ |
| L0 scheduled trading days | 2,989 | 2,989 | ✔ |
| zero-bar days | 20 | 20 | ✔ |
| L1 observed RTH days | 2,969 | 2,969 | ✔ |
| scheduled early-close days removed | 85 | 85 | ✔ |
| L2 regular full-session candidates | 2,884 | 2,884 | ✔ |
| RTH missing > 10 % days | 2 | 2 | ✔ |
| L3 structurally eligible days | 2,882 | 2,882 | ✔ |
| ADR14 warm-up days | 14 | 14 | ✔ |
| L4 final feature-construction dates | 2,868 | 2,868 | ✔ |
| complete 390-bar RTH days | 2,870 | 2,870 | ✔ |
| roll transitions | 47 | 47 | ✔ |
| `is_roll_window` days | 235 | 235 | ✔ |
| duplicate RTH minutes | none | none | ✔ |

Thirteen independently reproduced figures, zero discrepancies. This is
**mechanical evidence** that R1's transcribed funnel, ADR14 basis and roll
mapping behave identically to the frozen ITSF logic — it is not a builder claim,
and it is not independent verification of the frozen logic itself.

---

## 4. Post-PSMV record identities — the record repair of 2026-09-17

**Section 3 is frozen.** It records the identities as they stood when PSMV
executed, and nothing may edit it. This section records what changed *after*
PSMV, and what did not.

### Unchanged — verified by recomputation, not asserted

```
artifacts/PSMV_STRUCTURAL_REPORT.json   df0242bad6e2a1e2eb6ad1c412f91ffc1d9d421ef036ea802f7fd382e68aef47
artifacts/PSMV_PURITY_ATTESTATION.json  67e13b1770d1895084c2a989fb8c67e5692b1888f11d3c21cd464cdb7f546c7e
psmv/psmv_structural.py                 f3f582a19578ba8718f737ca1180971fb1b772a1de329467baa2889c9fcb2b9c
psmv/psmv_purity_guard.py               c53b4acc929acddfec0850e10115c2dfe4af21931afcd9b25e69a8e55ca44f2e
```

Both PSMV artifacts still hash to their §3 values. `psmv/validate_prereg.py`
recomputes them on every run and fails if either has moved, so "the repair
touched prose only" is a **mechanical fact**, not a claim. The repair could not
have removed an MDE from the artifacts in any case: they never contained one,
because a float leaf is exactly what invariant L-13 forbids.

### Changed after PSMV — prose and validator only

```
R1_S1_PREREGISTRATION_DRAFT_UNSEALED.md  r4  5dfa029dfd02ae61a649c4c7a93cbf42923873997645c3648c253632c1a18c2e
psmv/validate_prereg.py                  r4  961e3530eafdab730a4f8d3eb26286f24d6693249bbd2968dfb12db6bd486f1b
```

The r4 preregistration removes the recalculated MDE table, the two numeric
detection-floor lines and the conclusions drawn from them; preserves the
prospective form and its declared assumptions; records
`PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED`;
and closes P-7 and P-8. The r4 validator **removes** the four MDE entries from
its own hypothetical-exclusion set, so a numeric MDE anywhere in the pre-seal
record is now a failure rather than an allowlisted planning figure.

### Not pinned here, and why

`R1_PREREG_MANIFEST.json`, `PROJECT_STATE.md` and this registry each carry
`PRE_SEAL_PROJECT_COMMIT`, so each is finalised by the commit that records it. A
digest written here would be stale the moment it was written. **From that commit
onward git is their integrity record** — which is precisely what P-8 existed to
provide.

```
PRE_SEAL_PROJECT_COMMIT = PENDING
IS_SEALED_COMMIT        = NO
```
