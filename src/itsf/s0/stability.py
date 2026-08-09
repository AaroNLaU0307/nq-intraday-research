"""S0 Development internal-stability views (frozen §2) — E4 skeleton.

# frozen: S0 §2 — "Development 内部稳定性检查（替代 IV 访问）时代切片
2010-2013 / 2014-2017 / 2018-2021；按年表格（强制）＋ leave-one-year-out；
多空分开；20 日实现波动率三分位分层。"

Scope of THIS module: slice one engine x cost-scenario's ORACLE-day (D_TP,
i.e. `per_theta_block["d_tp"][engine][scenario]`) daily-USD-P&L series along
the four frozen §2 axes and describe each bucket with the ONE shared
descriptive cell shape. It computes no verdict and applies no threshold — the
GO/STOP/边界区 reading is MC's (frozen §10.4) and never happens here.

What is FROZEN and what is ENGINEERING
---------------------------------------
FROZEN (never a parameter, never re-derived here):
  * the three era boundaries 2010-2013 / 2014-2017 / 2018-2021, inclusive on
    both ends (frozen §2 时代切片);
  * by_year is MANDATORY (frozen §2 按年表格（强制）) — every year present in
    the series gets its own cell, never pooled away;
  * leave-one-year-out is a PURE RE-AGGREGATION of the same per-day P&L with
    NO refitting of any threshold (frozen §2 leave-one-year-out): the
    per-axis builders here take only a pnl series and a year/direction lookup,
    never a theta or a label — enforced structurally, not just by convention;
  * by_direction splits by d_open (frozen §2 多空分开);
  * vol_terciles is frozen TEXT (20 日实现波动率三分位分层). Its concrete
    volatility-regime VOCABULARY was DR-2, ruled by Aaron on 2026-08-10; the
    labels are still consumed here as OPAQUE group labels (exactly as
    `gridmix.py` treats its `volatility_regime` stratum axis) because the
    RULED producer lives in `s0/dataset.py` and this module must never hold a
    second computation of it. `vol_axis=None` still reports "unresolved"
    rather than inventing a vocabulary.

POPULATION AXIS (DR-7, ruled 2026-08-10)
----------------------------------------
`stability_population == "both_conditional_and_full_eligible"` requires EVERY
§2 view to be produced TWICE — once over the D_TP-conditional (oracle-day)
sequence, once over the full structurally-eligible day sequence, where a
non-oracle day contributes 0 to a P&L-type view and simply appears in a
count-type view. `build_stability_views` therefore emits, in addition to the
legacy five top-level axes (which remain the CONDITIONAL population, byte for
byte), a `"populations"` block carrying both under explicit keys. The ruled
string is read structurally from `contracts.aaron_ruled_methods()`; any other
non-None string is a ValueError (fail closed), and `None` keeps the pre-ruling
single-population shape for callers that have not been rewired yet.

ENGINEERING CONVENTION (disclosed, deterministic, not frozen text):
  * the ONE shared cell shape `_cell()` used by every axis and every bucket —
    never a bare count — matching the descriptive-block discipline already
    used by `s0/study.py`'s `_series_block`;
  * the P1/P5 worst-day percentile convention (numpy `method="linear"`)
    reused verbatim from `s0/study.py` (WORST_DAY_PERCENTILES, PERCENTILE_
    METHOD) so a stability-view percentile and a study.py percentile are
    computed by the identical estimator;
  * a "vol_na" bucket for any date absent from an injected `vol_axis`, so a
    caller's incomplete volatility mapping is DISCLOSED rather than silently
    dropping days from the tercile view (frozen §3 NA policy: no day is
    silently deleted).

Conservation discipline: every axis reports `"conservation_ok"` — for the
partitioning axes (epochs, by_year, by_direction, vol_terciles when resolved)
this is "do the bucket counts sum to the series length"; for
leave_one_year_out (which is NOT a partition — each bucket is the complement
of one year) it is "does loyo[y].n equal total - by_year[y].n for every y".
Neither ever silently passes on a shape it did not check.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from itsf.contracts import aaron_ruled_methods as _aaron_ruled_methods

# --- ruled inputs, READ from the single ruled source ------------------------
# DR-7 (Aaron 2026-08-10). The literal is NEVER restated here: it is read off
# `contracts.aaron_ruled_methods()` at import and only ever COMPARED against.
RULED_STABILITY_POPULATION: str = _aaron_ruled_methods().stability_population

# --- frozen constants (# frozen: S0 §2) -------------------------------------
EPOCHS = (
    ("2010-2013", 2010, 2013),
    ("2014-2017", 2014, 2017),
    ("2018-2021", 2018, 2021),
)
OUTSIDE_EPOCHS = "outside_epochs"
EPOCH_LABELS = tuple(label for label, _lo, _hi in EPOCHS)
ALL_EPOCH_LABELS = EPOCH_LABELS + (OUTSIDE_EPOCHS,)

DIRECTION_KEYS = {1: "+1", -1: "-1"}
# DR-7 full-eligible population only: a structurally eligible day with no
# frozen §5 direction (d_open == 0) is NOT an Oracle day and has no side, but
# it is part of the full-eligible sequence and must not be deleted. It gets
# its own bucket so 多空分开 stays literally two-sided and the no-direction
# days are never silently folded into either side.
DIRECTION_NONE_KEY = "0"

# DR-7 population keys (engineering names for a ruled REQUIREMENT).
POPULATION_CONDITIONAL = "conditional"
POPULATION_FULL_ELIGIBLE = "full_eligible"
POPULATION_KEYS = (POPULATION_CONDITIONAL, POPULATION_FULL_ELIGIBLE)

# engineering convention: reused verbatim from s0/study.py's worst-day report
# so a stability-view percentile and a study.py percentile are the same
# estimator (numpy's default, linear interpolation between order statistics).
WORST_DAY_PERCENTILES = (1.0, 5.0)
PERCENTILE_METHOD = "linear"

VOL_NA_BUCKET = "vol_na"
VOL_UNRESOLVED_REASON = "DR-M6-B-v2 pending"


class StabilityInputError(ValueError):
    """day_meta / vol_axis does not cover the pnl series it is asked to slice,
    or a supplied row is structurally malformed."""


# ===========================================================================
# the one shared descriptive cell
# ===========================================================================

def _percentile(values: Sequence[float], q: float) -> float | None:
    if not len(values):
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q,
                               method=PERCENTILE_METHOD))


def _cell(pairs: Sequence[tuple[str, float]]) -> dict[str, object]:
    """(trade_date, USD) pairs -> the ONE descriptive shape every stability
    axis and every bucket uses — never a bare count.

    "best_day" / "worst_day" are the best/worst SINGLE-DAY USD P&L values in
    the bucket (a bucket of zero days reports every field as None/0, never a
    silently-omitted key, so every bucket — including an empty one — has the
    identical key set).
    """
    vals = [float(v) for _d, v in pairs]
    n = len(vals)
    total = float(sum(vals)) if vals else 0.0
    return {
        "n": n,
        "sum_usd": total,
        "mean_usd": (total / n) if n else None,
        "worst_day_pnl_percentiles": {
            f"P{q:g}": _percentile(vals, q) for q in WORST_DAY_PERCENTILES},
        "best_day": max(vals) if vals else None,
        "worst_day": min(vals) if vals else None,
        "n_positive": sum(1 for v in vals if v > 0),
        "n_negative": sum(1 for v in vals if v < 0),
        "n_zero": sum(1 for v in vals if v == 0.0),
    }


CELL_KEYS = frozenset(_cell([]))


# ===========================================================================
# day_meta validation
# ===========================================================================

_REQUIRED_META_KEYS = ("year", "era", "d_open")


def _validated_meta(dates: Sequence[str],
                    day_meta: Mapping[str, Mapping[str, object]],
                    allow_no_direction: bool = False,
                    ) -> dict[str, dict[str, object]]:
    """Every date in the pnl series must carry year/era/d_open. Fail closed —
    an Oracle-day pnl value with no year/direction lookup cannot be sliced by
    ANY of the frozen §2 axes, so a gap here is a defect, not a silent skip.

    `allow_no_direction` is False for the D_TP-CONDITIONAL population (an
    Oracle day always has a direction, so d_open == 0 there is a defect) and
    True only for the DR-7 FULL-ELIGIBLE population, where a structurally
    eligible no-direction day legitimately appears and goes to its own
    `DIRECTION_NONE_KEY` bucket rather than being deleted or mis-sided."""
    missing = [d for d in dates if d not in day_meta]
    if missing:
        raise StabilityInputError(
            f"{len(missing)} date(s) have no day_meta entry, e.g. "
            f"{sorted(missing)[:5]} — every Oracle-day pnl date needs "
            "year/era/d_open (frozen: S0 §2)")
    out: dict[str, dict[str, object]] = {}
    for date in dates:
        row = day_meta[date]
        for key in _REQUIRED_META_KEYS:
            if key not in row:
                raise StabilityInputError(
                    f"day_meta[{date!r}] is missing required key {key!r} "
                    f"(needs {_REQUIRED_META_KEYS})")
        d_open = int(row["d_open"])
        legal = (1, -1, 0) if allow_no_direction else (1, -1)
        if d_open not in legal:
            raise StabilityInputError(
                f"day_meta[{date!r}].d_open must be one of {legal} (frozen §5 "
                f"no-direction days are not Oracle days; d_open == 0 is legal "
                f"only in the DR-7 full-eligible population), got {d_open!r}")
        out[date] = {"year": str(row["year"]), "era": str(row["era"]),
                    "d_open": d_open}
    return out


# ===========================================================================
# per-axis builders
# ===========================================================================

def _epoch_of(year: int) -> str:
    """# frozen: S0 §2 时代切片, inclusive on both ends of each bucket."""
    for label, lo, hi in EPOCHS:
        if lo <= year <= hi:
            return label
    return OUTSIDE_EPOCHS


