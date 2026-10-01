"""INDEPENDENT cold reducer for sealed MC atom traces (N01 / PHASE D6).

This module is the SECOND, structurally independent implementation of the
atom reduction. It exists so that no single piece of code both produces a
statistic and certifies it.

INDEPENDENCE CONTRACT (pinned by an import-graph test in
tests/test_mc_cold_replay.py):

  * it imports NOTHING from `itsf` — not the atom dataclass, not the
    canonical-JSON helper, not the schema constants, not the reduction
    functions. Standard library only.
  * it starts from the SERIALISED form (the canonical JSONL bytes), not
    from live objects, so it cannot inherit an in-memory error.
  * it shares NO expected-value-generating helper with the production
    reducer: every formula below is re-derived from the written
    specification, and the two implementations agree only because the
    specification is unambiguous — never because they call the same
    function.

Specification it re-implements (transcribed, not imported):
  - canonical JSON  : sorted keys, compact separators (",",":"), ASCII,
                      NaN/Infinity rejected;
  - atom digest     : sha256 of the atom's canonical JSON object;
  - set digest      : sha256 of the newline-joined canonical objects
                      (uncompressed, no trailing newline);
  - world mean      : sum of the world's per-phase EVs in ASCENDING PHASE
                      order, divided by the count;
  - within-world SE : sqrt(sum((x-mean)^2)/(n-1)) / sqrt(n), same order;
  - between-world SD: sample SD (ddof=1) of the world means in ASCENDING
                      WORLD order;
  - quantiles       : type-7 linear with h = (n-1) * q/100, evaluated in
                      the TWO-BRANCH order the specification fixes —
                      `a + (b - a) * t` for t < 0.5 and
                      `b - (b - a) * (1 - t)` for t >= 0.5 (N01 C5). The
                      branch point is part of the spec because the claim
                      being made is BITWISE agreement, not "same
                      estimator"; a single-expression form disagrees in
                      the last ULP on every t >= 0.5 sample.

Any disagreement with the production reducer is a REFUSAL to seal
(`reducer_disagreement`), never a reconciliation.
"""
from __future__ import annotations

import hashlib
import json
import math

COLD_REDUCER_VERSION = "itsf.mc.cold_reducer.v1"

# Transcribed (NOT imported) — a drift between these literals and the
# producer's schema strings is itself a detectable disagreement.
_ATOM_SCHEMA = "mc_simulation_path_observation.v1"
_ABSENT_TOKENS = ("NOT_APPLICABLE", "NOT_APPLICABLE_NO_TRADE",
                  "PENDING_RULING", "PENDING_ENGINEERING")
_ABSENT_FIELDS = ("contract_cap_hits", "e2_over_budget_days")


