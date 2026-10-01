# R2_MINIMUM_DATA_CONTRACT

```
RECORD_TYPE = PROSPECTIVE_DATA_CONTRACT
LINEAGE     = R2
CREATED     = 2026-09-18
STAGE       = S0 / DATA FEASIBILITY - PRE-S1
```

**Written before availability was judged.** This document states what R2 *would
need* to reconstruct an economically meaningful daily reset footprint without
look-ahead. It is deliberately free of any statement about what exists. Availability
is judged separately in `R2_DATA_SOURCE_AUDIT.md`, and the two are compared in
`R2_FEASIBILITY_REPORT.md`.

It is a **contract, not a design**. It fixes no entry time, no exit time, no
threshold, no bucket, no regression, no scaling, no cost rule and no hypothesis
test. Those belong to S1.

---

## 0. Notation and the decision point

```
t             a trading date
tau           a candidate intraday decision time on date t, ET, NOT chosen here
i             a fund
N_t           the set of funds in the mechanism universe on date t
m_{i,t}       fund i's target daily leverage multiple applicable on date t
A_{i,t-1}     fund i's net assets as at the close of t-1
r_pre_t       the benchmark return from the close of t-1 to tau on date t
L_t           a point-in-time tradeable-liquidity denominator, known by tau
```

`tau` is written symbolically on purpose. The only thing this contract may say about
it is a *constraint*: no input may enter the signal at `tau` unless it was published
before `tau` (section 6).

---

## 1. FUND IDENTITY - a point-in-time universe

R2 needs, for every date in the research sample, the set of funds that **existed and
were operating on that date**, not the set that exists today.

Required per fund:

| field | why R2 needs it |
|---|---|
| ticker | joins to market data |
| stable fund identifier (SEC Series ID, CUSIP/LEI, vendor permanent id) | tickers are reused and reassigned; a ticker is not an identity |
| issuer | mandate and disclosure provenance |
| benchmark index | determines which `r_pre` applies to the fund |
| target leverage multiple | enters the demand equation directly (section 2) |
| reset frequency | **daily-reset only**; monthly/weekly-reset vehicles are a different mechanism and must be excluded, not aggregated |
| effective launch / commencement-of-operations date | a fund contributes nothing before it operates |
| closure / liquidation / delisting date | a fund contributes nothing after it stops |
| benchmark or leverage **mandate-change** history | a mandate change splits one ticker into two economic objects |

**Ticker history alone is not sufficient.** Where identity changed - ticker change,
merger, reorganisation, benchmark substitution, leverage re-designation - the
reconstruction must treat the pre- and post-change object as distinct, or state
explicitly why the change is immaterial to `m(m-1)A`.

**Survivorship is a hard requirement, not a refinement.** A universe restricted to
funds alive today is disqualifying: leveraged and inverse products close at a high
rate, closures cluster after large adverse benchmark moves, and a survivor-only
universe therefore removes fund capital exactly in the states where the footprint
would be largest.

**Registered-but-never-launched series** are harmless if and only if they are
carried with `A = 0`; they are *not* harmless if their registration is mistaken for
operation and an assets figure is imputed to them.

---

## 2. TARGET LEVERAGE - point-in-time mandate

For each `(i, t)` R2 needs `m_{i,t}`: the leverage objective **applicable on that
date**, drawn from the document that was in force on that date.

Admissible values include `+2, +3, -1, -2, -3`, and R2 must not assume the set is
closed - `+1.25`, `+1.75`, `+4`, `-4` products exist in the wider family.

**Today's mandate may not be projected backwards.** Where an issuer changed a fund's
multiple, the change date governs. The authoritative statement of `m_{i,t}` is the
prospectus / post-effective amendment in force at `t`, because that is the document
that legally bound the fund's rebalancing on that date.

---

## 3. PRIOR-KNOWN FUND SIZE

R2 needs a fund-size quantity that was **knowable before `tau` on date t**. The
contract accepts any one of:

- prior-close total net assets / AUM, `A_{i,t-1}`;
- prior-close NAV times prior-close shares outstanding;
- another identity-safe equivalent whose publication timing is documented.

Hard prohibitions:

- **no value first published after `tau`** may enter the live signal, unless
  publication timing positively proves it was knowable by `tau`;
- **no backfilling of today's fund size into history**;
- **no restated vintage treated as the original vintage** without a statement of the
  restatement risk. A file downloaded today is a *current-vintage* file; that it
  agrees with what was published on `t-1` is an assumption until evidenced.