def _epoch_axis(pnl: Mapping[str, float],
                meta: Mapping[str, dict[str, object]]) -> dict[str, object]:
    buckets: dict[str, list[tuple[str, float]]] = {
        label: [] for label in ALL_EPOCH_LABELS}
    for date, value in pnl.items():
        buckets[_epoch_of(int(meta[date]["year"]))].append((date, value))
    cells = {label: _cell(pairs) for label, pairs in buckets.items()}
    conservation_ok = sum(c["n"] for c in cells.values()) == len(pnl)
    return {**cells, "conservation_ok": conservation_ok}


def _by_year_axis(pnl: Mapping[str, float],
                  meta: Mapping[str, dict[str, object]]) -> dict[str, object]:
    """# frozen: S0 §2 按年表格（强制）— every year present, never pooled."""
    years = sorted({meta[d]["year"] for d in pnl})
    buckets: dict[str, list[tuple[str, float]]] = {y: [] for y in years}
    for date, value in pnl.items():
        buckets[meta[date]["year"]].append((date, value))
    cells = {y: _cell(pairs) for y, pairs in buckets.items()}
    conservation_ok = sum(c["n"] for c in cells.values()) == len(pnl)
    return {**cells, "conservation_ok": conservation_ok}


def _loyo_axis(pnl: Mapping[str, float], meta: Mapping[str, dict[str, object]],
              by_year_cells: Mapping[str, object]) -> dict[str, object]:
    """# frozen: S0 §2 leave-one-year-out — pure re-aggregation of the SAME
    per-day pnl over all years except one. Takes only `pnl` (date -> usd) and
    `meta` (date -> year lookup) — no theta, no label, no threshold — so it
    structurally cannot refit anything."""
    years = [y for y in by_year_cells if y != "conservation_ok"]
    all_pairs = list(pnl.items())
    out: dict[str, object] = {}
    ok = True
    for y in years:
        other_pairs = [(d, v) for d, v in all_pairs if meta[d]["year"] != y]
        cell = _cell(other_pairs)
        out[y] = cell
        if cell["n"] != len(pnl) - by_year_cells[y]["n"]:
            ok = False
    out["conservation_ok"] = ok
    return out


