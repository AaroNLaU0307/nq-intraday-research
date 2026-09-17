# R1 — S2 BUILD REPORT

```
STAGE            = S2 BUILD
DATE             = 2026-09-17
AUTHORIZATION    = Aaron, explicit: S2 BUILD ONLY (implementation, synthetic
                   validation, invariant testing, contract binding,
                   run-readiness construction)
NOT AUTHORIZED   = the real R1 study, R1 outcome computation, the OD-3 power
                   gate, Internal Validation, Lockbox, experiments, backtests,
                   parameter changes, prereg redesign

S2_BUILD         = COMPLETE
S3_RUN           = NOT AUTHORIZED
OD3_POWER_GATE   = NOT RUN
R1_OUTCOME       = NOT COMPUTED
R1_OUTCOME_REVEAL= NOT AUTHORIZED
TRIAL_CONSUMED   = NO
```

**No real R1 result appears in this document, because none exists.** Every
number below is either a structural count already sealed at S1, a count of
code and tests, or a fabricated synthetic fixture value.

---

## 1. Sealed-contract binding

```
CONTENT_COMMIT          = 46b8aef9d2471dd427db6a780435e743660a6f24
SEAL_ATTESTATION_COMMIT = 595af1c9663eb868e9f2d72f44abfe2f426ca24d
TAG                     = r1-s1-sealed
```

`r1/contract.py` is the single source of every scientific constant. It does not
restate the sealed design from memory — it **binds** it at load time:

| what | bound to |
|---|---|
| operative design (family, entry, exit, k, n, E4 status) | `R1_S1_SEAL_ATTESTATION.json` `operative_design` |
| anchor minutes | the PSMV artifact, **cross-checked against each anchor's own label** (`C_0829` must be minute 509) |
| structural n, CPI/NFP split | the PSMV artifact **and** the attestation **and** the manifest, all three |
| cost inputs, bootstrap grammar, control and covariate parameters | verified present in the sealed preregistration text |
| RTH session structure, ADR lookback | verified present in the sealed `psmv/psmv_structural.py` |
| file identity | sha256 of all 12 sealed files, recomputed at every load |

Any mismatch raises `SealIdentityError` and the engine refuses to run. There is
no fallback path, and `verify_digests=False` exists only so a mutation test can
reach the semantic checks.

**Mutation tests — all eight required, each on a COPY of the sealed set:** k ·
event family · reaction anchors · entry time · exit time · calendar digest ·
structural n · seal identity. Plus: a single appended byte anywhere in the
sealed set, an unsealed attestation, and a manifest that disagrees with the
attestation. All refuse.

Scientific constants may live in exactly one module, and an AST scan enforces
it (`scan_no_duplicated_constants`). It found and removed a real duplication
during the build: `277` had been typed into `r1/events.py`.

## 2. Implementation inventory

19 modules, ~2,900 lines, `r1/`:

| module | task | what it is |
|---|---|---|
| `contract.py` | 1 | the sealed contract loader; every constant, bound |
| `errors.py` | — | fail-closed error types; none may be caught and defaulted |
| `roles.py` | 14 | the data-role boundary; IV and Lockbox refuse at the ROLE |
| `bars.py` | — | `Bar`/`BarSource`, the three causal windows, and the S3-blocked real source |
| `events.py` | 2 | event universe, E0→E3, reproduces n = 252 |
| `signal.py` | 3, 4 | `R_init`, `d_event`, and E4 |
| `costs.py` | 5 | the pinned ITSF cost adapter |
| `trade.py` | 5 | the sealed trade, `Y_net`, close-path and adverse-path |
| `controls.py` | 6, 7 | C1 and C2, the vol-tercile weighting, the D statistic |
| `covariates.py` | 8 | the four sealed covariates, trailing-only |
| `bootstrap.py` | 9 | the sealed stationary block bootstrap |
| `verdict.py` | 10 | both axes, every guard, the M.2 language matrix |
| `power_gate.py` | 11 | OD-3 machinery + the independence proof |
| `outcome_seal.py` | 12 | the four output classes and the reveal door |
| `invariants.py` | 13 | L-1…L-12 registry and the static scans |
| `run_identity.py` | 15 | prospective run identity and its digest |
| `pipeline.py` | — | the smallest complete engine, wired in the sealed order |
| `itsf_pin.py` | — | the pinned, read-only reference to parked ITSF |
| `../tools/validate_state.py` | — | UNSEALED current-state validator (see §10b) |

