# R2 — G3_ACCEPTANCE_CRITERIA

```
RECORD_TYPE = ACCEPTANCE_CRITERIA
LINEAGE     = R2
GAP         = G-3  publication timing of prior-close ProShares AUM
CREATED     = 2026-09-19, BEFORE any new timing evidence was collected
STAGE       = S0 / DATA FEASIBILITY - PRE-S1
```

**Written first, on purpose.** This file fixes what would count as closing G-3 before
any new evidence exists, so the standard cannot be bent to fit whatever turns up. It
is a separate file from the evidence report for exactly that reason.

---

## 1. The question, stated precisely

NOT: *"when is day `t`'s own AUM published?"* — that is already settled and already
forbidden (the day-`t` row must not be used).

THE QUESTION:

> By what latest defensible time on trading day `t` can it be **proven** that the
> prior trading day's AUM, `A_{i,t-1}`, was publicly available?

The output is a **causal-time availability bound**, not a trading time.

---

## 2. Closure hierarchy — any ONE of these closes G-3

### LEVEL A — DOCUMENTED PUBLICATION RULE

First-party issuer documentation, or authoritative regulatory/exchange documentation
binding on the issuer, states a publication or update schedule sufficient to prove
that prior-close AUM is available before some time `T` on the next trading day.

Admissible only if the document speaks to **the quantity R2 actually uses**. A rule
governing NAV-per-share publication is *not automatically* a rule governing
total-net-assets publication; if a Level A claim rests on a NAV rule, the gap between
NAV and AUM must be stated explicitly and either bridged with evidence or the claim
downgraded.

### LEVEL B — DIRECT TIMESTAMPED RETRIEVAL EVIDENCE

A timestamped retrieval demonstrates that the `t-1` row was publicly downloadable by
a known time `T` on trading day `t`, with **enough repeated evidence or supporting
metadata to make `T` defensible**. One observation is an anecdote; `T` must survive
being wrong on any single day.

### LEVEL C — CONSERVATIVE DAILY-LAG BOUND

If no intraday time can be established, but evidence proves `A_{i,t-1}` is available
by the **opening of trading day `t`**, G-3 may close with

```
AUM_AVAILABLE_BY = NEXT_TRADING_DAY_OPEN      (or a more conservative proven bound)
```

This chooses no trading time. It only constrains S1: `tau` must be later than the
proven bound.

---

## 3. What will NOT close G-3

Fixed in advance:

- a page showing today's latest row **now**;
- a file's local filesystem modified time after download;
- browser or CDN cache time with unclear semantics;
- the server's current `Date` header without row-level meaning;
- one observation that the current day `t` is absent;
- "daily NAV data must be ready by morning";
- finance-industry convention or plausibility;
- current-AUM page snapshots with no publication history;
- inference from convenience, i.e. adopting a bound because it is the one R2 would
  like to have.

A single **weekend or holiday** observation is explicitly weak evidence for the
general claim: the Friday-to-Monday gap is the easiest possible `(t-1, t)` pair, and
what holds across a 65-hour gap does not establish what holds across a 17-hour
overnight gap. Such an observation may be recorded but may not on its own carry a
Level B or Level C closure.

---

## 4. Universe requirement

The bound must hold for the whole accepted R2 universe — **QLD, QID, PSQ, TQQQ,
SQQQ** — not for the fastest fund. If publication timing differs materially across
the five, the **latest defensible universe-wide** bound is the one that closes G-3.

---

## 5. Separation of concerns, restated

```
AUM_AVAILABLE_BY = X      does NOT mean      tau = X
```

It means only that S1 must choose `tau` strictly after the proven causal availability
bound, subject to every other mechanism constraint. **This task does not choose
`tau`, entry, exit, threshold or any signal definition**, and a bound that happens to
be convenient for some imagined rule carries no extra weight because of it.

---

## 6. The adverse outcome is a legitimate outcome

If the obtainable evidence does not reach Level A, B or C, the correct result is

```
G3_STATUS = OPEN_INSUFFICIENT_EVIDENCE
```

with an exact statement of the missing evidence. Failing to close G-3 today is a
valid result and must not be avoided by weakening the standard above.

Separately: if the proven bound turns out to be so late that no plausible pre-close
interval remains for the R2 mechanism, that is reported as

```
G3_CLOSES_DATA_TIMING_BUT_CREATES_MECHANISM_TIMING_BLOCKER = YES
```

and is **not** to be solved by redefining the signal.