def _direction_axis(pnl: Mapping[str, float],
                    meta: Mapping[str, dict[str, object]],
                    allow_no_direction: bool = False) -> dict[str, object]:
    """# frozen: S0 §2 多空分开.

    The no-direction bucket is emitted ONLY for the DR-7 full-eligible
    population (`allow_no_direction`), so the conditional population's key set
    — the one every existing consumer validates — is unchanged.
    """
    buckets: dict[str, list[tuple[str, float]]] = {"+1": [], "-1": []}
    if allow_no_direction:
        buckets[DIRECTION_NONE_KEY] = []
    for date, value in pnl.items():
        d_open = meta[date]["d_open"]
        key = (DIRECTION_NONE_KEY if d_open == 0
               else DIRECTION_KEYS[d_open])
        buckets[key].append((date, value))
    cells = {k: _cell(pairs) for k, pairs in buckets.items()}
    conservation_ok = sum(c["n"] for c in cells.values()) == len(pnl)
    return {**cells, "conservation_ok": conservation_ok}


def _vol_axis(pnl: Mapping[str, float],
             vol_axis: Mapping[str, str] | None) -> dict[str, object]:
    """# frozen: S0 §2 20 日实现波动率三分位分层 — `vol_axis` values stay
    OPAQUE group labels here (same discipline as gridmix.py's
    volatility_regime stratum axis); None means "not yet resolvable" and is
    disclosed as such rather than guessed at.

    DR-2 (Aaron 2026-08-10) makes ``vol_na`` a RULED FIRST-CLASS LABEL — the
    fourth stratum a day lands in when it has fewer than 21 qualifying prior
    closes. The pre-ruling collision guard (which REFUSED an explicit
    ``vol_na`` because the label was reserved for "date absent from
    vol_axis") is therefore gone: an explicit ruled ``vol_na`` and an absent
    date now land in the SAME bucket by design, and the absent-date count is
    disclosed by the caller (`_engine_scenario_view`) rather than by a fourth
    key inside this axis — adding a key here would change the axis key set
    every downstream stratum-count validator pins.
    """
    if vol_axis is None:
        return {"status": "unresolved", "reason": VOL_UNRESOLVED_REASON}
    # M6.1.2: the NA bucket is part of the STABLE stratum shape — always
    # emitted (empty when every day carries a label) so the sealed payload
    # never changes key set with the data, and a reader can always see that
    # the NA layer was accounted for.
    #
    # DR-7 extends the SAME reasoning to the tercile buckets. The two ruled
    # populations slice DIFFERENT day sequences out of ONE `vol_axis`, so a
    # data-driven bucket set would let the conditional population emit two
    # terciles while the full-eligible one emits three — a key set that moves
    # with the data, which is precisely what the stable-shape discipline (and
    # the sealed-payload stratum-count validator) forbids. Buckets are
    # therefore seeded from the SUPPLIED VOCABULARY, not from the slice.
    buckets: dict[str, list[tuple[str, float]]] = {
        label: [] for label in set(vol_axis.values()) | {VOL_NA_BUCKET}}
    for date, value in pnl.items():
        label = vol_axis[date] if date in vol_axis else VOL_NA_BUCKET
        buckets.setdefault(label, []).append((date, value))
    cells = {label: _cell(pairs) for label, pairs in sorted(buckets.items())}
    conservation_ok = sum(c["n"] for c in cells.values()) == len(pnl)
    return {**cells, "conservation_ok": conservation_ok}


