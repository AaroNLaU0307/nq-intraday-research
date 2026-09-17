# R1 — S0 PROVENANCE RECORD

```
RECORD_TYPE   = S0_PROVENANCE
PURPOSE       = make the R1 lineage understandable WITHOUT chat history
CREATED       = 2026-09-17
CLOSES        = PRE_SEAL_OPEN_ITEM P-1
STATUS        = PROVENANCE ONLY — this file re-opens nothing and decides nothing
```

**This is a record of a completed S0, not a new S0 review.** It does not
re-argue any candidate, does not add evidence, and does not change any
disposition. It exists because the S0 work happened in model sessions whose
artifacts were never written into this workspace, and a lineage that cannot be
reconstructed from bytes is not reproducible.

## 1. The material chain

```
Fable 5.1 constructive scouting
        mechanism / factor / feature candidate generation
            |
            v
ChatGPT compression
        candidate set reduced to a comparable frame
            |
            v
GPT-6 Astra, effort XHIGH — narrowing and adversarial challenge
        identification, data feasibility and mining-risk challenge
            |
            v
Fable 5.1 concurrence
        agreement on the surviving framing and its binding constraints
            |
            v
ChatGPT synthesis
        the twelve S0 constraints carried into S1 as binding inputs
            |
            v
delegated final Owner decision process
        Aaron delegated the bounded decision packet; Fable 5.1 decided;
        ChatGPT accepted    (see R1_DELEGATED_OWNER_DECISIONS.md)
            |
            v
R1 = RESEARCH
```

**What `RESEARCH` means, restated so it is never misread:** R1 is permitted to
progress to S1 design. It does **not** mean SUPPORTED, does not mean a promising
edge was found, does not mean alpha exists, and does not authorize a backtest.

## 2. Dispositions of the parallel candidates

Recorded for lineage completeness. None of these is reopened here, and none of
them is part of R1.

| candidate | disposition |
|---|---|
| **R1** — scheduled-release information-diffusion continuation | **RESEARCH** |
| **R2** | **RESEARCH, conditional on separate data feasibility** |
| **D3** | **PARK**, with reserve rationale — held deliberately, not rejected |
| **D1** | **PARK** |
| **D5** | **PARK** |
| **D6** | **PARK** |
| **THIRD SLOT** | **EMPTY** — deliberately left unfilled |

A `PARK` is not a negative finding. Nothing in this table may be cited as
evidence about any candidate's merit.

## 3. The twelve S0 constraints carried into S1

These were accepted through the chain in §1 and are binding S1 inputs. The r3
preregistration implements each; the pointer says where.

| # | constraint | implemented in the r3 prereg |
|---|---|---|
| 1 | externally anchored events only | §D — frozen, source-hashed BLS calendar; no price-defined events |
| 2 | causal information set | §E.1, invariants L-1 / L-5 |
| 3 | executable decision point | §E.2 — entry `O(08:33)`, 60-second latency budget |
| 4 | release set fixed before outcome testing | §D.2, invariant L-6 |
| 5 | event counts / pooling predefined | §D.3, §I.2 — one pooled family, one primary test |
| 6 | cross-asset consistency optional, not automatic | §G / OD-6 — **omitted**, data absent |
| 7 | state variables are bounded covariates only | §H — four covariates, no grid |
| 8 | deseasonalisation must be causal | invariant L-5 — trailing-only baselines |
| 9 | economic materiality matters | §G.3 — `M = k × C_base_RT`, `k` fixed pre-seal |
| 10 | event-day risk matters | §R.2 — adverse-path emission, MAE disclosure |
| 11 | sample dependence matters | §I.1, §J — event-block bootstrap; regime counting |
| 12 | no assumed positive prior in NQ | §M — R1 is allowed to fail cleanly |

## 4. What this record is not

It is not an S0 packet, not a review, not a challenge and not an authority. The
operative decisions live in `R1_DELEGATED_OWNER_DECISIONS.md`; the design lives
in `R1_S1_PREREGISTRATION_DRAFT_UNSEALED.md`. Where this file and either of
those disagree, they win.
