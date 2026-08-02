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
from itsf.s0 import context as s0_context
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


def _is_unresolved(value: object) -> bool:
    """True iff `value` is one of THIS module's own UNRESOLVED markers (the
    bare sentinel, or a decision-tagged "UNRESOLVED_..." string). Used only
    to DERIVE `formal_sealable` below — it never changes what a field's
    value actually is, and it never resolves anything itself."""
    return value is UNRESOLVED or (isinstance(value, str)
                                   and value.startswith("UNRESOLVED"))


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

# Frozen F10 vocabulary (IR-12/18): a concrete category from the SAME
# single-sourced `s0_context.F10_CATEGORIES` tuple, or the literal "none"
# (zero-category day), or None (NA on a multi-category conflict — see
# `s0_context.EventCalendar.encode_f10`). "none_or_na" or any other spelling
# is NOT part of this vocabulary and is rejected below.
_EVENT_FLAG_VALUES = frozenset(s0_context.F10_CATEGORIES) | {"none"}


def _theta_key(theta: float) -> str:
    """Kept in sync with `s0.study.theta_key` BY CONVENTION (both format the
    frozen theta values identically: "theta_0.5" / "theta_0.3"); duplicated
    rather than imported so this schema-only module stays decoupled from the
    day-set-selection layer (`s0/study.py`)."""
    return f"theta_{theta:g}"


def _epoch_for_year(year: int) -> str:
    """Epoch label for `year`, read from the SAME frozen bucket boundaries
    `s0_stability.py` uses (`EPOCHS` / `OUTSIDE_EPOCHS`) — the boundary
    VALUES are single-sourced from that module's public constants; only this
    trivial lookup loop is (deliberately) duplicated, exactly the way
    `_theta_key` above duplicates a formatting convention rather than an
    import."""
    for label, lo, hi in s0_stability.EPOCHS:
        if lo <= year <= hi:
            return label
    return s0_stability.OUTSIDE_EPOCHS


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
    # Descending order: THETA NESTING MONOTONICITY is checked on adjacent
    # pairs (higher, lower) below — a day TP at the higher theta must also be
    # TP at the lower one (Y_cont >= hi implies Y_cont >= lo), so the TP set
    # only grows as theta falls. Checking adjacent pairs of the full sorted
    # sequence covers every pair transitively.
    theta_keys_desc = tuple(_theta_key(t) for t in sorted(thetas, reverse=True))

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

        year_str = str(row["year"])
        if year_str != date[:4]:
            raise ValueError(
                f"{date}: year {year_str!r} != the year implied by the date "
                f"itself ({date[:4]!r}) — date/year consistency violated")
        try:
            year_int = int(year_str)
        except ValueError:
            raise ValueError(
                f"{date}: year {year_str!r} is not an integer") from None
        expected_epoch = _epoch_for_year(year_int)
        if epoch != expected_epoch:
            raise ValueError(
                f"{date}: stability_epoch {epoch!r} does not match the "
                f"epoch computed from year {year_int} ({expected_epoch!r}) "
                "via the frozen S0 §2 buckets 2010-2013/2014-2017/2018-2021 "
                "(or 'outside_epochs') — year/epoch consistency violated")

        event_flag_final = row["event_flag_final"]
        if event_flag_final is not None and event_flag_final not in _EVENT_FLAG_VALUES:
            raise ValueError(
                f"{date}: event_flag_final {event_flag_final!r} is not one "
                f"of {sorted(_EVENT_FLAG_VALUES)} or None (frozen F10 "
                "vocabulary, IR-12/18 via itsf.s0.context.F10_CATEGORIES) — "
                "e.g. 'none_or_na' is NOT a valid value; NA is represented "
                "by None only")

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

        if d_open == 0:
            not_non_tradeable = {k: v for k, v in tp_fp_class.items()
                                 if v != "non_tradeable"}
            if not_non_tradeable:
                raise ValueError(
                    f"{date}: d_open == 0 (no direction) requires "
                    f"tp_fp_class == 'non_tradeable' for EVERY theta, got "
                    f"{not_non_tradeable} — frozen S0 §5 no-direction days "
                    "are not Oracle days")

        for hi_key, lo_key in zip(theta_keys_desc, theta_keys_desc[1:]):
            if tp_fp_class[hi_key] == "TP" and tp_fp_class[lo_key] != "TP":
                raise ValueError(
                    f"{date}: THETA NESTING MONOTONICITY violated — "
                    f"tp_fp_class[{hi_key!r}] == 'TP' but "
                    f"tp_fp_class[{lo_key!r}] == {tp_fp_class[lo_key]!r}; "
                    "the TP set at a HIGHER theta must be a SUBSET of the "
                    "TP set at a LOWER theta (Y_cont >= hi implies "
                    "Y_cont >= lo)")

        days[date] = {
            "micro_execution_era": era,
            "stability_epoch": epoch,
            "year": year_str,
            "d_open": d_open,
            "event_flag_final": event_flag_final,
            "event_na": event_flag_final is None,
            # DR-M6-F: the event -> Appendix-A stratum MAPPING is open, not
            # just its NA branch, so every day gets the same marker.
            "event_stratum": _unresolved("DR-M6-F"),
            "vol_status": str(row["vol_status"]),
            "tp_fp_class": {k: tp_fp_class[k] for k in theta_keys},
        }

    # formal_sealable: False whenever ANY artifact-level field is still an
    # UNRESOLVED marker (today: event_stratum, always, until DR-M6-F closes)
    # — a disclosed refusal flag for whatever "formal path" later seals these
    # artifacts for MC, never a silent pass.
    # LOW-3 (M6.1.1 audit): an EMPTY artifact is never sealable — the
    # vacuous-truth reading would let a zero-day strata self-declare.
    formal_sealable = bool(days) and not any(
        _is_unresolved(row["event_stratum"])
                              for row in days.values())

    return {
        "schema_version": SCHEMA_VERSION,
        "ordering": "sorted-by-date",
        "formal_sealable": formal_sealable,
        "days": days,
    }