# ===========================================================================
# entry point
# ===========================================================================

def _axes(pnl: Mapping[str, float],
          day_meta: Mapping[str, Mapping[str, object]],
          vol_axis: Mapping[str, str] | None,
          allow_no_direction: bool = False) -> dict[str, object]:
    """The five frozen §2 axes over ONE day sequence."""
    dates = sorted(pnl)
    meta = _validated_meta(dates, day_meta, allow_no_direction)
    by_year_cells = _by_year_axis(pnl, meta)
    return {
        "epochs": _epoch_axis(pnl, meta),
        "by_year": by_year_cells,
        "leave_one_year_out": _loyo_axis(pnl, meta, by_year_cells),
        "by_direction": _direction_axis(pnl, meta, allow_no_direction),
        "vol_terciles": _vol_axis(pnl, vol_axis),
    }


def _population_block(population: str, pnl: Mapping[str, float],
                      day_meta: Mapping[str, Mapping[str, object]],
                      vol_axis: Mapping[str, str] | None,
                      allow_no_direction: bool,
                      extra: Mapping[str, object] | None = None,
                      ) -> dict[str, object]:
    axes = _axes(pnl, day_meta, vol_axis, allow_no_direction)
    block: dict[str, object] = {
        "population": population,
        "n_days": len(pnl),
        "n_vol_axis_absent_days": (
            0 if vol_axis is None
            else sum(1 for d in pnl if d not in vol_axis)),
        **axes,
    }
    if extra:
        block.update(extra)
    return block