Same-day intraday creations and redemptions change true exposure within day `t`.
They are **not** knowable at `tau` and must be excluded from the live signal - their
omission is part of the mechanism's noise, not a defect to be repaired with
hindsight.

---

## 4. SHARES AND CORPORATE ACTIONS

R2 must determine, for each of the following, whether reconstruction needs it and
how it is handled with no look-ahead:

| event | handling requirement |
|---|---|
| shares outstanding | needed only if `A` is reconstructed as NAV times shares; if `A` is published directly, shares are a cross-check |
| forward / reverse splits | **`A` must be split-invariant.** Per-share quantities (NAV) and share counts are not. A retroactively split-adjusted NAV or share-count series is look-ahead-contaminated for any per-share use |
| distributions | reduce NAV, not exposure-relevant assets, at the ex-date; must not be mistaken for redemptions |
| launches | fund enters the universe at commencement of operations, not at registration |
| closures / liquidations | fund leaves the universe at the last date it held exposure; the run-off period, when a closing fund unwinds, is a distinct state and must be flagged, not silently treated as normal operation |
| mergers | the surviving object's assets are not the sum of histories; treat as a new object or document why not |
| ticker changes | resolve on the stable identifier, never on the ticker |

The contract's preferred form is: **use a directly published, split-invariant assets
series; use shares outstanding only as a consistency check, never as the primary
path, unless the shares series is verified un-adjusted.**

---

## 5. RESET-DEMAND MECHANICS - the equation, symbolically

A daily-reset fund holds benchmark exposure `S_{i,t} = m_{i,t} A_{i,t}`. If the
benchmark moves by `r` over the day, the fund's assets become
`A_{i,t}(1 + m_{i,t} r)` while its existing exposure becomes `m_{i,t} A_{i,t}(1+r)`.
To re-strike the promised multiple it must hold `m_{i,t} A_{i,t}(1 + m_{i,t} r)`.
The required trade is the difference:

```
    dS_{i,t}  =  m_{i,t} * ( m_{i,t} - 1 ) * A_{i,t-1} * r_pre_t
```

and the aggregate footprint over a single-benchmark universe is

```
    F_t  =  ( SUM_{i in N_t}  m_{i,t}*(m_{i,t}-1)*A_{i,t-1} )  *  r_pre_t
         =  K_t * r_pre_t                                            ... (dagger)

    K_t  =  SUM_{i in N_t}  m_{i,t}*(m_{i,t}-1)*A_{i,t-1}
```

normalized for economic significance as

```
    f_t  =  F_t / L_t  =  ( K_t / L_t ) * r_pre_t
```

**Sign convention.** `dS > 0` means the fund, or its swap counterparty, must **buy**
benchmark exposure; `dS < 0` means it must **sell**. With that convention:

- `m(m-1) > 0` for every admissible multiple, i.e. for all `m` outside `[0,1]`:
  `+2 -> 2`, `+3 -> 6`, `-1 -> 2`, `-2 -> 6`, `-3 -> 12`;
- therefore **long and inverse funds rebalance in the SAME direction as the
  benchmark** and their demands **do not cancel**;
- an inverse fund's contribution to `K_t` is strictly positive, and a `-3x` fund
  contributes twice the weight of a `+3x` fund of equal assets;
- `F_t` is a function of the benchmark *change*, not its *level*.

**Verification - not asserted from memory.** This equation and the same-direction
property were checked against two independent credible sources, both of which derive
it explicitly:

- Tuzun, *Are Leveraged and Inverse ETFs the New Portfolio Insurers?*, Federal
  Reserve Board Finance and Economics Discussion Series 2013-48, section III:
  derives `S_{t+1} - S_t = r * lambda * (lambda - 1) * W_t` and states that when
  lambda lies outside `[0,1]` the rebalancing amount has the same sign as `r`, so
  inverse and leveraged ETFs rebalance in the same direction and do not cancel each
  other out. It cites Cheng and Madhavan (2009) for the same derivation.
- Mathis and Moerke, *Liquidity Provision to Leveraged ETFs and Equity Options
  Rebalancing Flows*, section 2.3 equation (6): derives `L*(L-1)*A_t*r_bench` and
  states the required hedging multiple `L(L-1)` is strictly positive for `L` in
  `R \ [0,1]`, so counterparties always trade in the same direction as the index.

**Consequence that this contract must record, because it constrains R2's validity.**
Equation (dagger) **factorizes**: over a single-benchmark universe the whole
cross-sectional sum collapses to one scalar `K_t` multiplying `r_pre_t`. Therefore