class ColdReducerError(ValueError):
    """Fail-closed refusal raised by the independent reducer."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_jsonl(text: str) -> list:
    """Parse the sealed canonical JSONL trace into plain dict rows."""
    if not isinstance(text, str):
        raise ColdReducerError("cold_trace_not_text",
                               type(text).__name__)
    rows = []
    for i, line in enumerate(text.split("\n")):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise ColdReducerError("cold_trace_unparseable",
                                   f"line {i}: {exc}") from exc
        if not isinstance(row, dict):
            raise ColdReducerError("cold_trace_unparseable",
                                   f"line {i} is not an object")
        if row.get("schema") != _ATOM_SCHEMA:
            raise ColdReducerError("cold_trace_schema",
                                   f"line {i}: schema="
                                   f"{row.get('schema')!r}")
        rows.append(row)
    if not rows:
        raise ColdReducerError("cold_trace_empty", "no atoms in trace")
    return rows


def _require_number(row: dict, name: str, i: int) -> float:
    v = row.get(name)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or \
            not math.isfinite(float(v)):
        raise ColdReducerError("cold_trace_field",
                               f"atom {i}: {name}={v!r}")
    return float(v)


def _require_int(row: dict, name: str, i: int) -> int:
    v = row.get(name)
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ColdReducerError("cold_trace_field",
                               f"atom {i}: {name}={v!r}")
    return v


def _absent_aware_sum(rows: list, name: str):
    """Sum a quantity that may be typed-absent. Mixed absence semantics
    inside one set refuse; any absence makes the whole sum absent (a 0
    would be a forgery)."""
    tokens = set()
    total = 0
    for i, row in enumerate(rows):
        v = row.get(name)
        if isinstance(v, str):
            if v not in _ABSENT_TOKENS:
                raise ColdReducerError("cold_trace_absent_token",
                                       f"atom {i}: {name}={v!r}")
            tokens.add(v)
        else:
            total += _require_int(row, name, i)
    if tokens:
        if len(tokens) > 1:
            raise ColdReducerError("cold_trace_absent_mixed",
                                   f"{name}: {sorted(tokens)}")
        return sorted(tokens)[0]
    return total


def _quantile_linear(values_sorted: list, q: float) -> float:
    """Type-7 linear quantile in the SPECIFIED two-branch evaluation
    order (see the module docstring). Transcribed from the specification,
    independently of the production implementation: the branch point at
    t == 0.5 and both expressions are written out here again rather than
    imported, which is the whole point of the second reducer."""
    n = len(values_sorted)
    if n == 0:
        raise ColdReducerError("cold_trace_empty", "empty sample")
    if n == 1:
        return float(values_sorted[0])
    h = (n - 1) * (float(q) / 100.0)
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return float(values_sorted[int(h)])
    t = h - lo
    a = float(values_sorted[lo])
    b = float(values_sorted[hi])
    if t < 0.5:
        return a + (b - a) * t
    return b - (b - a) * (1.0 - t)


def _mean(values: list) -> float:
    if not values:
        raise ColdReducerError("cold_trace_empty",
                               "mean of an empty sample is undefined")
    total = 0.0
    for v in values:
        total += float(v)
    return total / len(values)


def _sd_ddof1(values: list) -> float:
    """n == 0 is UNDEFINED and refuses; n == 1 is a genuine 0.0 (the
    ddof-1 estimator has no within-set variation to measure). Mirrors the
    production primitive's two-case discipline BY SPECIFICATION — the two
    implementations still share no code."""
    n = len(values)
    if n == 0:
        raise ColdReducerError("cold_trace_empty",
                               "sample SD of an empty sample is "
                               "undefined, not zero")
    if n == 1:
        return 0.0
    m = _mean(values)
    acc = 0.0
    for v in values:
        d = float(v) - m
        acc += d * d
    return math.sqrt(acc / (n - 1))


def _se(values: list) -> float:
    n = len(values)
    if n == 0:
        raise ColdReducerError("cold_trace_empty",
                               "standard error of an empty sample is "
                               "undefined, not zero")
    if n == 1:
        return 0.0
    return _sd_ddof1(values) / math.sqrt(n)


def reduce_trace(text: str) -> dict:
    """Reduce a sealed canonical JSONL trace to EVERY downstream number.

    Returns plain JSON-shaped data (no itsf types) so the comparison
    against the production reduction is a pure value comparison."""
    rows = parse_jsonl(text)

    # --- structure ---
    counts: dict = {}
    by_world: dict = {}
    for i, row in enumerate(rows):
        w = _require_int(row, "world_index", i)
        p = _require_int(row, "phase_offset", i)
        counts[(w, p)] = counts.get((w, p), 0) + 1
        by_world.setdefault(w, []).append(
            (p, _require_number(row, "monthly_prop_operating_ev", i)))
    dupes = sorted(k for k, n in counts.items() if n > 1)
    if dupes:
        raise ColdReducerError("cold_trace_duplicate_key", f"{dupes[:3]}")

    world_ids = sorted(by_world)
    world_means = []
    world_ses = []
    phase_keys_by_world = {}
    for w in world_ids:
        ordered = sorted(by_world[w])
        phase_keys_by_world[w] = tuple(p for p, _ev in ordered)
        evs = [ev for _p, ev in ordered]
        world_means.append(_mean(evs))
        world_ses.append(_se(evs))

    sorted_means = sorted(world_means)
    between_sd = _sd_ddof1(world_means)
    max_se = max(world_ses) if world_ses else 0.0

    # --- raw feasibility metrics (counts only; NO gate, NO threshold) ---
    n = len(rows)
    offered = sum(_require_int(r, "offered_days", i)
                  for i, r in enumerate(rows))
    payout_paths = sum(1 for i, r in enumerate(rows)
                       if _require_int(r, "payout_count", i) > 0)
    exhausted_paths = 0
    for i, r in enumerate(rows):
        v = r.get("exhausted")
        if not isinstance(v, bool):
            raise ColdReducerError("cold_trace_field",
                                   f"atom {i}: exhausted={v!r}")
        if v:
            exhausted_paths += 1
    ambiguous_total = sum(_require_int(r, "ambiguous_days", i)
                          for i, r in enumerate(rows))

    feasibility = {
        "n_paths": n,
        "payout_event_paths": payout_paths,
        "total_payout_events": sum(_require_int(r, "payout_count", i)
                                   for i, r in enumerate(rows)),
        "total_skips_n0": sum(_require_int(r, "skips_n0", i)
                              for i, r in enumerate(rows)),
        "total_offered": offered,
        "total_executed_trade_days":
            sum(_require_int(r, "executed_trade_days", i)
                for i, r in enumerate(rows)),
        "total_winning_days": sum(_require_int(r, "winning_days", i)
                                  for i, r in enumerate(rows)),
        "total_days_profit_ge_150":
            sum(_require_int(r, "days_profit_ge_150", i)
                for i, r in enumerate(rows)),
        "total_qualifying_days": sum(_require_int(r, "qualifying_days", i)
                                     for i, r in enumerate(rows)),
        "total_ambiguous_days": ambiguous_total,
        "exhausted_paths": exhausted_paths,
        "total_b2f_used": sum(_require_int(r, "b2f_used", i)
                              for i, r in enumerate(rows)),
        "total_contract_cap_hits":
            _absent_aware_sum(rows, "contract_cap_hits"),
        "total_e2_over_budget_days":
            _absent_aware_sum(rows, "e2_over_budget_days"),
        "payout_event_path_share": payout_paths / n,
        "exhausted_share": exhausted_paths / n,
        "ambiguous_share": (ambiguous_total / offered if offered else 0.0),
    }

    # --- digests, recomputed from the SERIALISED bytes ---
    atom_digests = {}
    for row in rows:
        atom_digests[(_require_int(row, "world_index", 0),
                      _require_int(row, "phase_offset", 0))] = \
            _sha256(_canonical(row))

    return {
        "cold_reducer_version": COLD_REDUCER_VERSION,
        "n_atoms": n,
        "world_ids": tuple(world_ids),
        "world_means": tuple(world_means),
        "within_world_ses": tuple(world_ses),
        "p5": _quantile_linear(sorted_means, 5),
        "median": _quantile_linear(sorted_means, 50),
        "p95": _quantile_linear(sorted_means, 95),
        "between_world_sd": between_sd,
        "max_within_world_se": max_se,
        "feasibility": feasibility,
        "actual_phase_keys_by_world": phase_keys_by_world,
        "atom_digests": atom_digests,
        "observations_digest": _sha256(
            "\n".join(_canonical(r) for r in rows)),
        "total_predictive_evs": tuple(
            ev for _k, ev in sorted(
                ((( _require_int(r, "world_index", i),
                    _require_int(r, "phase_offset", i)),
                  _require_number(r, "monthly_prop_operating_ev", i))
                 for i, r in enumerate(rows)),
                key=lambda kv: kv[0])),
    }