def _full_eligible_series(pnl: Mapping[str, float],
                          day_meta: Mapping[str, Mapping[str, object]],
                          ) -> dict[str, float]:
    """DR-7 — the FULL structurally-eligible day sequence's P&L series.

    `day_meta` is the caller's structurally-eligible day universe (the
    producer builds it from EVERY `S0Dataset.records` row, not from the D_TP
    subset). A day outside the conditional D_TP set contributes EXACTLY 0.0
    to a P&L-type view — the frozen §2 reading of "this day was in the
    sample and the strategy earned nothing on it" — and is simply present for
    a count-type view. No day is dropped and no value is imputed.
    """
    return {d: float(pnl.get(d, 0.0)) for d in sorted(day_meta)}


def _resolved_population_rule(stability_population: str | None) -> str | None:
    """Fail-closed dispatch on the DR-7 ruled string.

    None  -> the pre-ruling single-population shape (legacy callers).
    RULED -> both populations.
    anything else -> ValueError; an un-ruled population word must never
    silently select one of the two behaviours.
    """
    if stability_population is None:
        return None
    if stability_population == RULED_STABILITY_POPULATION:
        return stability_population
    raise ValueError(
        f"stability_population_not_ruled:{stability_population} — the only "
        "ruled value is the one carried by "
        "contracts.aaron_ruled_methods().stability_population (fail closed)")


def check_populations(cell: Mapping[str, object],
                      stability_population: str | None) -> list[str]:
    """Problem codes for one engine x scenario cell against the DR-7 ruling.

    Exposed so a renderer/validator can refuse a SINGLE-population cell that
    claims the ruled both-populations method, without re-implementing the
    rule. Empty list == admissible. A malformed `cell` never raises (it comes
    back as problem codes); an UN-RULED `stability_population` still raises,
    because that is the fail-closed dispatch itself and must not degrade into
    a silent "no problems".
    """
    problems: list[str] = []
    rule = _resolved_population_rule(stability_population)
    if rule is None:
        return problems
    pops = cell.get("populations") if isinstance(cell, Mapping) else None
    if not isinstance(pops, Mapping):
        problems.append("stability_populations_missing")
        return problems
    if pops.get("rule") != rule:
        problems.append(f"stability_population_rule_mismatch:{pops.get('rule')}")
    for key in POPULATION_KEYS:
        block = pops.get(key)
        if not isinstance(block, Mapping):
            problems.append(f"stability_population_missing:{key}")
            continue
        if block.get("population") != key:
            problems.append(f"stability_population_mislabelled:{key}")
        for axis in ("epochs", "by_year", "leave_one_year_out",
                     "by_direction", "vol_terciles"):
            if axis not in block:
                problems.append(f"stability_population_axis_missing:{key}|{axis}")
    return problems