```
    sign( F_t )  ==  sign( r_pre_t )        - always, by construction
```

and R2's *entire* beyond-return content lives in the magnitude modulation
`K_t / L_t`. R2 is scientifically distinct from generic late-day momentum **only if**
`K_t / L_t` carries material, non-degenerate variation that is not itself a
deterministic function of the same-day return. Establishing that this variation
exists in the obtainable data is the object of section 9 of the feasibility report.

**Mechanism caveats the contract records now, so S1 cannot forget them.** These funds
generally obtain exposure via total-return swaps and futures rather than cash equity,
so the observable is the *counterparty's* hedge, not the fund's own trade; the hedge
timing is unobservable and is an assumption, not a measurement. Any statement about
*when* within the day the demand arrives is therefore a modelling assumption that
must be declared at S1 and cannot be calibrated here.

---

## 6. CAUSAL TIMING - `AVAILABLE_BY` for every input

Every input carries an `AVAILABLE_BY` stamp. **A value available only after `tau` may
not enter the live signal.**

| input | required `AVAILABLE_BY` | note |
|---|---|---|
| fund existence on date `t` | before open of `t` | registration is not operation; a launch is knowable from the launch announcement / effectiveness |
| leverage mandate `m_{i,t}` | before open of `t` | governed by the document in force at `t`; filing dates make this verifiable |
| benchmark identity | before open of `t` | same |
| prior-close assets `A_{i,t-1}` | **before `tau` on `t`** | this is the binding constraint of the whole design; publication time must be evidenced, not assumed |
| shares outstanding `t-1` | before `tau` on `t` | only if used |
| corporate action effective on `t` | before open of `t` | issuers announce in advance; a retroactively adjusted series fails this test |
| closure / liquidation of fund `i` | before open of `t` | a fund known to be closing is in a different state |
| benchmark return `r_pre_t` | by `tau`, from data timestamped at or before `tau` | includes the latency budget to act |
| liquidity denominator `L_t` | by `tau` | must be built from data strictly before `tau`, e.g. a trailing average, never from `t`'s realised full-day volume |

Two timing traps the contract names explicitly:

- **the trailing-window trap** - any denominator, baseline or scaling built from a
  window that includes date `t`'s post-`tau` data is look-ahead, however innocuous
  it looks;
- **the vintage trap** - a historical file downloaded today may have been restated.
  Point-in-time safety requires either an archived vintage or an argued bound on
  restatement.

---

## 7. NORMALIZATION

A dollar footprint in isolation is not an economic magnitude: one billion dollars of
reset demand means one thing against a thin tape and another against a deep one, and
the scale of both the LETF complex and the futures market changed by more than an
order of magnitude over any plausible sample. R2 therefore needs at least one
**pre-specified, point-in-time, defensible** denominator `L_t`, known by `tau`.

Candidate denominator families - this contract **assesses availability only** and
chooses none:

1. NQ futures traded volume or dollar volume available by `tau`, e.g. a trailing
   average of late-session volume computed strictly from dates before `t`;
2. Nasdaq-100 underlying cash-equity liquidity - trailing dollar volume of the index
   constituents;
3. another pre-specified tradeable-liquidity proxy with a documented `AVAILABLE_BY`.

**The denominator must not be optimized.** Feasibility asks only *which defensible
causal denominators are obtainable*. Selecting among them, and fixing the trailing
window, is S1 work. If more than one is obtainable, S1 must fix one as Primary
before any outcome is touched and may use the others only as pre-declared robustness
checks.

---

## 8. What would make R2 INFEASIBLE under this contract

Recorded in advance so the conclusion cannot be reverse-engineered:

- **F-1** the point-in-time fund universe cannot be reconstructed survivorship-free,
  so `K_t` systematically loses capital in large-move states;
- **F-2** no fund-size quantity with a provable pre-`tau` `AVAILABLE_BY` exists, so
  `A_{i,t-1}` can only be had with look-ahead;
- **F-3** historical leverage mandates cannot be established point-in-time, so
  `m_{i,t}` must be assumed constant at today's value;
- **F-4** `K_t / L_t` is degenerate - effectively constant, or a deterministic
  function of the same-day return - in which case `f_t` is a monotone transform of
  `r_pre_t`, R2 collapses into generic late-day momentum, and **R2 must be parked,
  not substituted**;
- **F-5** no causal liquidity denominator is obtainable, so economic significance
  cannot be expressed without look-ahead.

Any of F-1..F-5 holding to a material degree is a feasibility failure. None of them
is a statement about whether an edge exists, and none may be reported as one.
