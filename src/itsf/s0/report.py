"""S0 formal-report boundary (M6.1 Track E2+E3).

Scope: this module owns exactly the pieces the formal S0 report needs
before Stage E may seal anything (S0_REPORT_CONTENT_CONTRACT.md;
M6_HOLD_RESPONSE.md items 2 and 10):

  1. `record_to_formal_dict` / `to_formal_json` — the FROZEN §10.1 atomic-
     record serialization and a hard-failing (never silently-stringifying)
     JSON encoder for the sealed release.
  2. `split_envelope` — the internal/formal payload split (M6_HOLD_RESPONSE
     item 2's "oracle_daily -> study drift" defect: the formal side is
     keyed EXACTLY by the contract's A-keys at the top level, nothing lives
     one level down inside a "study" wrapper, and no live object — dataset,
     TradePathRecord, DataFrame, ... — may cross into it).
  3. `validate_formal_payload` / `validate_sealed_files` — the machine gate
     S0_REPORT_CONTENT_CONTRACT.md §B describes; ANY problem in the
     returned list means Stage E must refuse to seal (fail-closed).

This module does not render anything and does not decide what numbers go
into a study payload — it is the boundary that either lets a payload
through onto disk or explains, in a flat list of strings, exactly why not.
No real data is loaded here and nothing in this file consumes researcher
exposure; every function is a pure transform/check over plain Python
objects supplied by the caller.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from itsf.s0.dataset import ERA_ACTUAL, ERA_PROXY
from itsf.s0.study import ENGINES

# ---------------------------------------------------------------------------
# 1. frozen top-level section keys (S0_REPORT_CONTENT_CONTRACT.md §A1-A12,
#    plus A2b stability_views per M6_HOLD_RESPONSE.md item 3). VERBATIM and
#    FROZEN to this exact tuple — a change here is an interface break that
#    only the main agent may make.
# ---------------------------------------------------------------------------
FORMAL_SECTIONS: tuple[str, ...] = (
    "structural", "oracle_daily", "theoretical_oracle", "e2_worst_days",
    "sizing_outputs", "frequency", "stability_views", "bootstrap_ci",
    "feasibility_grid", "mc_handoff_manifest", "era_axis", "disclosures",
    "governance",
)

# Keys that stay OFF the sealed formal release (numbers-bearing but never
# published verbatim; Stage-D integrity adapters and record objects live
# here — `split_envelope` moves them here, never into a FORMAL_SECTIONS key).
_INTERNAL_KEYS: tuple[str, ...] = (
    "dataset", "na_reason_counts", "reported_total_na", "records",
)

# --- grid axes reused by the validator (frozen citations; ENGINES/ERA_* are
#     imported so this module can never drift from the single source of
#     truth already frozen in study.py / dataset.py). ------------------------
_SCENARIOS: tuple[str, ...] = ("Base", "Conservative", "Stress", "Severe")
# frozen: S0 §6 (four cost scenarios)
_BLOCKS: tuple[int, ...] = (5, 21)
# frozen: S0 §9 (Primary block 5 trading days / Sensitivity block 21)
_ERAS: tuple[str, ...] = (ERA_PROXY, ERA_ACTUAL)
# frozen: S0 §6 L109-115 (counterfactual_micro_execution / actual era)
_EPOCHS: tuple[str, ...] = ("2010-2013", "2014-2017", "2018-2021")
# frozen: S0 §2 (three stability epochs — M6_HOLD_RESPONSE.md item 3)
_DIRECTIONS: tuple[str, ...] = ("+1", "-1")
# frozen: S0 §2 (多空分开 — long/short split)
FROZEN_N_BOOT = 10_000
# frozen: S0 §9 (10,000 resamples)


# ---------------------------------------------------------------------------
# 2. record_to_formal_dict — FROZEN §10.1 field names
# ---------------------------------------------------------------------------
_TS_RENAME = {"entry_ts": "entry_timestamp", "exit_ts": "exit_timestamp"}

# frozen: S0 §10.1 atomic per-contract intraday trade path — trade_date,
# entry_timestamp/exit_timestamp (renamed from entry_ts/exit_ts), direction,
# entry_fill, exit_fill, final_pnl_per_contract, mtm_close_pnl_1m,
# mtm_adverse_pnl_1m, max_adverse_pnl, max_favourable_pnl,
# time_of_max_adverse, planned_stop, actual_stop_fill, stop_triggered —
# PLUS the four M6.1 extension fields already carried on
# contracts.TradePathRecord: engine, cost_scenario, sizing_anchor_usd,
# ambiguous_stop_vs_floor. Every non-timestamp name is verbatim.
FORMAL_RECORD_FIELDS: tuple[str, ...] = (
    "trade_date", "engine", "cost_scenario", "direction",
    "entry_timestamp", "exit_timestamp", "entry_fill", "exit_fill",
    "final_pnl_per_contract", "mtm_close_pnl_1m", "mtm_adverse_pnl_1m",
    "max_adverse_pnl", "max_favourable_pnl", "time_of_max_adverse",
    "planned_stop", "actual_stop_fill", "stop_triggered",
    "sizing_anchor_usd", "ambiguous_stop_vs_floor",
)


def record_to_formal_dict(rec) -> dict:
    """TradePathRecord (or an equivalent plain dict) -> the FROZEN §10.1
    formal-record dict.

    `entry_ts`/`exit_ts` are renamed to `entry_timestamp`/`exit_timestamp`;
    every other field keeps its internal name. Raises ValueError if the
    resulting field set is not EXACTLY `FORMAL_RECORD_FIELDS` (no silent
    drop, no silent extra) and TypeError if `rec` is neither a dataclass
    instance nor a plain dict. Key order in the returned dict is
    deterministic (alphabetically sorted).
    """
    if is_dataclass(rec) and not isinstance(rec, type):
        raw = asdict(rec)
    elif isinstance(rec, dict):
        raw = dict(rec)
    else:
        raise TypeError(
            "record_to_formal_dict: expected a TradePathRecord dataclass "
            f"instance or a plain dict, got {type(rec).__name__}")
    renamed = {_TS_RENAME.get(k, k): v for k, v in raw.items()}
    got, want = set(renamed), set(FORMAL_RECORD_FIELDS)
    if got != want:
        raise ValueError(
            "record_to_formal_dict: field set mismatch vs frozen S0 §10.1 "
            f"— missing={sorted(want - got)} extra={sorted(got - want)}")
    return {k: renamed[k] for k in sorted(renamed)}


# ---------------------------------------------------------------------------
# 3. to_formal_json — strict serializer, no silent stringification
# ---------------------------------------------------------------------------
class _StrictEncoder(json.JSONEncoder):
    """Defense-in-depth only: `_clean` (below) already rejects every
    disallowed type/key/non-finite-float BEFORE `json.dumps` ever runs, so
    `default` should never actually fire on a `_clean`-ed tree. It exists so
    a stray type that somehow reaches `json.dumps` still gets a hard raise
    instead of any `str(...)` fallback."""

    def default(self, o):
        raise TypeError(
            f"to_formal_json: unsupported type reached the encoder: "
            f"{type(o).__name__} (no default=str fallback — fix the "
            "producer, or fix `_clean` if this type should be rejected "
            "earlier)")


def _clean(obj, path: str = "$"):
    """Validate + copy `obj` into a JSON-safe tree (tuple -> list).

    Allowed leaf/container types: dict (str keys only), list, tuple, str,
    int, bool, None, and FINITE float. Anything else raises — TypeError for
    a disallowed type or a non-str dict key, ValueError for a non-finite
    float — a hard failure, never a `default=str` fallback. Reused by
    `split_envelope` (validation only; the transformed copy is discarded
    there) so the two callers can never drift into different type policies.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"to_formal_json: dict key at {path} must be str, got "
                    f"{type(key).__name__}: {key!r}")
            cleaned[key] = _clean(value, f"{path}.{key}")
        return cleaned
    if isinstance(obj, (list, tuple)):
        return [_clean(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, bool) or obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(
                f"to_formal_json: non-finite float at {path}: {obj!r}")
        return obj
    if isinstance(obj, int):
        return obj
    raise TypeError(
        f"to_formal_json: unsupported type at {path}: {type(obj).__name__} "
        "(no default=str fallback — fix the producer)")


def to_formal_json(obj) -> str:
    """Strict JSON serialization for the sealed formal release.

    `sort_keys=True, indent=1, allow_nan=False` and NO `default=` fallback:
    anything that is not a plain dict/list/tuple/str/int/bool/None/finite
    float is a hard raise (M6_HOLD_RESPONSE.md item 2's `default=str` /
    `n_boot=40` leak class of defect). Non-finite floats are rejected by an
    explicit `math.isfinite` walk (`_clean`) BEFORE `json.dumps` runs;
    `allow_nan=False` on the dumps call is a redundant second net, not the
    primary guard (and the walk also catches things allow_nan alone would
    not — e.g. a bool/int/float/None dict key, which `json.dumps` would
    otherwise silently stringify rather than reject).
    """
    cleaned = _clean(obj)
    return json.dumps(cleaned, cls=_StrictEncoder, sort_keys=True, indent=1,
                      allow_nan=False)


# ---------------------------------------------------------------------------
# 4. split_envelope — internal vs formal payload split
# ---------------------------------------------------------------------------
def split_envelope(compute_result: dict) -> tuple[dict, dict]:
    """Split a Stage-C compute result into (internal, formal).

    internal = whichever of {"dataset", "na_reason_counts",
    "reported_total_na", "records"} are present in `compute_result`
    (objects allowed — this side never reaches Stage E's sealed release).

    formal = whichever of `FORMAL_SECTIONS` are present, UNCHANGED (a
    section simply absent from `compute_result` stays simply absent here
    too — `validate_formal_payload` is what reports that as a problem;
    this function never invents a placeholder section).

    Raises TypeError/ValueError (via the same strict-type walk `to_formal_
    json` uses) if any FORMAL_SECTIONS value contains anything other than
    plain dict/list/tuple/str/int/bool/None/finite-float — in particular a
    raw dataset object or a TradePathRecord instance can never reach the
    formal side; the fix is to keep such data on the internal side or
    convert it (e.g. via `record_to_formal_dict`) before it enters
    `compute_result` under a FORMAL_SECTIONS key.
    """
    if not isinstance(compute_result, dict):
        raise TypeError(
            "split_envelope: compute_result must be a dict, got "
            f"{type(compute_result).__name__}")
    internal = {k: compute_result[k] for k in _INTERNAL_KEYS
               if k in compute_result}
    formal: dict = {}
    for key in FORMAL_SECTIONS:
        if key not in compute_result:
            continue
        value = compute_result[key]
        _clean(value, path=f"${key}")          # raises on any non-plain object
        formal[key] = value
    return internal, formal


# ---------------------------------------------------------------------------
# 5. validate_formal_payload — S0_REPORT_CONTENT_CONTRACT.md §B, rules R1-R10
# ---------------------------------------------------------------------------
def _walk_r8(obj, path: str, problems: list[str]) -> None:
    """Rule R8: whole-payload scan for a non-finite float, a non-str dict
    key, a stringified-object leak ("...object at 0x..."), or a literal
    "dataset" key anywhere in the tree (not just at the top level)."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "dataset":
                problems.append(f"dataset_key_present:{path}.{key}")
            if not isinstance(key, str):
                problems.append(f"non_str_key:{path}:{key!r}")
                _walk_r8(value, f"{path}.<{key!r}>", problems)
                continue
            _walk_r8(value, f"{path}.{key}", problems)
        return
    if isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            _walk_r8(value, f"{path}[{i}]", problems)
        return
    if isinstance(obj, bool) or obj is None or isinstance(obj, int):
        return
    if isinstance(obj, float):
        if not math.isfinite(obj):
            problems.append(f"non_finite_float:{path}")
        return
    if isinstance(obj, str):
        if "object at 0x" in obj:
            problems.append(f"object_repr_leak:{path}")
        return
    # `split_envelope`/`to_formal_json` already reject every other type
    # before a payload reaches this validator; this is a defensive net so
    # a hand-built or malformed payload degrades to a problem, not a crash.
    problems.append(f"unexpected_type:{path}:{type(obj).__name__}")


def validate_formal_payload(payload) -> list[str]:
    """S0_REPORT_CONTENT_CONTRACT.md §B machine check, rules R1-R10.

    Returns a flat list of problem strings; EMPTY means sealable. Never
    raises on a malformed payload — every rule below degrades to a problem
    string instead (a validator that can crash is not a fail-closed gate).
    """
    if not isinstance(payload, dict):
        return ["payload_not_dict"]

    problems: list[str] = []

    # R1 — every section present, non-empty, and a dict.
    for key in FORMAL_SECTIONS:
        if key not in payload:
            problems.append(f"missing_section:{key}")
        elif not isinstance(payload[key], dict):
            problems.append(f"wrong_type:{key}")
        elif not payload[key]:
            problems.append(f"empty_section:{key}")
    if problems:
        # deeper rules assume every section exists and is a non-empty dict;
        # fail closed on the coarse defect rather than risk KeyError noise.
        return problems

    tkeys = sorted(payload["oracle_daily"])
    if len(tkeys) != 2:
        problems.append(f"theta_axis_count:{tkeys}")

    # R2 + R3 — bootstrap_ci grid + per-cell shape.
    expected_ci = {f"{t}|{e}|{s}|block{b}"
                   for t in tkeys for e in ENGINES for s in _SCENARIOS
                   for b in _BLOCKS}
    actual_ci = set(payload["bootstrap_ci"])
    for k in sorted(expected_ci - actual_ci):
        problems.append(f"bootstrap_ci_missing:{k}")
    for k in sorted(actual_ci - expected_ci):
        problems.append(f"bootstrap_ci_extra:{k}")
    for key in sorted(expected_ci & actual_ci):
        blk = int(key.rsplit("block", 1)[1])
        cell = payload["bootstrap_ci"][key]
        if not isinstance(cell, dict):
            problems.append(f"bootstrap_ci_cell_type:{key}")
            continue
        per_seed = cell.get("per_seed")
        # Key TYPE is deliberately not pinned: stats.bootstrap_mean_ci's
        # native return uses int seed keys, but a sealed (JSON-safe) payload
        # can only use str keys (to_formal_json hard-rejects a non-str dict
        # key) — so a payload that is ALREADY sealable must use "7"/"13"/
        # "31" string keys. Both are accepted here and normalised to the
        # seed IDENTITY (int) for the {7,13,31} comparison; only the key's
        # value, never its str/int type, is what R3 actually cares about.
        if isinstance(per_seed, dict):
            try:
                seeds = sorted(int(k) for k in per_seed)
            except (TypeError, ValueError):
                seeds = None
        else:
            seeds = None
        if seeds != [7, 13, 31]:
            problems.append(f"bootstrap_ci_seeds:{key}")
        if cell.get("quoted_seed") != 7:
            problems.append(f"bootstrap_ci_quoted_seed:{key}")
        for seed in (7, 13, 31):
            entry = None
            if isinstance(per_seed, dict):
                entry = per_seed.get(seed, per_seed.get(str(seed)))
            if not isinstance(entry, dict):
                problems.append(f"bootstrap_ci_seed_entry:{key}:{seed}")
                continue
            if entry.get("n_boot") != FROZEN_N_BOOT:
                problems.append(f"bootstrap_ci_n_boot:{key}:{seed}")
            if entry.get("block_len") != blk:
                problems.append(f"bootstrap_ci_block_len:{key}:{seed}")
            lo, hi = entry.get("ci_lo"), entry.get("ci_hi")
            bounds_ok = (
                isinstance(lo, (int, float)) and not isinstance(lo, bool)
                and isinstance(hi, (int, float)) and not isinstance(hi, bool)
                and math.isfinite(lo) and math.isfinite(hi) and lo <= hi)
            if not bounds_ok:
                problems.append(f"bootstrap_ci_bounds:{key}:{seed}")

    # R4 — oracle_daily / e2_worst_days / sizing_outputs / frequency.
    for section in ("oracle_daily", "e2_worst_days", "sizing_outputs",
                    "frequency"):
        if sorted(payload[section]) != tkeys:
            problems.append(f"theta_keys_mismatch:{section}")

    for tkey in tkeys:
        for scn in _SCENARIOS:
            eng_block = payload["e2_worst_days"].get(tkey, {})
            cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                    else None)
            if not isinstance(cell, dict):
                problems.append(f"e2_worst_days_missing:{tkey}|{scn}")
                continue
            pooled = cell.get("pooled")
            if (not isinstance(pooled, dict) or "P1" not in pooled
                    or "P5" not in pooled):
                problems.append(f"e2_worst_days_pooled:{tkey}|{scn}")
            by_era = cell.get("by_era")
            if (not isinstance(by_era, dict)
                    or sorted(by_era) != sorted(_ERAS)):
                problems.append(f"e2_worst_days_by_era:{tkey}|{scn}")
            else:
                for era in _ERAS:
                    era_cell = by_era.get(era, {})
                    if (not isinstance(era_cell, dict)
                            or "P1" not in era_cell or "P5" not in era_cell):
                        problems.append(
                            f"e2_worst_days_by_era_p1p5:{tkey}|{scn}|{era}")

    for tkey in tkeys:
        cell = payload["sizing_outputs"].get(tkey, {})
        for label in ("rows", "coverage"):
            block = cell.get(label) if isinstance(cell, dict) else None
            if not isinstance(block, dict):
                problems.append(f"sizing_outputs_{label}_missing:{tkey}")
                continue
            for eng in ENGINES:
                eng_block = block.get(eng)
                if not isinstance(eng_block, dict):
                    problems.append(
                        f"sizing_outputs_{label}_cell_missing:{tkey}|{eng}")
                    continue
                for scn in _SCENARIOS:
                    if scn not in eng_block:
                        problems.append(
                            f"sizing_outputs_{label}_cell_missing:"
                            f"{tkey}|{eng}|{scn}")

    # R5 — stability_views (M6_HOLD_RESPONSE.md item 3 / frozen S0 §2).
    for tkey in tkeys:
        for eng in ENGINES:
            for scn in _SCENARIOS:
                eng_block = payload["stability_views"].get(tkey, {})
                eng_block = (eng_block.get(eng)
                            if isinstance(eng_block, dict) else None)
                cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                        else None)
                if not isinstance(cell, dict):
                    problems.append(
                        f"stability_views_missing:{tkey}|{eng}|{scn}")
                    continue
                epochs = cell.get("epochs")
                # structural extras allowed: outside_epochs bucket (days
                # beyond the three frozen epochs, disclosed not dropped)
                # and the per-axis conservation flag.
                if (not isinstance(epochs, dict)
                        or not set(_EPOCHS) <= set(epochs)
                        or not set(epochs) <= (set(_EPOCHS)
                                               | {"outside_epochs",
                                                  "conservation_ok"})):
                    problems.append(
                        f"stability_views_epochs:{tkey}|{eng}|{scn}")
                if not cell.get("by_year"):
                    problems.append(
                        f"stability_views_by_year:{tkey}|{eng}|{scn}")
                if not cell.get("leave_one_year_out"):
                    problems.append(
                        f"stability_views_loyo:{tkey}|{eng}|{scn}")
                by_dir = cell.get("by_direction")
                if (not isinstance(by_dir, dict)
                        or not set(_DIRECTIONS) <= set(by_dir)
                        or not set(by_dir) <= (set(_DIRECTIONS)
                                               | {"conservation_ok"})):
                    problems.append(
                        f"stability_views_by_direction:{tkey}|{eng}|{scn}")
                vol = cell.get("vol_terciles")
                if not isinstance(vol, dict):
                    problems.append(
                        f"stability_views_vol_terciles:{tkey}|{eng}|{scn}")
                elif vol.get("status") == "unresolved":
                    # frozen S0 §2 vol axis blocked on DR-M6-B — sealing
                    # must fail closed until the sub-definition ruling lands.
                    problems.append("vol_axis_unresolved")

    # R6 — disclosures.pending_method_decisions must be empty to seal.
    if payload["disclosures"].get("pending_method_decisions"):
        problems.append("pending_method_decisions_unresolved")

    # R7 — governance.
    gov = payload["governance"]
    trial_id = gov.get("trial_id")
    if not isinstance(trial_id, str) or not trial_id:
        problems.append("governance_trial_id")
    commit = gov.get("authorized_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}",
                                                        commit or ""):
        problems.append("governance_authorized_commit")
    seed = gov.get("engineering_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        problems.append("governance_engineering_seed")
    hashes = gov.get("frozen_hashes")
    if not isinstance(hashes, dict) or len(hashes) != 7:
        problems.append("governance_frozen_hashes_count")
    else:
        for hpath, hval in hashes.items():
            if (not isinstance(hpath, str) or not isinstance(hval, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", hval)):
                problems.append(f"governance_frozen_hash_format:{hpath}")
    seq = gov.get("registry_sequence_snapshot")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        problems.append("governance_registry_sequence_snapshot")

    # R9 — mc_handoff_manifest counts grid.
    counts = payload["mc_handoff_manifest"].get("counts")
    if not isinstance(counts, dict):
        problems.append("mc_handoff_manifest_counts_missing")
    else:
        for eng in ENGINES:
            eng_block = counts.get(eng)
            for scn in _SCENARIOS:
                cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                        else None)
                if not isinstance(cell, dict) or "n_records" not in cell:
                    problems.append(
                        f"mc_handoff_manifest_counts_missing:{eng}|{scn}")
                    continue
                n = cell["n_records"]
                if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                    problems.append(
                        f"mc_handoff_manifest_counts_invalid:{eng}|{scn}")

    # R10 — feasibility_grid.
    fg = payload["feasibility_grid"]
    if not fg.get("cells"):
        problems.append("feasibility_grid_cells_empty")
    if fg.get("regions", {}).get("status") != "pending_mc":
        problems.append("feasibility_grid_regions_not_pending_mc")

    # R8 — whole-payload walk (runs last so the section-shape problems above
    # are reported with their own, more specific codes first).
    _walk_r8(payload, "$", problems)

    # O2: A2 matrix completeness + A9 record-count conservation
    od = payload.get("oracle_daily")
    mh = payload.get("mc_handoff_manifest")
    if isinstance(od, dict) and isinstance(mh, dict):
        counts = mh.get("counts", {})
        for tkey, tcell in od.items():
            ex = tcell.get("executable") if isinstance(tcell, dict) else None
            uni = tcell.get("day_universe") if isinstance(tcell, dict) else {}
            n_exp = None
            if isinstance(uni, dict):
                try:
                    n_exp = int(uni["n_tp"]) + int(uni["n_fp"])
                except Exception:
                    n_exp = None
            for eng in ENGINES:
                for scn in _SCENARIOS:
                    if isinstance(ex, dict) and scn not in ex.get(eng, {}):
                        problems.append(f"oracle_daily_cell:{tkey}|{eng}|{scn}")
                    n_rec = (counts.get(eng, {}).get(scn, {})
                             .get("n_records"))
                    if n_exp is not None and n_rec != n_exp:
                        problems.append(
                            f"records_conservation:{tkey}|{eng}|{scn}:"
                            f"{n_rec}!={n_exp}")
    return problems


# FROZEN §10.1 names every sealed JSONL line must carry (leak check).
_FROZEN_LINE_FIELDS: tuple[str, ...] = ("entry_timestamp",
                                        "exit_timestamp", "trade_date")
# Internal names that must NEVER appear on a sealed line (leak check).
_INTERNAL_NAME_LEAK: tuple[str, ...] = ("entry_ts", "exit_ts")


def validate_sealed_files(files: Mapping[str, str], payload, *,
                          trade_date_universe=None) -> list[str]:
    """Verify the sealed JSONL bodies against `payload["mc_handoff_manifest"]
    ["files"]` (name -> {"file", "n_records", "sha256"}).

    For every manifest entry: the named file must be present in `files`;
    its sha256 (of the UTF-8 bytes) must match; its line count must equal
    `n_records`; and every line must parse as a JSON object carrying the
    FROZEN §10.1 `entry_timestamp`/`exit_timestamp`/`trade_date` names (an
    internal `entry_ts`/`exit_ts` name anywhere on a line is flagged as a
    leak, never silently accepted as a synonym).

    `trade_date_universe`: the contract wants every sealed trade_date to
    lie inside the union of the oracle_daily TP/FP day universes, but the
    M6.1 formal `oracle_daily` nested shape is not yet nailed down (see this
    module's `unresolved` report for the interface request). Rather than
    guess a key convention that might not match the final contract, that
    check is exposed as an EXPLICIT optional day-set argument: pass any
    iterable of "YYYY-MM-DD" strings to enable the containment check; omit
    it (default) to skip that one sub-check.
    """
    problems: list[str] = []
    manifest = (payload.get("mc_handoff_manifest", {})
               if isinstance(payload, dict) else {})
    file_specs = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(file_specs, dict) or not file_specs:
        return ["mc_handoff_manifest_files_missing"]

    universe = (set(trade_date_universe)
               if trade_date_universe is not None else None)
    seen_dates: set[str] = set()

    for name, spec in file_specs.items():
        if not isinstance(spec, dict):
            problems.append(f"sealed_file_spec_type:{name}")
            continue
        fname = spec.get("file")
        want_sha = spec.get("sha256")
        want_n = spec.get("n_records")
        if fname not in files:
            problems.append(f"sealed_file_missing:{name}:{fname}")
            continue
        body = files[fname]
        got_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if got_sha != want_sha:
            problems.append(f"sealed_file_sha256_mismatch:{name}")
        lines = body.splitlines() if body else []
        if len(lines) != want_n:
            problems.append(
                f"sealed_file_line_count_mismatch:{name}:"
                f"{len(lines)}!={want_n}")
        for i, line in enumerate(lines):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"sealed_file_line_not_json:{name}:{i}")
                continue
            if not isinstance(rec, dict):
                problems.append(f"sealed_file_line_not_object:{name}:{i}")
                continue
            for field in _FROZEN_LINE_FIELDS:
                if field not in rec:
                    problems.append(
                        f"sealed_file_line_missing_field:{name}:{i}:{field}")
            leaked = [f for f in _INTERNAL_NAME_LEAK if f in rec]
            if leaked:
                problems.append(
                    f"sealed_file_line_internal_name_leak:{name}:{i}:"
                    f"{leaked}")
            trade_date = rec.get("trade_date")
            if isinstance(trade_date, str):
                seen_dates.add(trade_date)

    if universe is not None:
        for d in sorted(seen_dates - universe):
            problems.append(f"trade_date_outside_universe:{d}")

    return problems