**Leakage is structural, not procedural.** Nothing reads bars directly: the
signal builder gets a `SignalWindow` (refuses ≥ 08:32), the P&L builder a
`TradeWindow` (refuses < 08:33), the covariate builder a `TrailingHistory`
(refuses the current date). L-1, L-4 and L-5 are enforced by the only object
that can reach a bar.

**Real data is unreachable.** `DevelopmentBarSource` refuses without an S3
token *before* importing a decoder or building a path; `apply_e4`, `run_primary`
and `run_study` refuse any non-synthetic source the same way.

## 3. Tests

```
203 tests, 16 files, ~2,200 lines            203 passed, 0 failed
```

Unit · property · **mutation** · synthetic integration · contract · fixture ·
static/AST · schema · hash checks. Forbidden categories were not run: no real
Primary, no real event P&L, no real E4 over the 252 events, no real C2
dispersion, no real OD-3 gate, no real bootstrap of R1 outcomes, no real
verdict.

Guards demonstrated able to fail (a guard never shown to fail is not a guard):

| guard | poisoned fixture | caught |
|---|---|---|
| sealed contract | 11 separate mutations | yes |
| L-3 release-time inference | `T = "08:30"`, `default_release_time=` | yes |
| L-8 parameter scan | `for entry_minute in candidate_entry_times`, `k = 2` | yes |
| L-8 constants home | `ENTRY = 513`, `M = 3.99` outside the contract | yes |
| L-10 raw decoder | `import databento` | yes |
| OD-3 independence proof | a module importing `TradeResult` into the gate | yes |
| C1 invariance | an arm with a different cost model / sample size | yes |

## 4. The cost adapter, cross-checked

R1 transcribes ITSF's frozen S0 §6 fill formulas rather than importing them,
because importing from a parked working tree would make R1 depend on mutable
state outside its own sealed commit. The transcription is checked two ways:

* against the **sealed G.2 table** — Base $3.99 / Conservative $5.49 /
  Stress $6.24 / Severe $6.74 all reproduce exactly from the sealed E.3 spread
  rows and the $1.74 fee;
* against **ITSF's own module**, imported read-only in a test, gated on the
  pinned sha256 of `src/itsf/s0/costs.py` and `src/itsf/contracts.py`. With
  equal per-side spreads R1 collapses to ITSF exactly.

R1's only deviation is a specialisation the sealed design requires: the entry
minute (08:33) and the exit minute (09:29) have different sealed spread
distributions, so friction is priced per side. **ITSF was not modified.**

## 5. Authority boundaries in code

```
DevelopmentBarSource      refuses without an S3 token, before any import
apply_e4 / run_primary /
  run_study               refuse a non-synthetic source without an S3 token
refuse_real_gate()        states the OD-3 boundary rather than half-running it
seal_outcome(synthetic=False)  requires an S3 token
reveal()                  requires an explicit Owner reveal token
roles.check_role          IV and Lockbox refuse at the ROLE -- no path is built
```

A test monkeypatches `open` and asserts that an IV/Lockbox request opens
**nothing** before refusing.

## 6. OD-3 isolation

Every function in `power_gate.py` takes floats and the contract. There is no
parameter anywhere in the module through which a Primary result could arrive,
and `prove_gate_independence()` walks the module's imports, AST and signatures
to prove it. `c2_dispersion()` takes a single argument — the control arm — so
the gate's input cannot be an event arm even by accident. The pipeline exposes
exactly one bridge, `power_gate_inputs_from_control(c2_arm)`.

## 7. Known limitations