# ===========================================================================
# E6b — build_grid_samples
# ===========================================================================

# run_meta is no longer an opaque passthrough: it is exactly which
# theta/engine/scenario this ONE grid belongs to (build_grid is always
# called for ONE engine x cost-scenario x theta), and `verify_handoff_
# conservation` now reads `run_meta["theta"]` to check the PER-THETA TP/FP
# classification, so its shape must be pinned rather than caller-defined.
_REQUIRED_RUN_META: dict[str, tuple[type, ...]] = {
    "theta": (int, float),
    "engine": (str,),
    "scenario": (str,),
}


def _validated_run_meta(run_meta: Mapping[str, object]) -> dict[str, object]:
    unknown = sorted(set(run_meta) - set(_REQUIRED_RUN_META))
    if unknown:
        raise ValueError(
            f"run_meta has unknown key(s) {unknown} — only "
            f"{sorted(_REQUIRED_RUN_META)} are recognised (unknown keys are "
            "rejected rather than silently passed through)")
    missing = [k for k in _REQUIRED_RUN_META if k not in run_meta]
    if missing:
        raise ValueError(f"run_meta is missing required key(s) {missing} "
                         f"(needs {sorted(_REQUIRED_RUN_META)})")
    out: dict[str, object] = {}
    for key, types in _REQUIRED_RUN_META.items():
        value = run_meta[key]
        if isinstance(value, bool) or not isinstance(value, types):
            raise ValueError(
                f"run_meta[{key!r}] must be one of {types}, got {value!r} "
                f"({type(value).__name__})")
        out[key] = float(value) if key == "theta" else value
    return out


