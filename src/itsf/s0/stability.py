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
  * vol_terciles is frozen TEXT (20 日实现波动率三分位分层) but its concrete
    volatility-regime VOCABULARY is an open decision (DR-M6-B / DR-M6-B-v2):
    this module treats `vol_axis` values as OPAQUE group labels, exactly as
    `gridmix.py` treats its `volatility_regime` stratum axis, and reports
    "unresolved" rather than inventing a vocabulary when no axis is supplied.

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
                    ) -> dict[str, dict[str, object]]:
    """Every date in the pnl series must carry year/era/d_open. Fail closed —
    an Oracle-day pnl value with no year/direction lookup cannot be sliced by
    ANY of the frozen §2 axes, so a gap here is a defect, not a silent skip."""
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
        if d_open not in (1, -1):
            raise StabilityInputError(
                f"day_meta[{date!r}].d_open must be +1 or -1 (frozen §5 "
                f"no-direction days are not Oracle days), got {d_open!r}")
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
                    meta: Mapping[str, dict[str, object]]) -> dict[str, object]:
    """# frozen: S0 §2 多空分开."""
    buckets: dict[str, list[tuple[str, float]]] = {"+1": [], "-1": []}
    for date, value in pnl.items():
        buckets[DIRECTION_KEYS[meta[date]["d_open"]]].append((date, value))
    cells = {k: _cell(pairs) for k, pairs in buckets.items()}
    conservation_ok = sum(c["n"] for c in cells.values()) == len(pnl)
    return {**cells, "conservation_ok": conservation_ok}


def _vol_axis(pnl: Mapping[str, float],
             vol_axis: Mapping[str, str] | None) -> dict[str, object]:
    """# frozen: S0 §2 20 日实现波动率三分位分层 — vocabulary is DR-M6-B/-v2
    (open), so `vol_axis` values are opaque group labels (same discipline as
    gridmix.py's volatility_regime stratum axis); None means "not yet
    resolvable" and is disclosed as such rather than guessed at."""
    if vol_axis is None:
        return {"status": "unresolved", "reason": VOL_UNRESOLVED_REASON}
    for date, label in vol_axis.items():
        if label == VOL_NA_BUCKET:
            raise StabilityInputError(
                f"vol_axis[{date!r}] == {VOL_NA_BUCKET!r} collides with the "
                "reserved bucket this module uses for dates ABSENT from "
                "vol_axis — pick a different label")
    # M6.1.2: the NA bucket is part of the STABLE stratum shape — always
    # emitted (empty when every day carries a label) so the sealed payload
    # never changes key set with the data, and a reader can always see that
    # the NA layer was accounted for.
    buckets: dict[str, list[tuple[str, float]]] = {VOL_NA_BUCKET: []}
    for date, value in pnl.items():
        label = vol_axis[date] if date in vol_axis else VOL_NA_BUCKET
        buckets.setdefault(label, []).append((date, value))
    cells = {label: _cell(pairs) for label, pairs in sorted(buckets.items())}
    conservation_ok = sum(c["n"] for c in cells.values()) == len(pnl)
    return {**cells, "conservation_ok": conservation_ok}


# ===========================================================================
# entry point
# ===========================================================================

def _engine_scenario_view(pnl: Mapping[str, float],
                          day_meta: Mapping[str, Mapping[str, object]],
                          vol_axis: Mapping[str, str] | None,
                          ) -> dict[str, object]:
    dates = sorted(pnl)
    meta = _validated_meta(dates, day_meta)
    by_year_cells = _by_year_axis(pnl, meta)
    return {
        "epochs": _epoch_axis(pnl, meta),
        "by_year": by_year_cells,
        "leave_one_year_out": _loyo_axis(pnl, meta, by_year_cells),
        "by_direction": _direction_axis(pnl, meta),
        "vol_terciles": _vol_axis(pnl, vol_axis),
    }


def build_stability_views(per_theta_block: Mapping[str, object],
                          day_meta: Mapping[str, Mapping[str, object]],
                          vol_axis: Mapping[str, str] | None = None,
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
        caller (this module does no lookahead and reads no archive).
    vol_axis
        date -> opaque volatility-regime label, or None if the axis is not
        yet resolvable (DR-M6-B-v2 pending) — then `vol_terciles` reports
        `{"status": "unresolved", "reason": ...}` instead of guessing at a
        vocabulary.

    Returns
    -------
    {engine: {scenario: {"epochs", "by_year", "leave_one_year_out",
                        "by_direction", "vol_terciles"}}}
    """
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
                d_tp[engine][scenario], day_meta, vol_axis)
    return out