1. **`DevelopmentBarSource.bars_for` is unimplemented.** Its body would be
   exercised only by a real run, which S2 may not do. It is built against the
   same `Bar`/`BarSource` contract the entire suite pins, so S3 implements one
   method and nothing else moves.
2. **The synthetic fixtures are deliberately simple.** They test the engine's
   logic, not market realism; no synthetic fixture is evidence about NQ.
3. **`vol_state` terciles use an order-statistic cut** on the trailing window.
   The sealed text says "tercile" without naming an interpolation rule.
4. **A1's median split** (sealed L) is not yet implemented as a pipeline stage;
   `a1_sign_holds` is an explicit input to the verdict engine. A1 is
   non-confirmatory and cannot create support, so this is an S3 wiring item,
   not a gap in the confirmatory path.

## 8. Implementation-level resolutions of sealed ambiguities

None changes a sealed rule; each makes an under-specified one concrete, and
each is recorded here rather than buried.

| # | sealed text | resolution |
|---|---|---|
| 1 | K.1: "if C1 also clears M" | C1 is held to the **same bar as the Primary** (95 % lower bound of its mean > M). The naive alternative (mean of draw means > M) is computed and reported beside it, never instead. |
| 2 | I.1: "percentile, 95 %" + C.2's "CI half-width" | the interval is **two-sided** percentile 95 % (2.5/97.5); a half-width only exists for a two-sided interval. The test stays one-sided as declared. |
| 3 | I.1: "seeds {7, 13, 31}" | run as a **stability set**: the primary interval pools all three seeds' resample means; per-seed intervals are reported beside it. No seed is ever chosen after seeing a result. |
| 4 | M.1: "a data-availability exclusion materially shrank n" | **not** given an invented threshold. It is an explicit input to the verdict engine, defaulting to the non-excusing value. Same for the OD-3 gate outcome. |

## 9. `SEALED_CONTRACT_CONFLICT` — one, non-blocking

```
SEALED_CONTRACT_CONFLICT = Sealed section D.3's balance block, which reports the
                           balance AT PRE_SEAL_STRUCTURAL_N = 252, ends with
                           "span  2010-06-17 .. 2021-12-10". 2010-06-17 is NOT
                           in the n = 252 population: it was removed at E3 for
                           ADR14 warm-up (8 prior complete-390 days), and the
                           sealed record says so itself, twice (D.3 exclusion
                           table and S.1). The span line is the E2-population
                           start, carried into an n = 252 block.

IMPLEMENTATION_EVIDENCE  = r1.events.build_universe, run against the frozen
                           calendar and the sealed PSMV artifact, reproduces
                           n = 252 / CPI 118 / NFP 134 exactly, and its first
                           kept event is 2010-07-02. The sealed per-year row
                           independently agrees: 2010 carries 11 events, which
                           is the 12 CPI+NFP releases from July to December
                           minus the 2010-10-15 FOMC coexistence. A span
                           starting 2010-06-17 would require 12.

MATERIALITY              = NON_BLOCKING. The span line is descriptive. No rule,
                           threshold, count, eligibility test or statistic reads
                           it; n, the funnel, the balance and every operative
                           constant are unaffected.

SAFE_ACTION              = RETURN_TO_AARON as a record note. The seal is
                           immutable and was NOT edited. If Aaron wants the line
                           corrected it needs a superseding revision and a new
                           seal -- which is disproportionate for a descriptive
                           date, hence this disclosure instead.
```

## 10. `S2_MATERIAL_BLOCKER` — the sealed trial registry cannot grow

Found by building, not by reading.