def build_grid_samples(grid_output: Mapping[str, object],
                       run_meta: Mapping[str, object]) -> dict[str, object]:
    """Wrap one `gridmix.build_grid(...)` output into the MC handoff shape.

    Parameters
    ----------
    grid_output
        the return value of `gridmix.build_grid` (or `_build_grid_unchecked`
        in a test) for ONE engine x cost-scenario x theta.
    run_meta
        provenance for which theta/engine/scenario this grid belongs to.
        Required keys, validated and normalised (unknown keys rejected):
        `"theta"` (int or float, stored as float), `"engine"` (str),
        `"scenario"` (str). Pinned (rather than an opaque caller-defined
        blob) because `verify_handoff_conservation` reads `run_meta["theta"]`
        to check per-theta TP/FP conservation against day_strata.

    Returns
    -------
    {"schema_version", "formal_sealable", "cells": {cell_key: {
        "per_seed": {seed: {...}}, "infeasible_by_sample", "q_mil", "r_mil"}},
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
    validated_run_meta = _validated_run_meta(run_meta)
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

    replay = {
        "stream_formula":
            "default_rng([master, GRID_STREAM_TAG, q_mil, r_mil])",
        "grid_stream_tag": s0_gridmix.GRID_STREAM_TAG,
        "k_policy": _unresolved("DR-M6-E"),
        "crn_scope": str(UNRESOLVED),
    }
    formal_sealable = not (_is_unresolved(replay["k_policy"])
                          or _is_unresolved(replay["crn_scope"]))

    return {
        "schema_version": SCHEMA_VERSION,
        "formal_sealable": formal_sealable,
        "cells": cells,
        "run_meta": validated_run_meta,
        "replay": replay,
    }


# ===========================================================================
# E6c — build_seed_manifest
# ===========================================================================

def build_seed_manifest() -> dict[str, object]:
    """The frozen seed/stream provenance MC needs to replay S0's randomness,
    read from the modules that own each constant (never a second copy)."""
    # IR DR-02 single-source guard: stats.py / gridmix.py must be
    # re-exporting the SAME object as contracts.RESEARCH_BOOTSTRAP_SEEDS, not
    # a local copy that could silently drift. A production governance gate
    # must be a real `raise`, never a bare `assert` — `python -O` strips
    # `assert` statements, which would silently disable this exact check.
    if s0_stats.RESEARCH_BOOTSTRAP_SEEDS is not contracts.RESEARCH_BOOTSTRAP_SEEDS:
        raise AssertionError(
            "itsf.s0.stats.RESEARCH_BOOTSTRAP_SEEDS is not the SAME object "
            "as contracts.RESEARCH_BOOTSTRAP_SEEDS — IR DR-02 single-source "
            "mutation guard tripped (a local copy would silently drift from "
            "the one research-seed source of truth)")
    if s0_gridmix.RESEARCH_BOOTSTRAP_SEEDS is not contracts.RESEARCH_BOOTSTRAP_SEEDS:
        raise AssertionError(
            "itsf.s0.gridmix.RESEARCH_BOOTSTRAP_SEEDS is not the SAME "
            "object as contracts.RESEARCH_BOOTSTRAP_SEEDS — IR DR-02 "
            "single-source mutation guard tripped")

    k_policy = _unresolved("DR-M6-E")
    crn_scope = str(UNRESOLVED)
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_sealable": not (_is_unresolved(k_policy)
                               or _is_unresolved(crn_scope)),
        "research_bootstrap_seeds": list(contracts.RESEARCH_BOOTSTRAP_SEEDS),
        "quoted_seed_convention": (
            "quoted interval/selection = the FIRST frozen master seed, by "
            "fixed convention that predates any data (never best-of); all "
            "seeds are independently run and always reported in full"),
        "stream_tags": {
            "stats_stream_tag": s0_stats.STATS_STREAM_TAG,
            "grid_stream_tag": s0_gridmix.GRID_STREAM_TAG,
        },
        "k_policy": k_policy,
        "crn_scope": crn_scope,
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
    through the hash so a large .jsonl handoff never needs two full passes.

    `line_count` counts LINES, not `\\n` bytes: for a well-formed JSONL body
    (every line, including the last, ends with `\\n`) those are the same
    number, but a body with NO trailing newline has one more line than it
    has `\\n` bytes (the final, unterminated line still counts), and a
    completely empty body has zero lines even though "ends with `\\n`" is
    vacuously false for it. Both edges are pinned: empty body -> 0; N lines
    with no trailing newline -> N.
    """
    manifest: dict[str, object] = {}
    for name, path in files.items():
        digest = hashlib.sha256()
        n_bytes = 0
        n_newlines = 0
        last_byte = b""
        is_jsonl = str(path).endswith(".jsonl")
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
                n_bytes += len(chunk)
                if is_jsonl:
                    n_newlines += chunk.count(b"\n")
                    last_byte = chunk[-1:]
        entry: dict[str, object] = {"sha256": digest.hexdigest(),
                                    "bytes": n_bytes}
        if is_jsonl:
            if n_bytes == 0:
                n_lines = 0
            elif last_byte == b"\n":
                n_lines = n_newlines
            else:
                n_lines = n_newlines + 1        # trailing unterminated line
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
    1b. PER-THETA marker agreement: `grid_samples["run_meta"]["theta"]`
       names which theta this grid_samples bundle is FOR (build_grid_samples
       always attaches it — see `_validated_run_meta`); every date a grid
       sample marks as a tp-marker must be classed "TP" in day_strata for
       THAT theta (not merely "TP for some theta"), and every fp-marker date
       must be classed "FP" for that SAME theta. A swapped TP/FP marker pair
       is caught here even though the OLD "any theta" check in #3 below
       would have missed it.
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

    if grid_dates:
        run_meta = grid_samples.get("run_meta")
        if not isinstance(run_meta, Mapping) or "theta" not in run_meta:
            raise ValueError(
                "grid_samples['run_meta']['theta'] is required to check "
                "PER-THETA TP/FP conservation (build_grid_samples always "
                "attaches it); a grid_samples without it cannot be "
                "cross-checked against day_strata's per-theta tp_fp_class "
                "— fail closed rather than silently skip the check")
        theta_key = _theta_key(float(run_meta["theta"]))
        for cell in grid_samples.get("cells", {}).values():
            for block in cell.get("per_seed", {}).values():
                for date in block.get("tp_dates", ()):
                    row = days.get(date)
                    if row is None:
                        continue          # already reported above (check 1)
                    actual = row.get("tp_fp_class", {}).get(theta_key)
                    if actual != "TP":
                        problems.append(
                            f"{date}: grid sample marks it a TP date for "
                            f"{theta_key} but day_strata classifies it "
                            f"{actual!r} for {theta_key}")
                for date in block.get("fp_dates", ()):
                    row = days.get(date)
                    if row is None:
                        continue
                    actual = row.get("tp_fp_class", {}).get(theta_key)
                    if actual != "FP":
                        problems.append(
                            f"{date}: grid sample marks it an FP date for "
                            f"{theta_key} but day_strata classifies it "
                            f"{actual!r} for {theta_key}")

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