def _engine_scenario_view(pnl: Mapping[str, float],
                          day_meta: Mapping[str, Mapping[str, object]],
                          vol_axis: Mapping[str, str] | None,
                          population_rule: str | None = None,
                          ) -> dict[str, object]:
    # The five top-level axes ARE the D_TP-conditional population and stay
    # exactly where every existing consumer reads them (byte-for-byte
    # unchanged when population_rule is None).
    conditional = _axes(pnl, day_meta, vol_axis)
    out: dict[str, object] = dict(conditional)
    if population_rule is None:
        return out
    full_pnl = _full_eligible_series(pnl, day_meta)
    out["populations"] = {
        "rule": population_rule,
        POPULATION_CONDITIONAL: _population_block(
            POPULATION_CONDITIONAL, pnl, day_meta, vol_axis,
            allow_no_direction=False),
        POPULATION_FULL_ELIGIBLE: _population_block(
            POPULATION_FULL_ELIGIBLE, full_pnl, day_meta, vol_axis,
            allow_no_direction=True,
            extra={"n_zero_filled_non_oracle_days":
                   len(full_pnl) - len(pnl),
                   "zero_fill_note":
                       "non-oracle structurally-eligible days contribute "
                       "0.0 USD to P&L-type views and are counted, never "
                       "dropped (DR-7)"}),
    }
    return out


def build_stability_views(per_theta_block: Mapping[str, object],
                          day_meta: Mapping[str, Mapping[str, object]],
                          vol_axis: Mapping[str, str] | None = None,
                          stability_population: str | None = None,
                          ) -> dict[str, object]:
    """frozen: S0 §2 — the four Development stability axes, for EACH engine x
    cost-scenario of one `per_theta_block` (the `s0/study.py` per-theta output
    shape), computed over the ORACLE-day (D_TP) pnl series
    `per_theta_block["d_tp"][engine][scenario]`.

    Parameters
    ----------
    per_theta_block
        One entry of `build_study(...)["per_theta"]` (i.e. already selected
        for ONE frozen theta) — must carry `"executable"` (used only to
        enumerate the engine x scenario keys) and `"d_tp"` (date -> usd, the
        actual series this module slices).
    day_meta
        date -> {"year": str, "era": str, "d_open": int}, supplied by the
        caller (this module does no lookahead and reads no archive). Under
        DR-7 this mapping is ALSO the full structurally-eligible day
        universe: its key set defines the second population, so it must
        carry every structurally eligible day, not only the D_TP days.
    vol_axis
        date -> volatility-regime label (the DR-2 producer's output, consumed
        as opaque labels), or None if the axis is not supplied — then
        `vol_terciles` reports `{"status": "unresolved", "reason": ...}`
        instead of guessing at a vocabulary.
    stability_population
        DR-7. None keeps the pre-ruling single (conditional) population
        shape; the ruled string additionally emits `"populations"`; any other
        string raises ValueError.

    Returns
    -------
    {engine: {scenario: {"epochs", "by_year", "leave_one_year_out",
                        "by_direction", "vol_terciles"
                        [, "populations"]}}}
    """
    population_rule = _resolved_population_rule(stability_population)
    executable = per_theta_block.get("executable")
    d_tp = per_theta_block.get("d_tp")
    if executable is None or d_tp is None:
        raise StabilityInputError(
            "per_theta_block must carry 'executable' and 'd_tp' — the "
            "s0/study.py per_theta output shape")
    out: dict[str, object] = {}
    for engine, scenarios in executable.items():
        if engine not in d_tp:
            raise StabilityInputError(
                f"engine {engine!r} is in 'executable' but absent from "
                "'d_tp' — malformed per_theta_block")
        out[engine] = {}
        for scenario in scenarios:
            if scenario not in d_tp[engine]:
                raise StabilityInputError(
                    f"scenario {scenario!r} is in executable[{engine!r}] but "
                    f"absent from d_tp[{engine!r}] — malformed per_theta_block")
            out[engine][scenario] = _engine_scenario_view(
                d_tp[engine][scenario], day_meta, vol_axis, population_rule)
    return out
