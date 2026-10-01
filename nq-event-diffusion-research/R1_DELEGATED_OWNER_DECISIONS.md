# R1 — DELEGATED OWNER DECISION RECORD

```
DECISION_TYPE = DELEGATED_OWNER_RULING
DELEGATED_BY  = Aaron
DECIDED_BY    = Fable 5.1
ACCEPTED_BY   = ChatGPT
RECORDED_BY   = Claude Opus 5 (Main Agent / builder seat), 2026-09-17
PACKET_STATUS = PASS / CLOSED
SCOPE         = the bounded R1 pre-seal Owner-decision packet: OD-1 … OD-7, P-2
```

**Provenance, stated exactly and not paraphrased.** Aaron **delegated** this
bounded decision packet. **Fable 5.1 decided** it. **ChatGPT reviewed and
accepted** the delegated ruling. These are **not** Aaron personally authoring
each scientific selection, and this file must never be cited as though they
were. **Aaron retains override authority over every line below.**

---

## OD-1 — DATA AUTHORITY

```
RULING = GRANT
```

**Granted, for R1 only:**

| asset | identity |
|---|---|
| existing NQ Development OHLCV | `NQ.v.0 ohlcv-1m`, 2010-06-06 → 2022-01-01 exclusive; job `GLBX-20260727-DL3BEBCHJA`; manifest `d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8` |
| frozen F10 CPI/NFP event calendar | `gate1/f10_event_calendar/f10_events.csv`, sha256 `5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c` |
| derived spread-cost table | `spread_cost_table.csv` (the derived per-minute table only, never raw BBO) |

**NOT granted:**

```
Internal Validation (2022-01-01 → 2025-07-01)   NOT GRANTED — and not on this machine
Physical Lockbox    (2025-07-01 → )             NOT GRANTED — and not on this machine
protected ITSF outcome artifacts                NOT GRANTED
```

The ITSF `RoleError` fail-closed boundary is inherited unchanged. R1 adds
nothing to it and relaxes nothing in it.

---

## OD-2 — SECOND TRIAL ON THE DEVELOPMENT SAMPLE

```
RULING     = ACCEPT
ACCOUNTING = SEPARATE R1 LINEAGE / SEPARATE R1 TRIAL REGISTRY
```

**Permanent disclosures, carried in every R1 output:**

```
· this is formal trial #2 on the NQ Development sample
· inherited researcher_exposure_count = 1575, carried as the CONSERVATIVE
  DISCLOSED UPPER BOUND
· the prior ITSF registry remains UNTOUCHED
· R1 may reference the ITSF lineage by identity/hash and must NOT mutate it
```

**No new multiple-testing correction was invented under this task.** The
authoritative charter requirement (`PROJECT_CHARTER.md` clause 13 — raw exposure
reported in full as a conservative upper bound; a correlation-adjusted `N_eff`
derivation, or a correction suited to correlated candidates, to be
preregistered; counting only surviving versions forbidden) is **preserved
exactly**. The raw exposure facts are recorded in `R1_TRIAL_REGISTRY.md`; any
statistical adjustment is deferred to the already-accepted preregistration and
statistical plan.

---

## OD-3 — PRE-REVEAL POWER GATE

```
RULING = ACCEPT
```

The gate is part of the **future sealed protocol**. It was **NOT run**, and
**PSMV did not compute control dispersion, `s_hat`, `SE_hat` or any MDE.** It
executes in S2, after the seal, and before any R1 outcome is read.

---

## OD-4 — MATERIALITY

```
RULING = k = 1        (OPTION A)
THEREFORE  M = 1 x C_base_RT
```

Using the accepted Base cost definition — median spread + 1 tick per side at
R1's own entry (`08:33`) and exit (`09:29`) minutes, plus the conservative
`$1.74` platform fee per round turn — `C_base_RT = $3.99` per 1 MNQ, so

```
M = $3.99 per event per 1 MNQ   ( = 2.00 NQ index points )
```

Correct interpretation, per the repaired algebra: `Y_net ≥ k·C_base` is
equivalent to `gross ≥ (k+1)·C_base`, so **`k = 1` breaks even if the true
round-turn cost is up to 2× Base.**

`k = 1` was recorded in the preregistration **before any PSMV output was
interpreted**, and it may never be recomputed from data (prereg §C.3,
invariant L-8).

---

## OD-5 — PROJECT HOME

```
RULING = OPTION A
```

A new project at
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\nq-event-diffusion-research`,
carrying only the minimum vNext structure R1 needs. ITSF governance is **not**
cloned; QROS / L6 / reviewer machinery is **not** copied; the parked ITSF
repository is **not** modified. ITSF assets are reused by **digest-pinned
read-only reference**, and ITSF frozen logic by **transcription validated
against ITSF's own published preflight figures**, never by importing or
executing ITSF code.

---

## OD-6 — CROSS-ASSET

```
RULING = DECLINE_PURCHASE
```

No ES purchase, no rates purchase. **No cross-asset covariate enters R1.**

---

## OD-7 — FOMC

```
RULING = CONFIRM_DEFER
FOMC   = UNRESOLVED / DEFERRED
REASON = historical timestamp integrity / different event structure
```

**FOMC is NOT falsified and NOT rejected.** 45 of the 92 scheduled statement
days in the Development window (all of 2010–2015) carry no official release time
in any archived Fed source, and ITSF IR-17 (`APPROVED_BY_AARON 2026-07-29`)
forbids backfilling from typical times, news wires or third-party calendars and
bars time-level use of those rows. Nothing in R1 speaks to post-FOMC diffusion
in either direction.

---

## P-2 — REACTION WINDOW AND TIMING

```
RULING = OPTION A   (fixed design; no alternative timing arm; no scan)
```

```
P_pre                    = C(08:29)
R_init                   = C(08:31) - C(08:29)
SIGNAL_COMPLETE          = 08:32:00 ET
PRIMARY_ENTRY_REFERENCE  = O(08:33)
EXIT                     = O(09:29)
```

`R_init` and its sign were **not computed during PSMV** — they require price
values, which invariant L-13 forbids pre-seal.

---

## Standing limits on this record

This ruling closes the bounded pre-seal decision packet. It does **not**:

* seal S1;
* authorize S2;
* authorize the R1 outcome engine, any return, sign, P&L or statistic;
* authorize the OD-3 power gate to run;
* authorize any reveal;
* grant Internal Validation, Lockbox or protected-ITSF-outcome access.

Aaron alone seals, and Aaron alone may override any line above.
