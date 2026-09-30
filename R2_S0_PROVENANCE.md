# R2 — S0 PROVENANCE RECORD

```
RECORD_TYPE   = S0_PROVENANCE
LINEAGE       = R2
CREATED       = 2026-09-18
STAGE         = S0 / DATA FEASIBILITY — PRE-S1
STATUS        = PROVENANCE ONLY — this file decides nothing and authorizes nothing
```

## 1. Where R2 came from

R2 is one of the parallel candidates from the closed S0 narrowing recorded in
`../nq-event-diffusion-research/R1_S0_PROVENANCE.md` §2, where its disposition is:

> **R2** — **RESEARCH, conditional on separate data feasibility**

That table also carries its own prohibition, which this record repeats: *"A `PARK`
is not a negative finding. Nothing in this table may be cited as evidence about any
candidate's merit."* The same applies to R1's own disposition.

## 2. What R2 is

```
R2 = leveraged-ETF daily-reset / rebalancing pressure transmitted to tradeable
     index futures, candidate tradeable market primarily Nasdaq-100 / NQ / MNQ
```

The intended mechanism, stated so it cannot be quietly widened:

1. daily-reset leveraged and inverse ETFs must re-strike their benchmark exposure
   as the trading day evolves, because they promise a multiple of the **daily**
   benchmark return;
2. aggregate predicted reset demand may create a mechanically predictable late-day
   footprint;
3. that footprint may transmit into index futures.

**R2 is NOT generic late-day momentum.** A rule of the form
`positive day -> buy late / negative day -> sell late` is not R2 and may never be
substituted for it. R2 is scientifically meaningful only if the footprint varies
materially with point-in-time *fund* characteristics — assets/NAV/shares, target
leverage, fund existence, benchmark identity, mandate, reset mechanics, relative
market scale — rather than being a deterministic transform of the same-day index
return. Return sign alone is invalid.

## 3. What this stage is

An **outcome-blind data-feasibility study only**. Its single question is:

> does the data required to study R2 correctly actually exist and is it obtainable?

It does not test alpha, does not inspect any NQ outcome relationship, does not write
a preregistration, does not choose a trading rule, does not optimize timing, and
does not purchase anything.

## 4. Relationship to R1

R1 is **closed and is not reopened**. No R1 outcome, P&L, confidence interval, event
behaviour or verdict was read, and none may be used to motivate, strengthen or
handicap R2. R1 is relevant here only as *workflow precedent* (how a lineage is
staged and sealed) and as the holder of the existing NQ data grant, which R2 does
not inherit.

## 5. Material chain of this record

```
Aaron (Owner) — task: R2 outcome-blind data feasibility only
        |
        v
Claude Opus 5 (Main Agent / builder), fresh top-level session, 2026-09-18
        · read QUANT_WORKFLOW_VNEXT
        · searched the workspace: no R2 project existed
        · wrote R2_MINIMUM_DATA_CONTRACT *before* judging availability
        · audited local data, then public data, then paid options
        · verified the reset-demand equation against two credible sources
        · measured fund-side signal identifiability using fund data only
        |
        v
R2_FEASIBILITY_REPORT.md  — classification + bounded Owner decisions
```

No independent reviewer was dispatched. Under `QUANT_WORKFLOW_VNEXT` §4 this stage
is not one of Astra's two normal appearances and no named trigger fired; §2's S0
Fable seat is a *constructive design* seat and no design question was open. If Aaron
wants an independent challenge of this feasibility finding before S1, that is his
call, not an automatic gate.

## 6. What this record is not

It is not a design, not a hypothesis, not a review, not an authority. Where it and
`R2_FEASIBILITY_REPORT.md` disagree, the report wins.
