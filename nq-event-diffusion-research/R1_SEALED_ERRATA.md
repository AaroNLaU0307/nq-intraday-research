# R1 SEALED ERRATA — post-seal interpretation record

```
RECORD_TYPE   = POST_SEAL_INTERPRETATION_ARTIFACT
SEALED        = NO -- deliberately OUTSIDE the S1 sealed digest set
CREATED       = 2026-09-17 (S2 BUILD)
AUTHORITY     = descriptive correction only. This file CANNOT change the sealed
                design, and nothing in the engine reads a design value from it.
SEALED_TARGET = R1_S1_PREREGISTRATION_SEALED.md, section D.3
                (CONTENT_COMMIT 46b8aef9d2471dd427db6a780435e743660a6f24)
```

The sealed preregistration is **immutable and was not edited**. Where its prose
is descriptively wrong, the correction is recorded here and the sealed text
stays exactly as Aaron sealed it. Future reports use the corrected description
and cite this file.

---

## E-1 — the structural span in section D.3

```
SEALED_TEXT                    = structural span starts 2010-06-17
                                 (section D.3 balance block:
                                  "span  2010-06-17 .. 2021-12-10")
CORRECT_STRUCTURAL_DESCRIPTION = first E3-eligible event is 2010-07-02;
                                 the span at PRE_SEAL_STRUCTURAL_N = 252 is
                                 2010-07-02 .. 2021-12-10
CAUSE                          = 2010-06-17 is excluded at E3 because the ADR14
                                 warm-up is unavailable: only 8 complete-390
                                 RTH days precede it, against the 14 required.
                                 The sealed record states this itself, twice --
                                 the D.3 exclusion table and section S.1. The
                                 span line carried the E2-population start into
                                 an n = 252 block.
MATERIALITY                    = DESCRIPTIVE_ONLY
CHANGES_EVENT_MEMBERSHIP       = NO
CHANGES_PRE_SEAL_STRUCTURAL_N  = NO
CHANGES_PRIMARY_DESIGN         = NO
CHANGES_SEAL                   = NO
```

**Evidence, mechanical.** `r1.events.build_universe`, run against the frozen F10
calendar and the sealed PSMV artifact, reproduces `n = 252` / CPI 118 / NFP 134
exactly, and its first kept event is **2010-07-02**. The sealed per-year row
agrees independently: 2010 carries **11** events, which is the twelve CPI and
NFP releases from July to December minus the 2010-10-15 FOMC coexistence. A
span beginning 2010-06-17 would require twelve.

**Nothing operative reads the span line.** No rule, threshold, count,
eligibility test or statistic consumes it. `n`, the funnel, the balance table
and every sealed constant are unaffected — which is exactly why this is an
erratum and not a reason to supersede the seal.

---

## How this file is bound

The errata digest is carried in the **run identity** as a post-seal
interpretation artifact, alongside — and clearly distinct from — the sealed
identity:

```
CONTENT_COMMIT           the sealed research content        (immutable)
SEAL_ATTESTATION_COMMIT  the attestation to it              (immutable)
S2_BUILD_COMMIT          implementation identity            (mutable, versioned)
SEALED_ERRATA_SHA256     this file                          (post-seal, additive)
```

It is **not** part of the historical S1 sealed digest set, and adding it never
changes that set. A future erratum is a new numbered section appended here,
never an edit to an existing one.
