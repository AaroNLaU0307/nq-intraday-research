"""S0 -> MC handoff schema skeleton (E6). SCHEMA_VERSION = "m6.1-draft-1".

Scope of THIS module: package the day-level classification, the Appendix-A
grid samples, and the frozen seed/stream provenance into a byte-stable JSON
shape MC can consume and REPLAY, WITHOUT deciding any of the open method
questions those shapes still carry (DR-M6-E / DR-M6-F / …). Where a field's
vocabulary is genuinely undecided, this module emits a disclosed, greppable
UNRESOLVED marker rather than silently picking one — the same discipline
`stability.py` uses for the vol_terciles axis and `gridmix.py` uses for
`volatility_regime`.

Ownership note: `src/itsf/s0/report.py` and `tests/test_s0_report.py` are
owned by a PARALLEL agent in this same round; this module deliberately does
NOT import anything from `report.py` (nor does it duplicate report.py's own
canonical-JSON helper by reference — `dumps_canonical` here is a separate,
self-contained implementation of the identical
`json.dumps(..., allow_nan=False, sort_keys=True)` recipe). The main agent is
expected to unify the two canonical-JSON helpers later; until then this
module must not create a cross-import dependency on the other agent's
in-flight file.

What is FROZEN and what is OPEN (DR-M6-*)
------------------------------------------
FROZEN:
  * contracts.RESEARCH_BOOTSTRAP_SEEDS {7, 13, 31} is the only source of
    research randomness (IR DR-02) — `build_seed_manifest` asserts this by
    identity rather than by value, so a future local copy anywhere upstream
    would be caught here too.
  * the quoted-seed convention (first frozen seed, never best-of) and the
    stats/grid stream tags are read FROM those modules' own constants, never
    restated as a second copy.

OPEN (disclosed as UNRESOLVED, never silently resolved):
  * DR-M6-F — the mapping of `event_flag_final` (including its NA state) into
    an Appendix-A stratum; `event_stratum` is ALWAYS the marker
    "UNRESOLVED_DR-M6-F" (regardless of whether the day's own event flag is
    concrete or NA — the entire event -> stratum MAPPING SCHEME is undecided,
    not just its NA branch), and `build_day_strata` REFUSES a day_row that
    already carries an `"event_stratum"` key of its own: silently accepting a
    caller-supplied vocabulary would be exactly the premature resolution this
    marker exists to prevent.
  * DR-M6-E — the replay `k_policy` (how many MC resamples/paths a grid
    sample feeds), marked "UNRESOLVED_DR-M6-E".
  * `crn_scope` (which layers share common random numbers across the S0/MC
    boundary) — marked with the bare `UNRESOLVED` sentinel.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from itsf import contracts
from itsf.s0 import gridmix as s0_gridmix
from itsf.s0 import stability as s0_stability
from itsf.s0 import stats as s0_stats

SCHEMA_VERSION = "m6.1-draft-1"


# ===========================================================================
# UNRESOLVED sentinel
# ===========================================================================

class _UnresolvedSentinel(str):
    """Singleton sentinel for a field whose value is blocked on an open
    method decision (DR-M6-*).

    Subclasses `str` with the literal value "UNRESOLVED" so it survives plain
    JSON serialization and any `== "UNRESOLVED"` check downstream unchanged,
    while remaining identity-comparable (`is UNRESOLVED`) so a caller can
    still distinguish "genuinely blocked, marked by this module" from a field
    that merely happens to hold that literal string for an unrelated reason.
    """
    _instance: "_UnresolvedSentinel | None" = None

    def __new__(cls) -> "_UnresolvedSentinel":
        if cls._instance is None:
            cls._instance = super().__new__(cls, "UNRESOLVED")
        return cls._instance

    def __repr__(self) -> str:
        return "UNRESOLVED"


UNRESOLVED = _UnresolvedSentinel()


def _unresolved(decision_id: str) -> str:
    """A disclosed, greppable stand-in for a value blocked on open decision
    record `decision_id` (e.g. "DR-M6-F" -> "UNRESOLVED_DR-M6-F"). Never
    silently resolved by picking a vocabulary."""
    return f"UNRESOLVED_{decision_id}"


# ===========================================================================
# canonical JSON
# ===========================================================================

def dumps_canonical(obj: object) -> str:
    """The ONE canonical serialization this module uses for anything destined
    for a byte-stable handoff artifact: `sort_keys=True` for reproducible
    byte output, `allow_nan=False` so a NaN/Infinity raises loudly instead of
    silently emitting non-standard JSON (frozen S0 §3 NA policy: NA is
    reported through explicit sentinels — None, "UNRESOLVED_*", explicit NA
    reason strings — never a JSON NaN literal)."""
    return json.dumps(obj, allow_nan=False, sort_keys=True)


# ===========================================================================
# E6a — build_day_strata
# ===========================================================================

_REQUIRED_DAY_ROW_KEYS = ("micro_execution_era", "stability_epoch", "year",
                         "d_open", "event_flag_final", "vol_status",
                         "tp_fp_class")

_KNOWN_ERAS = frozenset({"counterfactual_micro_execution",
                        "actual_micro_available_era"})
_KNOWN_EPOCHS = frozenset(s0_stability.ALL_EPOCH_LABELS)
_TP_FP_VALUES = frozenset({"TP", "FP", "non_tradeable"})


def _theta_key(theta: float) -> str:
    """Kept in sync with `s0.study.theta_key` BY CONVENTION (both format the
    frozen theta values identically: "theta_0.5" / "theta_0.3"); duplicated
    rather than imported so this schema-only module stays decoupled from the
    day-set-selection layer (`s0/study.py`)."""
    return f"theta_{theta:g}"


def build_day_strata(day_rows: Mapping[str, Mapping[str, object]],
                     thetas: Sequence[float]) -> dict[str, object]:
    """Wrap the per-day classification into the frozen handoff shape.

    Parameters
    ----------
    day_rows
        date -> {"micro_execution_era", "stability_epoch", "year", "d_open",
        "event_flag_final", "vol_status", "tp_fp_class"}. See module
        docstring for the DR-M6-F event_stratum discipline and the
        micro_execution_era / stability_epoch distinctness rule.
    thetas
        the frozen theta values this handoff round reports (subset of the
        frozen {0.5, 0.3} pair) — used only to validate each day's
        `tp_fp_class` covers exactly this set of theta keys.

    Returns
    -------
    {"schema_version", "ordering": "sorted-by-date", "days": {date: row}}
    with `days` built in canonical (sorted) date order.
    """
    theta_keys = tuple(_theta_key(t) for t in thetas)
    if not theta_keys:
        raise ValueError("thetas must not be empty")
    if len(set(theta_keys)) != len(theta_keys):
        raise ValueError(f"duplicate theta in {thetas}")
    theta_key_set = set(theta_keys)

    days: dict[str, object] = {}
    for date in sorted(day_rows):
        row = day_rows[date]
        if "event_stratum" in row:
            raise ValueError(
                f"{date}: day_rows must not carry 'event_stratum' — the "
                "event -> Appendix-A stratum mapping is DR-M6-F (open); this "
                "module computes it as UNRESOLVED and refuses a "
                "caller-supplied vocabulary (no silent resolution)")
        missing = [k for k in _REQUIRED_DAY_ROW_KEYS if k not in row]
        if missing:
            raise ValueError(f"{date}: day_rows entry missing {missing}")

        era = str(row["micro_execution_era"])
        epoch = str(row["stability_epoch"])
        if era not in _KNOWN_ERAS:
            raise ValueError(
                f"{date}: micro_execution_era {era!r} is not one of "
                f"{sorted(_KNOWN_ERAS)} (frozen S0 §6 two-era axis) — a "
                "stability_epoch label in this slot would be a conflation")
        if epoch not in _KNOWN_EPOCHS:
            raise ValueError(
                f"{date}: stability_epoch {epoch!r} is not one of "
                f"{sorted(_KNOWN_EPOCHS)} (frozen S0 §2 epoch labels) — a "
                "micro_execution_era label in this slot would be a "
                "conflation")

        d_open = int(row["d_open"])
        if d_open not in (-1, 0, 1):
            raise ValueError(f"{date}: d_open must be in (-1, 0, 1), got "
                             f"{d_open!r}")

        tp_fp_class = dict(row["tp_fp_class"])
        if set(tp_fp_class) != theta_key_set:
            raise ValueError(
                f"{date}: tp_fp_class keys {sorted(tp_fp_class)} != the "
                f"requested thetas {sorted(theta_key_set)}")
        bad_values = {k: v for k, v in tp_fp_class.items()
                     if v not in _TP_FP_VALUES}
        if bad_values:
            raise ValueError(
                f"{date}: tp_fp_class has non-TP/FP/non_tradeable values "
                f"{bad_values}")

        event_flag_final = row["event_flag_final"]
        days[date] = {
            "micro_execution_era": era,
            "stability_epoch": epoch,
            "year": str(row["year"]),
            "d_open": d_open,
            "event_flag_final": event_flag_final,
            "event_na": event_flag_final is None,
            # DR-M6-F: the event -> Appendix-A stratum MAPPING is open, not
            # just its NA branch, so every day gets the same marker.
            "event_stratum": _unresolved("DR-M6-F"),
            "vol_status": str(row["vol_status"]),
            "tp_fp_class": {k: tp_fp_class[k] for k in theta_keys},
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "ordering": "sorted-by-date",
        "days": days,
    }


# ===========================================================================
# E6b — build_grid_samples
# ===========================================================================

def build_grid_samples(grid_output: Mapping[str, object],
                       run_meta: Mapping[str, object]) -> dict[str, object]:
    """Wrap one `gridmix.build_grid(...)` output into the MC handoff shape.

    Parameters
    ----------
    grid_output
        the return value of `gridmix.build_grid` (or `_build_grid_unchecked`
        in a test) for ONE engine x cost-scenario x theta.
    run_meta
        caller-supplied provenance (e.g. which theta/engine/scenario this
        grid belongs to) — passed through verbatim under `"run_meta"` so a
        replay consumer can identify which grid it is looking at; this
        module attaches no meaning to its contents.

    Returns
    -------
    {"schema_version", "cells": {cell_key: {"per_seed": {seed: {...}},
                                           "infeasible_by_sample", "q_mil",
                                           "r_mil"}},
     "run_meta", "replay": {"stream_formula", "grid_stream_tag", "k_policy",
                           "crn_scope"}}

    `q_mil` / `r_mil` are recovered as `round(target_precision * 1000)` /
    `round(target_recall * 1000)` — the exact inverse of how `gridmix`
    produced those floats (`q_mil / 1000.0`), so they replay the ORIGINAL
    integer millis exactly; a replay test rebuilds
    `default_rng([master, GRID_STREAM_TAG, q_mil, r_mil])` from these two
    integers plus `replay.grid_stream_tag` and reproduces the cell's
    selection.
    """
    grid = grid_output["grid"]
    cells: dict[str, object] = {}
    for cell_key, point in grid.items():
        per_seed: dict[int, object] = {}
        for seed, block in point.get("per_seed", {}).items():
            per_seed[seed] = {
                "tp_dates": list(block["tp_dates"]),
                "fp_dates": list(block["fp_dates"]),
                "markers": [list(m) for m in block["day_markers"]],
                "realized_precision": block["realized_precision"],
                "realized_recall": block["realized_recall"],
                "target_precision": block["target_precision"],
                "target_recall": block["target_recall"],
            }
        cells[cell_key] = {
            "per_seed": per_seed,
            "infeasible_by_sample": bool(point["infeasible_by_sample"]),
            "q_mil": int(round(point["target_precision"] * 1000)),
            "r_mil": int(round(point["target_recall"] * 1000)),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "cells": cells,
        "run_meta": dict(run_meta),
        "replay": {
            "stream_formula":
                "default_rng([master, GRID_STREAM_TAG, q_mil, r_mil])",
            "grid_stream_tag": s0_gridmix.GRID_STREAM_TAG,
            "k_policy": _unresolved("DR-M6-E"),
            "crn_scope": str(UNRESOLVED),
        },
    }


# ===========================================================================
# E6c — build_seed_manifest
# ===========================================================================

def build_seed_manifest() -> dict[str, object]:
    """The frozen seed/stream provenance MC needs to replay S0's randomness,
    read from the modules that own each constant (never a second copy)."""
    # IR DR-02 single-source assertion: stats.py / gridmix.py must be
    # re-exporting the SAME object as contracts.RESEARCH_BOOTSTRAP_SEEDS, not
    # a local copy that could silently drift.
    assert s0_stats.RESEARCH_BOOTSTRAP_SEEDS is contracts.RESEARCH_BOOTSTRAP_SEEDS
    assert s0_gridmix.RESEARCH_BOOTSTRAP_SEEDS is contracts.RESEARCH_BOOTSTRAP_SEEDS

    return {
        "schema_version": SCHEMA_VERSION,
        "research_bootstrap_seeds": list(contracts.RESEARCH_BOOTSTRAP_SEEDS),
        "quoted_seed_convention": (
            "quoted interval/selection = the FIRST frozen master seed, by "
            "fixed convention that predates any data (never best-of); all "
            "seeds are independently run and always reported in full"),
        "stream_tags": {
            "stats_stream_tag": s0_stats.STATS_STREAM_TAG,
            "grid_stream_tag": s0_gridmix.GRID_STREAM_TAG,
        },
        "k_policy": _unresolved("DR-M6-E"),
        "crn_scope": str(UNRESOLVED),
        "engineering_seed_note": (
            "run-infra provenance only; value recorded in governance "
            "metadata, not here"),
    }


# ===========================================================================
# E6d — build_handoff_manifest
# ===========================================================================

def build_handoff_manifest(files: Mapping[str, str]) -> dict[str, object]:
    """name -> {sha256, bytes, line_count (.jsonl only)} manifest of the
    files being handed off to MC. Each file is read exactly once, streamed
    through the hash so a large .jsonl handoff never needs two full passes."""
    manifest: dict[str, object] = {}
    for name, path in files.items():
        digest = hashlib.sha256()
        n_bytes = 0
        n_lines = 0
        is_jsonl = str(path).endswith(".jsonl")
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
                n_bytes += len(chunk)
                if is_jsonl:
                    n_lines += chunk.count(b"\n")
        entry: dict[str, object] = {"sha256": digest.hexdigest(),
                                    "bytes": n_bytes}
        if is_jsonl:
            entry["line_count"] = n_lines
        manifest[name] = entry
    return {"schema_version": SCHEMA_VERSION, "files": manifest}


# ===========================================================================
# E6e — verify_handoff_conservation
# ===========================================================================

def verify_handoff_conservation(
        day_strata: Mapping[str, object], grid_samples: Mapping[str, object],
        record_dates_by_engine_scenario: Mapping[str, Mapping[str, Sequence[str]]],
        ) -> list[str]:
    """Cross-check the three handoff artifacts against each other. Returns a
    (sorted, deterministic) list of problem descriptions — empty means
    conservation holds.

    Checks
    ------
    1. every date appearing in a grid sample (any cell, any seed, TP or FP)
       is present in `day_strata`;
    2. every date appearing in `record_dates_by_engine_scenario` (any engine
       x scenario) is present in `day_strata`;
    3. BIDIRECTIONAL TP/FP <-> record coverage: every date `day_strata`
       classifies TP or FP (for ANY requested theta) has a record for EVERY
       engine x scenario in `record_dates_by_engine_scenario`, and
       conversely every date that HAS a record for some engine x scenario is
       TP/FP-classified in `day_strata` (never only `non_tradeable`).
    """
    problems: list[str] = []
    days = day_strata.get("days", {})

    grid_dates: set[str] = set()
    for cell in grid_samples.get("cells", {}).values():
        for block in cell.get("per_seed", {}).values():
            grid_dates.update(block.get("tp_dates", ()))
            grid_dates.update(block.get("fp_dates", ()))
    for date in sorted(grid_dates):
        if date not in days:
            problems.append(
                f"{date}: appears in a grid sample but is absent from "
                "day_strata")

    engine_scenarios = [(engine, scenario)
                        for engine, scenarios in
                        record_dates_by_engine_scenario.items()
                        for scenario in scenarios]

    record_dates: set[str] = set()
    for engine, scenarios in record_dates_by_engine_scenario.items():
        for scenario, dates in scenarios.items():
            record_dates.update(dates)
    for date in sorted(record_dates):
        if date not in days:
            problems.append(
                f"{date}: has a record but is absent from day_strata")

    classified_dates = {
        date for date, row in days.items()
        if any(v in ("TP", "FP") for v in row.get("tp_fp_class", {}).values())
    }

    for date in sorted(classified_dates):
        for engine, scenario in engine_scenarios:
            engine_dates = record_dates_by_engine_scenario.get(engine, {})
            scenario_dates = set(engine_dates.get(scenario, ()))
            if date not in scenario_dates:
                problems.append(
                    f"{date}: TP/FP-classed but missing a record for "
                    f"{engine}/{scenario}")

    for engine, scenarios in record_dates_by_engine_scenario.items():
        for scenario, dates in scenarios.items():
            for date in sorted(dates):
                if date in days and date not in classified_dates:
                    problems.append(
                        f"{date}: has a record for {engine}/{scenario} but "
                        "is not TP/FP-classed in day_strata")

    return sorted(set(problems))