```
S2_MATERIAL_BLOCKER    = R1_TRIAL_REGISTRY.md is inside the SEALED DIGEST SET,
                         and it is also an APPEND-ONLY EVENT CHAIN that must
                         still grow: `S2_BUILD_STARTED`, `RUN_AUTHORIZED`,
                         `RUN_STARTED` (the row that CONSUMES exposure),
                         `POWER_GATE_REPORTED`, `REVEAL_AUTHORIZED`,
                         `COMPLETED`. Appending any of them changes its bytes,
                         so its sealed digest stops verifying and the contract
                         loader refuses to run the engine.

SEALED_REQUIREMENT     = the seal binds every sealed file byte-for-byte
                         (R1_S1_SEAL_ATTESTATION.json `sealed_digests`), and
                         the registry's own rules require appending a row at
                         RUN_STARTED before exposure may be consumed.

IMPLEMENTATION_CONFLICT= the two cannot both hold. Mechanically demonstrated by
                         tests/test_contract.py::test_appending_a_registry_row_
                         breaks_the_seal, which appends one row to a COPY and
                         gets SealIdentityError.

MATERIALITY            = NON_BLOCKING for S2 -- no row is due, the trial is not
                         consumed, and the engine loads and runs today.
                         BLOCKING for S3 -- the first real run must append
                         RUN_STARTED, and at that instant the engine would
                         refuse to load.

MINIMUM_SAFE_ACTION    = RETURN_TO_AARON. This was NOT repaired in
                         implementation, because every available repair changes
                         what the seal guarantees. Three options, Owner's call:
                         (a) verify the registry APPEND-ONLY -- the sealed bytes
                             must remain an exact PREFIX -- instead of
                             byte-identical;
                         (b) remove the registry from the sealed digest set and
                             pin it separately (it is a ledger, not a design
                             document);
                         (c) leave the seal alone and append future events to a
                             NEW file that references the sealed registry.
                         The seal was not edited and no workaround was coded.
```

### 10b. A second instance of the same root cause

`psmv/validate_prereg.py` is also inside the sealed digest set, and it asserts
project STATE rather than design:

```
check("state: S2 NOT AUTHORIZED", "S2 = NOT AUTHORIZED" in state)
```

That was true at seal time. Aaron authorized S2 BUILD on 2026-09-17, so it is
now false. The sealed validator cannot be updated -- editing it would break the
seal it exists to protect -- and PROJECT_STATE.md must not be made to lie in
order to satisfy it.

```
psmv/validate_prereg.py   184 passed, 1 failed   <- the expired S2 assertion,
                                                    expected and documented
tools/validate_state.py    33 passed, 0 failed   <- UNSEALED; validates the
                                                    current stage state and
                                                    re-verifies every sealed
                                                    digest
```

**Root cause, stated once for both 10 and 10b:** the sealed digest set contains
two files that are not design documents -- a ledger that must grow and a
validator that asserts stage state. Whatever Aaron rules for the registry
should cover this too. Nothing was edited to make either go away.

## 11. Remaining blockers for S3

Nothing blocks S3 **authorization**; these are what S3 must do first.

1. **Implement `DevelopmentBarSource.bars_for`** against the frozen DBN archive
   and the manifest, and pin the data-manifest sha256 into the run identity.
2. **Publish `POST_SEAL_SIGNAL_DEFINED_N` and the E4 count** as the first
   outcome-adjacent act (sealed S.3), before the power gate consumes n.
3. **Run the OD-3 gate** on real C2 dispersion and put the packet in front of
   Aaron. `PROCEED_TO_REVEAL` or `PARK_FOR_INSUFFICIENT_POWER` is his call; the
   machinery neither decides nor recommends.
4. **Wire A1** (the |R_init| median split) as a pipeline stage.
5. **Owner authorization tokens** for the real run and, separately, the reveal.
6. **Rule on the sealed-registry conflict in section 10** before the first real
   run, because `RUN_STARTED` cannot be appended until it is resolved.

---

```
REAL_E4_EVALUATED           = NO
REAL_C2_DISPERSION_COMPUTED = NO
OD3_POWER_GATE_RUN          = NO
R1_PRIMARY_OUTCOME_COMPUTED = NO
R1_OUTCOME_INSPECTED        = NO
INTERNAL_VALIDATION_ACCESSED= NO
LOCKBOX_ACCESSED            = NO
TRIAL_CONSUMED              = NO
S2_BUILD_COMPLETE           = YES
S3_STARTED                  = NO
```
