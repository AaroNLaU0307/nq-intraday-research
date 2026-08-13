"""DR-5 MC production consumer (MAIN-AGENT AUTHORED, DR-5 wiring round).

The seam the DR-5 staged-boundary ruling deferred to "the MC wiring": a
TYPED, RUN-SCOPED, IMMUTABLE prepared input built from the sealed S0
bundle behind a ten-check fail-closed battery, plus the epistemic /
aleatoric drivers that feed the frozen verdict table. Everything method-
shaped is INHERITED verbatim from the frozen sources:

  - MC_METHOD_SPEC.md (mc-freeze-v1): template calendar window (SS4.1),
    three-layer uncertainty + inner randomness sources (SS5), B=1000
    worlds / block 5 / PCG64 / master seeds 7/13/31 (SS5), convergence
    rules a-d (SS5), Primary decision set = 2 lifecycles x P2 (SS2.5),
    EV unit = 24-month prop_operating total / 24 (SS4.4);
  - S0 SS10.4 verdict table via itsf.mc.verdict (order STOP->GO->beta->
    alpha, quantifiers scoped to the Primary set);
  - platform/fee/payout/MLL/sizing state machines via the existing
    itsf.mc.{account,platforms,orchestrator} modules — NOTHING is
    re-derived here (no formula duplication);
  - seeds via contracts.RESEARCH_BOOTSTRAP_SEEDS (IR DR-02 single source).

What this module does NOT do: it never runs a real MC (the public real
entry refuses deterministically — no MC authorization vocabulary exists in
the registry yet), never creates output roots or registry events, never
reads any repository path after the prepared input is built (exposure
freeze: the computation consumes ONLY the immutable prepared object), and
never invents grid samples — the grid-replay harness is a separate PARTIAL
item (source matrix R12) and its absence machine-refuses the
deployable_region layer only, never Checkpoint-0.

`handoff.mc_ready_gate` is deliberately LEFT IN PLACE. This module is the
replacement path the gate's docstring demanded: a reviewed code change
with a typed prepared input, not a permissive check over payload shapes.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[3]

import numpy as np

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS, TradePathRecord
from itsf.mc import bootstrap as mc_bootstrap
from itsf.mc import orchestrator as orch
from itsf.mc.account import PRIMARY_POLICY
from itsf.s0.study import THETA_PRIMARY, THETA_SECONDARY

# frozen: S0 §7 L133 — "θ 主 0.5、副 0.3（完整报告，不得事后升格）".
# Checkpoint-0 accepts ONLY the primary channel; the secondary channel is
# report/sensitivity-only and can NEVER be promoted into the verdict.
PRIMARY_THETA_CHANNEL = f"theta_{THETA_PRIMARY}"        # 'theta_0.5'
SECONDARY_THETA_CHANNEL = f"theta_{THETA_SECONDARY}"    # 'theta_0.3'

# --- frozen axes (MC SS2.5 / SS4.1 / SS5) ----------------------------------
ENGINES = ("E1", "E2")
SCENARIOS = ("Base", "Conservative", "Stress", "Severe")
PLATFORMS = ("lucid", "topstep")
# frozen: MC SS2.5 decision_roles.primary — 2 lifecycles x P2, nothing else
PRIMARY_COMBOS = (("lucid", PRIMARY_POLICY), ("topstep", PRIMARY_POLICY))
# frozen: MC SS0 quantifier scope — the verdict grid is the FULL cross of
# the Primary lifecycles with BOTH engines (S0 SS10.4 row 1 quantifies over
# "E1 与 E2 的所有预注册组合"; row 3's first arm needs the E2 combos present)
PRIMARY_VERDICT_GRID = frozenset(
    f"{platform}|{engine}|{PRIMARY_POLICY}"
    for platform, _p in PRIMARY_COMBOS for engine in ENGINES)
# frozen: S0 SS10.4 — the four mutually exclusive verdict categories
VERDICT_CATEGORIES = frozenset({"STOP", "GO", "beta", "alpha"})
# frozen: MC SS5 rule (a) — B, M and K are EACH doubled separately
DOUBLING_AXES = frozenset({"B", "M", "K"})
# frozen: MC SS4.1 synthetic template calendar window
TEMPLATE_START = "2026-08-01"
TEMPLATE_END = "2028-07-31"
# frozen: MC SS5 epistemic layer
B_WORLDS_FROZEN = 1000
# frozen: SEED_MANIFEST k_policy (S0 gridmix, DR-5 staging)
K_PER_SEED_FROZEN = 200
CRN_SCOPE_FROZEN = "shared_within_theta_engine_scenario"
# frozen: MC SS5 convergence rule (c) — max($25, 5% relative)
CONV_ABS_USD = 25.0
CONV_REL = 0.05
# frozen: MC SS5 convergence rule (d) — MCSE <= 10% of between-world SD
MCSE_MAX_FRACTION = 0.10

# The sealed-bundle exact set (S0-T001 layout; runner-side custody files
# included — the consumer re-derives day universes and governance identity
# from the SAME bytes the S0 seal proved).
BUNDLE_EXACT_SET = frozenset(
    [f"MC_HANDOFF_{e}_{s}.jsonl" for e in ENGINES for s in SCENARIOS]
    + ["S0_REPORT.json", "S0_REPORT.md", "HANDOFF_ADMISSION.json",
       "SEED_MANIFEST.json", "REGISTRY_AFTER_RUN_STARTED.json",
       "manifest.jsonl"])

_RECORD_FIELDS = tuple(TradePathRecord.__dataclass_fields__)  # 19 fields


class MCInputError(ValueError):
    """Fail-closed refusal from the prepared-input battery. `code` is the
    machine-readable refusal reason (source matrix R13)."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


class MCNotAuthorized(RuntimeError):
    """No real-MC authorization exists in the registry vocabulary."""


class MCNotConverged(RuntimeError):
    """MC SS5 convergence rules not satisfied — verdicts are refused."""


# frozen: MC SS5 — M is the EXHAUSTIVELY ENUMERATED start-phase count
# (first template month, ≈21; "非 200"). "Doubling M" has NO unique frozen
# meaning for an exhaustive enumeration, so the M axis of convergence rule
# (a) is DECISION_REQUIRED and CANNOT be assembled in production — the
# convergence evidence path refuses without it, which keeps every real
# Checkpoint-0 verdict structurally unreachable until Aaron rules.
M_AXIS_DOUBLING_STATUS = "DECISION_REQUIRED_M_AXIS"


# Deeply immutable canonical mirror of TradePathRecord (R2 PHASE F): the
# SAME 19 field names (duck-type compatible with the platform state
# machines), frozen dataclass, mtm arrays stored as tuples — attribute
# assignment AND leaf mutation are both impossible. Generated dynamically
# from the contracts dataclass so this module never SPELLS a diagnostic
# field name (the mc layer's static guard forbids consuming them; a
# generated pass-through mirror cannot consume anything).
import dataclasses as _dc

FrozenTradePath = _dc.make_dataclass(
    "FrozenTradePath",
    [(name, object) for name in TradePathRecord.__dataclass_fields__],
    frozen=True, slots=True)
FrozenTradePath.__doc__ = (
    "Deeply immutable mirror of TradePathRecord (generated; R2 PHASE F).")


def _deep_freeze(node):
    """Recursively freeze JSON-shaped data: dict -> MappingProxyType,
    list -> tuple. Scalars pass through."""
    if isinstance(node, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in node.items()})
    if isinstance(node, (list, tuple)):
        return tuple(_deep_freeze(v) for v in node)
    return node


@dataclass(frozen=True, slots=True)
class TemplateCalendar:
    """The frozen 24-month synthetic calendar (MC SS4.1)."""
    days: tuple                       # tuple[orch.TemplateDay, ...]
    first_month_offsets: tuple        # start-phase offsets (MC SS5 source 1)


@dataclass(frozen=True, slots=True)
class PreparedMCInput:
    """Run-scoped immutable MC input (source matrix R13/R14).

    Built ONCE by `prepare_mc_input` from bundle BYTES; the epistemic /
    aleatoric drivers consume ONLY this object — they carry no paths, no
    handles, no registry access (exposure freeze by construction)."""
    trial_id: str
    authorized_commit: str
    file_sha256: Mapping             # name -> hex digest (exact set)
    records: Mapping                 # (engine, scenario) -> {date: record}
    day_sequences: Mapping           # channel -> ordered tuple of dates
    traded_day_sets: Mapping         # channel -> frozenset of dates
    seeds: tuple
    k_per_seed: int
    method_digest: str               # sha256 over frozen method sources
    authorization_snapshot: Mapping  # injected at build; deeply frozen
    calendar: TemplateCalendar


def prepared_digest(prepared: "PreparedMCInput") -> str:
    """Deterministic identity digest of a prepared input — bound into
    every RunEvidence and the seal candidate, and re-checked pre/post
    seal (R2 PHASE F)."""
    ident = {
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "k_per_seed": prepared.k_per_seed,
        "method_digest": prepared.method_digest,
        "channels": {ch: len(seq)
                     for ch, seq in sorted(prepared.day_sequences.items())},
        "n_slots": len(prepared.calendar.days),
    }
    return hashlib.sha256(
        json.dumps(ident, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Template calendar (MC SS4.1 — algorithm frozen, calendar generated from
# the real exchange calendar; bootstrap only fills outcomes onto slots)
# ---------------------------------------------------------------------------

def build_template_calendar(start: str = TEMPLATE_START,
                            end: str = TEMPLATE_END) -> TemplateCalendar:
    import pandas as pd
    import pandas_market_calendars as mcal
    sched = mcal.get_calendar("CME_Equity").schedule(
        start_date=start, end_date=end)
    if len(sched) == 0:
        raise MCInputError("template_calendar_empty",
                           f"no trading days in [{start}, {end}]")
    # frozen-window sanity (review M5): the 24-month template must carry a
    # plausible CME trading-day count — a truncated or mis-windowed build
    # refuses rather than silently shortening the horizon.
    if (start, end) == (TEMPLATE_START, TEMPLATE_END) and \
            not (460 <= len(sched) <= 540):
        raise MCInputError("template_calendar_count_implausible",
                           str(len(sched)))
    start_ts = pd.Timestamp(start)
    days = []
    offsets = []
    for i, ts in enumerate(sched.index):
        day_id = ts.strftime("%Y-%m-%d")
        cal_offset = int((ts - start_ts).days)
        days.append(orch.TemplateDay(day_id=day_id, cal_offset=cal_offset))
        # frozen: MC SS5 inner source (1) — uniform start phase within the
        # FIRST template month (~21 offsets)
        if ts.year == start_ts.year and ts.month == start_ts.month:
            offsets.append(i)
    return TemplateCalendar(days=tuple(days),
                            first_month_offsets=tuple(offsets))


# ---------------------------------------------------------------------------
# The ten-check fail-closed battery (source matrix SS2)
# ---------------------------------------------------------------------------

def _parse_record(row: dict, name: str, i: int) -> FrozenTradePath:
    if not isinstance(row, dict) or set(row) != set(_RECORD_FIELDS):
        raise MCInputError("record_schema_violation",
                           f"{name}:{i} field set != TradePathRecord(19)")
    if not isinstance(row["ambiguous_stop_vs_floor"], bool):
        raise MCInputError("record_ambiguous_flag_not_bool", f"{name}:{i}")
    row = dict(row)
    row["mtm_close_pnl_1m"] = tuple(row["mtm_close_pnl_1m"])
    row["mtm_adverse_pnl_1m"] = tuple(row["mtm_adverse_pnl_1m"])
    return FrozenTradePath(**row)


def prepare_mc_input(bundle: Mapping[str, bytes], *,
                     authorization_snapshot: Mapping,
                     expected_file_sha256: Mapping,
                     calendar: TemplateCalendar | None = None,
                     ) -> PreparedMCInput:
    """Build the immutable prepared input from bundle BYTES, refusing on
    the first violated check. `bundle` maps file name -> raw bytes (the
    caller reads the sealed directory ONCE; tests pass synthetic bytes).

    `expected_file_sha256` is MANDATORY (R2 PHASE C): the EXTERNAL custody
    authority — per-file digests recorded OUTSIDE the bundle under review
    (e.g. the S0 blind post-run attestation table / archive inventory).
    Its key set must equal the full bundle exact-set INCLUDING
    manifest.jsonl; a payload-plus-internal-manifest rewrite therefore
    cannot self-certify."""
    # (10, hoisted as a precondition) authorization snapshot — injected
    # once at build time; everything downstream binds against it, so its
    # absence refuses BEFORE any binding comparison can misattribute.
    if not isinstance(authorization_snapshot, Mapping) or \
            not authorization_snapshot.get("authorized_commit") or \
            not authorization_snapshot.get("trial_id"):
        raise MCInputError("authorization_snapshot_missing")

    # (1) bundle exact-set — missing AND extra both refuse
    names = set(bundle)
    if names != BUNDLE_EXACT_SET:
        missing = sorted(BUNDLE_EXACT_SET - names)
        extra = sorted(names - BUNDLE_EXACT_SET)
        raise MCInputError("bundle_exact_set_violation",
                           f"missing={missing} extra={extra}")

    # (2) per-file sha256 — recomputed here and DUAL-pinned: the sealed
    # manifest must COVER every non-manifest bundle file with a well-formed
    # 64-hex digest (a silent or None entry is a refusal, not a skip), and
    # the independent expectation (when supplied) must agree too.
    sha = {n: hashlib.sha256(bundle[n]).hexdigest() for n in sorted(names)}
    declared: dict[str, object] = {}
    for i, line in enumerate(bundle["manifest.jsonl"].decode("utf-8")
                             .splitlines()):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("record_type") == "file" and "relative_path" in rec:
            declared[rec["relative_path"]] = rec.get("file_sha256")
    hex64 = re.compile(r"^[0-9a-f]{64}$")
    for n in sorted(names - {"manifest.jsonl"}):
        want = declared.get(n)
        if not isinstance(want, str) or not hex64.match(want):
            raise MCInputError("bundle_manifest_coverage",
                               f"{n}: no well-formed manifest digest")
        if sha[n] != want:
            raise MCInputError("bundle_hash_mismatch",
                               f"{n}: manifest={want[:12]} got={sha[n][:12]}")
    # EXTERNAL custody authority (R2 PHASE C): exact key-set equality with
    # the bundle exact-set INCLUDING manifest.jsonl — a missing external
    # digest, an extra one, a malformed one, or any byte mismatch refuses.
    if not isinstance(expected_file_sha256, Mapping):
        raise MCInputError("custody_authority_missing")
    ext_names = set(expected_file_sha256)
    if ext_names != BUNDLE_EXACT_SET:
        raise MCInputError(
            "custody_authority_keyset_violation",
            f"missing={sorted(BUNDLE_EXACT_SET - ext_names)} "
            f"extra={sorted(ext_names - BUNDLE_EXACT_SET)}")
    for n in sorted(ext_names):
        want = expected_file_sha256[n]
        if not isinstance(want, str) or not hex64.match(want):
            raise MCInputError("custody_authority_malformed", n)
        if sha[n] != want:
            raise MCInputError(
                "bundle_hash_mismatch",
                f"{n}: external={want[:12]} got={sha[n][:12]}")

    # (3) trial/commit binding — snapshot vs sealed registry custody file
    reg = json.loads(bundle["REGISTRY_AFTER_RUN_STARTED.json"])
    snap = reg.get("snapshot_before", {})
    for key in ("trial_id", "authorized_commit"):
        want = authorization_snapshot.get(key)
        got = snap.get(key)
        if not want or want != got:
            raise MCInputError("trial_commit_binding_violation",
                               f"{key}: snapshot={want!r} bundle={got!r}")

    report = json.loads(bundle["S0_REPORT.json"])
    gov = report.get("governance", {})
    if gov.get("trial_id") != snap["trial_id"] or \
            gov.get("authorized_commit") != snap["authorized_commit"]:
        raise MCInputError("trial_commit_binding_violation",
                           "S0_REPORT governance disagrees with registry "
                           "custody snapshot")

    # (4) engine/scenario/platform axis — exact
    records: dict = {}
    for e in ENGINES:
        for s in SCENARIOS:
            name = f"MC_HANDOFF_{e}_{s}.jsonl"
            rows: dict = {}
            for i, line in enumerate(bundle[name].decode("utf-8")
                                     .splitlines()):
                if not line.strip():
                    continue
                rec = _parse_record(json.loads(line), name, i)
                if rec.engine != e or rec.cost_scenario != s:
                    raise MCInputError("axis_violation",
                                       f"{name}:{i} carries "
                                       f"{rec.engine}/{rec.cost_scenario}")
                if rec.trade_date in rows:
                    raise MCInputError("duplicate_record_date",
                                       f"{name}:{rec.trade_date}")
                rows[rec.trade_date] = rec       # FrozenTradePath (deep)
            records[(e, s)] = MappingProxyType(rows)
    # (6b, review H3) cross-file record-set consistency: every one of the
    # eight (engine, scenario) files must carry EXACTLY the same trade-date
    # key set — a scenario-selective omission silently becomes a no-trade
    # day downstream and un-anchors the same-combo Conservative/Stress
    # comparison, so it refuses HERE.
    ref_key = ("E1", "Base")
    ref_dates = frozenset(records[ref_key])
    for key, rows in records.items():
        if frozenset(rows) != ref_dates:
            drift = sorted(ref_dates ^ frozenset(rows))[:3]
            raise MCInputError("record_set_drift_across_files",
                               f"{key[0]}|{key[1]} vs E1|Base: {drift}")

    # (5) seed / K vs SEED_MANIFEST and the frozen constants
    seed_manifest = json.loads(bundle["SEED_MANIFEST.json"])
    seeds = tuple(seed_manifest.get("research_bootstrap_seeds", ()))
    if seeds != tuple(RESEARCH_BOOTSTRAP_SEEDS):
        raise MCInputError("seed_axis_violation",
                           f"manifest seeds {seeds} != frozen "
                           f"{tuple(RESEARCH_BOOTSTRAP_SEEDS)}")
    # structured parse (review M3): the k token must EQUAL the frozen K —
    # substring matching admitted k_per_seed=2000.
    k_policy = str(seed_manifest.get("k_policy", ""))
    k_tokens = dict(part.split("=", 1) for part in k_policy.split(";")
                    if "=" in part)
    if k_tokens.get("k_per_seed") != str(K_PER_SEED_FROZEN):
        raise MCInputError("k_policy_violation", k_policy)
    if seed_manifest.get("crn_scope") != CRN_SCOPE_FROZEN:
        raise MCInputError("crn_scope_violation",
                           str(seed_manifest.get("crn_scope")))

    # (6)+(7) date order and TP/FP disjointness per theta channel
    oracle = report.get("oracle_daily", {})
    day_sequences: dict = {}
    traded: dict = {}
    if not isinstance(oracle, dict) or not oracle:
        raise MCInputError("day_universe_missing", "oracle_daily absent")
    for theta, node in oracle.items():
        du = node.get("day_universe", {})
        tp = list(du.get("tp_days", ()))
        fp = list(du.get("fp_days", ()))
        if not tp and not fp:
            raise MCInputError("day_universe_missing", theta)
        # (6, review H3) STRICTLY ascending is a refusal, never a repair —
        # a repaired order would silently hide producer drift.
        for label, lst in (("tp_days", tp), ("fp_days", fp)):
            if any(b <= a for a, b in zip(lst, lst[1:])):
                raise MCInputError("day_sequence_not_ascending",
                                   f"{theta}.{label}")
        overlap = set(tp) & set(fp)
        if overlap:
            raise MCInputError("tp_fp_overlap",
                               f"{theta}: {sorted(overlap)[:3]}")
        seq = tp + fp
        if len(set(seq)) != len(seq):
            raise MCInputError("day_sequence_duplicates", theta)
        ordered = tuple(sorted(seq))          # canonical merged sequence
        # every oracle-selected day must carry a record in EVERY file — a
        # tp day without a record would silently become a no-trade day.
        missing_tp = sorted(set(tp) - ref_dates)
        if missing_tp:
            raise MCInputError("tp_day_without_record",
                               f"{theta}: {missing_tp[:3]}")
        day_sequences[theta] = ordered
        traded[theta] = frozenset(tp)

    # (8) realized-count reconciliation — records vs report manifest counts
    counts = report.get("mc_handoff_manifest", {}).get("counts", {})
    for e in ENGINES:
        for s in SCENARIOS:
            want = counts.get(e, {}).get(s, {}).get("n_records")
            got = len(records[(e, s)])
            if want != got:
                raise MCInputError("realized_count_mismatch",
                                   f"{e}|{s}: manifest={want} parsed={got}")

    # (9) frozen method digest — recomputed from the LIVE frozen files and
    # required to match guards.FROZEN_HASHES (spec + platform params)
    from itsf import guards as g
    method_parts = []
    for fname in ("MC_METHOD_SPEC.md", "gate1/platform_params.yaml"):
        want = g.FROZEN_HASHES[fname]
        # repo-root anchored (review LOW): never CWD-dependent.
        got = hashlib.sha256((_REPO_ROOT / fname).read_bytes()).hexdigest()
        if got != want:
            raise MCInputError("frozen_method_drift", fname)
        method_parts.append(f"{fname}:{got}")
    method_digest = hashlib.sha256(
        "|".join(method_parts).encode("utf-8")).hexdigest()

    # calendar structural validation (review M5) — production window
    # sanity lives in build_template_calendar; EVERY calendar (injected or
    # built) must be structurally sound.
    cal = calendar if calendar is not None else build_template_calendar()
    _validate_calendar(cal)

    # (10) authorization snapshot — presence enforced at the top of the
    # battery; embedded via a JSON round-trip (no aliasing) and then
    # RECURSIVELY frozen (R2 PHASE F).
    frozen_snap = _deep_freeze(
        json.loads(json.dumps(dict(authorization_snapshot))))
    return PreparedMCInput(
        trial_id=str(snap["trial_id"]),
        authorized_commit=str(snap["authorized_commit"]),
        file_sha256=MappingProxyType(dict(sha)),
        records=MappingProxyType(records),
        day_sequences=MappingProxyType(day_sequences),
        traded_day_sets=MappingProxyType(traded),
        seeds=seeds,
        k_per_seed=K_PER_SEED_FROZEN,
        method_digest=method_digest,
        authorization_snapshot=frozen_snap,
        calendar=cal)


def _validate_calendar(cal: TemplateCalendar) -> None:
    days = cal.days
    if not days:
        raise MCInputError("calendar_invalid", "empty")
    ids = [d.day_id for d in days]
    if len(set(ids)) != len(ids):
        raise MCInputError("calendar_invalid", "duplicate day_ids")
    offs = [d.cal_offset for d in days]
    if any(b <= a for a, b in zip(offs, offs[1:])):
        raise MCInputError("calendar_invalid",
                           "cal_offsets not strictly ascending")
    fmo = cal.first_month_offsets
    if not fmo or any(not (0 <= i < len(days)) for i in fmo):
        raise MCInputError("calendar_invalid",
                           "first_month_offsets empty or out of range")


# ---------------------------------------------------------------------------
# Epistemic / aleatoric drivers (MC SS5 — strictly separated layers)
# ---------------------------------------------------------------------------

def _paths_for_world(prepared: PreparedMCInput, world: Sequence[str],
                     channel: str, engine: str, scenario: str) -> dict:
    """Map template slots to the drawn historical day's path record.

    A slot trades iff the drawn day is in the channel's ORACLE-SELECTED
    set AND a sealed record exists for it (frozen: MC SS4.1 — bootstrap
    fills outcomes onto template slots, never invents trades)."""
    recs = prepared.records[(engine, scenario)]
    sel = prepared.traded_day_sets[channel]
    days = prepared.calendar.days
    out = {}
    for slot, hist_day in zip(days, world):
        if hist_day in sel and hist_day in recs:
            out[slot.day_id] = recs[hist_day]
    return out


def _lifecycle_stats(prepared: PreparedMCInput, platform: str,
                     paths_by_day: dict, start_offset: int) -> dict:
    cfg = orch.LifecycleConfig(platform=platform,
                               sizing_policy=PRIMARY_POLICY)
    res = orch.run_lifecycle(cfg, list(prepared.calendar.days),
                             paths_by_day, start_offset=start_offset)
    rep = res.ledger_report
    return {
        "monthly_ev": float(rep["prop_operating_ev_monthly"]),
        "payout_realized": float(rep["payout_cash_total"]) > 0.0,
        "skips_n0": int(res.skips_n0),
        "exhausted": bool(res.terminated_by_exhaustion),
        "n_offered": len(paths_by_day),
    }


@dataclass(frozen=True)
class FeasibilityEvidence:
    """MECHANICALLY computed from lifecycle outputs (R2 PHASE E.5) — never
    a caller-declared boolean. `feasible` is the plain mechanical reading
    of the three items S0 SS10.4 row 2 names ("整数仓位、频率、payout
    路径可行性经 MC 确认"): integer sizing left SOME trades standing,
    trading opportunities existed at all, and at least one simulated path
    actually realized a payout. These are NECESSARY-condition readings of
    the frozen text, not invented thresholds; Codex may tighten them."""
    n_paths: int
    payout_realized_share: float
    total_skips_n0: int
    total_offered: int
    exhausted_share: float

    @property
    def feasible(self) -> bool:
        if self.n_paths == 0 or self.total_offered == 0:
            return False
        integer_sizing_ok = self.total_skips_n0 < self.total_offered
        payout_path_ok = self.payout_realized_share > 0.0
        return integer_sizing_ok and payout_path_ok

    @staticmethod
    def from_stats(stats: Sequence[Mapping]) -> "FeasibilityEvidence":
        n = len(stats)
        return FeasibilityEvidence(
            n_paths=n,
            payout_realized_share=(sum(1 for s in stats
                                       if s["payout_realized"]) / n
                                   if n else 0.0),
            total_skips_n0=sum(int(s["skips_n0"]) for s in stats),
            total_offered=sum(int(s["n_offered"]) for s in stats),
            exhausted_share=(sum(1 for s in stats if s["exhausted"]) / n
                             if n else 0.0))


@dataclass(frozen=True)
class EpistemicResult:
    """B world-level mean monthly prop_operating_EVs + decision quantiles.
    THE ONLY object Checkpoint-0 statistics may be read from. Carries its
    own provenance (prepared digest, B, master seed) and the mechanically
    computed feasibility evidence (R2 PHASE E)."""
    platform: str
    engine: str
    scenario: str
    channel: str
    world_means: tuple
    p5: float
    median: float
    p95: float
    mcse_ok: bool
    max_within_world_se: float
    between_world_sd: float
    B: int
    master_seed: int
    prepared_digest: str
    feasibility: FeasibilityEvidence

    @staticmethod
    def from_world_means(platform, engine, scenario, channel, world_means,
                         *, within_world_ses, B, master_seed,
                         prepared_digest_value,
                         feasibility) -> "EpistemicResult":
        arr = np.asarray(world_means, dtype=float)
        between_sd = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
        max_se = float(max(within_world_ses)) if within_world_ses else 0.0
        # frozen: MC SS5 rule (d) — within-world MCSE <= 10% of the
        # between-world SD, computed from ACTUAL samples (never declared).
        mcse_ok = (between_sd == 0.0
                   or max_se <= MCSE_MAX_FRACTION * between_sd)
        return EpistemicResult(
            platform=platform, engine=engine, scenario=scenario,
            channel=channel, world_means=tuple(float(x) for x in arr),
            p5=float(np.percentile(arr, 5)),
            median=float(np.percentile(arr, 50)),
            p95=float(np.percentile(arr, 95)),
            mcse_ok=mcse_ok, max_within_world_se=max_se,
            between_world_sd=between_sd, B=int(B),
            master_seed=int(master_seed),
            prepared_digest=prepared_digest_value,
            feasibility=feasibility)


def run_epistemic(prepared: PreparedMCInput, *, platform: str, engine: str,
                  scenario: str, channel: str, B: int,
                  master_seed: int) -> EpistemicResult:
    """B bootstrap worlds -> per-world MEAN monthly prop_operating_EV over
    the start-phase offsets (MC SS5 inner source (1)) -> quantiles.

    CRN: worlds derive ONLY from (day_ids, B, master_seed) via the frozen
    builder, so every (platform, engine, scenario) evaluated with the same
    arguments sees IDENTICAL worlds by construction."""
    if platform not in PLATFORMS:
        raise MCInputError("axis_violation", platform)
    if (engine, scenario) not in prepared.records:
        raise MCInputError("axis_violation", f"{engine}|{scenario}")
    day_ids = prepared.day_sequences[channel]
    n_slots = len(prepared.calendar.days)
    # review H1: worlds must fill EVERY template slot (MC SS4.1 — the
    # bootstrap decides the outcome sequence placed on the template's
    # trading days, all of them; the pool size is the historical eligible
    # universe, which is smaller than the 24-month template).
    worlds = mc_bootstrap.build_worlds(day_ids, B, master_seed,
                                       length=n_slots)
    offsets = prepared.calendar.first_month_offsets
    world_means = []
    ses = []
    all_stats = []
    for world in worlds:
        if len(world) != n_slots:
            raise MCInputError("world_length_mismatch",
                               f"{len(world)} != {n_slots}")
        paths = _paths_for_world(prepared, world, channel, engine, scenario)
        stats = [_lifecycle_stats(prepared, platform, paths, off)
                 for off in offsets]
        all_stats.extend(stats)
        evs = [s["monthly_ev"] for s in stats]
        world_means.append(float(np.mean(evs)))
        n = len(evs)
        ses.append(float(np.std(evs, ddof=1) / math.sqrt(n))
                   if n > 1 else 0.0)
    return EpistemicResult.from_world_means(
        platform, engine, scenario, channel, world_means,
        within_world_ses=ses, B=B, master_seed=master_seed,
        prepared_digest_value=prepared_digest(prepared),
        feasibility=FeasibilityEvidence.from_stats(all_stats))


@dataclass(frozen=True)
class AleatoricResult:
    """CONDITIONAL aleatoric distribution (MC SS5): the M single-attempt
    paths WITHIN ONE FIXED bootstrap world — reporting only, never a GO
    gate input. Binds the fixed world by digest (R2 PHASE G)."""
    platform: str
    engine: str
    scenario: str
    channel: str
    world_digest: str
    attempt_monthly_evs: tuple


def run_conditional_aleatoric(prepared: PreparedMCInput, *,
                              world: Sequence[str], platform: str,
                              engine: str, scenario: str,
                              channel: str) -> AleatoricResult:
    """M attempt paths inside ONE FIXED world (frozen: MC SS5 conditional
    aleatoric — "固定世界内 M 条账户路径的结果分布"). The world must be a
    full-slot-length sequence drawn from the channel's pool (i.e. one
    element of a bootstrap worlds list); historical-sequence tiling is NOT
    a fixed-world simulation and is refused."""
    n_slots = len(prepared.calendar.days)
    if len(world) != n_slots:
        raise MCInputError("world_length_mismatch",
                           f"{len(world)} != {n_slots}")
    pool = set(prepared.day_sequences[channel])
    if not set(world) <= pool:
        raise MCInputError("world_membership_violation",
                           "world draws days outside the channel pool")
    paths = _paths_for_world(prepared, tuple(world), channel, engine,
                             scenario)
    evs = [_lifecycle_stats(prepared, platform, paths, off)["monthly_ev"]
           for off in prepared.calendar.first_month_offsets]
    wd = hashlib.sha256("|".join(world).encode("utf-8")).hexdigest()
    return AleatoricResult(platform=platform, engine=engine,
                           scenario=scenario, channel=channel,
                           world_digest=wd,
                           attempt_monthly_evs=tuple(evs))


def epistemic_go_gate_input(cons: EpistemicResult,
                            stress: EpistemicResult):
    """Build the frozen VerdictInput for ONE combo from the SAME combo's
    Conservative and Stress epistemic results (S0 SS10.4 anti-cherry-pick:
    no cross-combo stitching). Feasibility comes EXCLUSIVELY from the
    combo's own mechanically computed evidence (R2 PHASE E — never a
    caller-declared boolean), and ONLY the frozen primary theta channel
    may enter Checkpoint-0 (S0 §7 L133 — 不得事后升格)."""
    from itsf.mc.verdict import VerdictInput
    if type(cons) is not EpistemicResult or type(stress) is not EpistemicResult:
        raise MCInputError("aleatoric_leak_into_go_gate")
    same = (cons.platform == stress.platform
            and cons.engine == stress.engine
            and cons.channel == stress.channel)
    if not same:
        raise MCInputError(
            "cross_combo_stitching",
            f"Conservative from {cons.platform}/{cons.engine}/"
            f"{cons.channel} vs Stress from {stress.platform}/"
            f"{stress.engine}/{stress.channel}")
    if cons.scenario != "Conservative" or stress.scenario != "Stress":
        raise MCInputError("scenario_role_violation",
                           f"{cons.scenario}/{stress.scenario}")
    if cons.channel != PRIMARY_THETA_CHANNEL:
        raise MCInputError(
            "theta_channel_not_primary",
            f"{cons.channel!r} is report/sensitivity-only — Checkpoint-0 "
            f"accepts exactly {PRIMARY_THETA_CHANNEL!r} (S0 §7 L133, "
            "不得事后升格)")
    if cons.prepared_digest != stress.prepared_digest:
        raise MCInputError("provenance_mismatch",
                           "Conservative/Stress computed from different "
                           "prepared inputs")
    feasible = (cons.feasibility.feasible and stress.feasibility.feasible)
    return VerdictInput(p5_cons=cons.p5, median_cons=cons.median,
                        median_stress=stress.median, p95_cons=cons.p95,
                        feasible=feasible, platform=cons.platform,
                        engine=cons.engine, channel=cons.channel)


# ---------------------------------------------------------------------------
# Convergence (MC SS5 rules a-d; rule encoded, the doubling RUNS happen at
# real-MC time — an unconverged input refuses to produce a verdict)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConvergenceReport:
    category_stable_under_doubling: bool     # rule (a) — B, M AND K each
    category_same_across_seeds: bool         # rule (b) — seeds 7/13/31
    quantile_drift_ok: bool                  # rule (c)
    mcse_ok: bool                            # rule (d)
    drift_by_axis: Mapping                   # axis -> {quantile: |delta|}

    @property
    def converged(self) -> bool:
        return (self.category_stable_under_doubling
                and self.category_same_across_seeds
                and self.quantile_drift_ok and self.mcse_ok)


@dataclass(frozen=True)
class RunEvidence:
    """One COMPLETE epistemic evaluation of the frozen Primary verdict
    grid, with provenance (R2 PHASE E): every convergence quantity is
    computed FROM these objects, never declared by a caller."""
    run_label: str                # 'base' | 'double_B' | 'double_M' |
    #                               'double_K' | 'seed_<n>'
    axis: str                     # 'base' | 'B' | 'M' | 'K' | 'seed'
    B: int
    M: int                        # start-phase count actually used
    K: int                        # grid repeats per seed (frozen 200)
    master_seed: int
    prepared_digest: str
    results: Mapping              # combo_id -> (cons: EpistemicResult,
    #                                            stress: EpistemicResult)

    def verdict(self):
        """The verdict THIS run's actual results produce (frozen table
        over the full Primary grid; feasibility from evidence)."""
        from itsf.mc.verdict import apply_verdict
        grid = {cid: epistemic_go_gate_input(cons, stress)
                for cid, (cons, stress) in self.results.items()}
        if set(grid) != PRIMARY_VERDICT_GRID:
            raise MCInputError(
                "primary_grid_coverage_violation",
                f"run {self.run_label}: got {sorted(grid)}")
        return apply_verdict(grid)

    def quantile_map(self) -> dict:
        out = {}
        for cid, (cons, stress) in sorted(self.results.items()):
            out[f"{cid}.p5_cons"] = cons.p5
            out[f"{cid}.median_cons"] = cons.median
            out[f"{cid}.p95_cons"] = cons.p95
            out[f"{cid}.median_stress"] = stress.median
        return out


def _check_run_provenance(base: RunEvidence, other: RunEvidence,
                          axis: str) -> None:
    if other.prepared_digest != base.prepared_digest:
        raise MCInputError("provenance_mismatch",
                           f"{other.run_label} vs base prepared digest")
    if other.axis != axis:
        raise MCInputError("axis_identity_mismatch",
                           f"{other.run_label}: axis={other.axis!r} "
                           f"expected {axis!r}")
    scale = {"B": ("B", 2), "M": ("M", 2), "K": ("K", 2)}[axis]
    field, factor = scale
    got, want = getattr(other, field), factor * getattr(base, field)
    if got != want:
        raise MCInputError("doubling_scale_violation",
                           f"{other.run_label}: {field}={got} != {want}")
    for f in ("B", "M", "K"):
        if f != field and getattr(other, f) != getattr(base, f):
            raise MCInputError("doubling_scale_violation",
                               f"{other.run_label}: {f} moved on a "
                               f"{field}-doubling run")


def convergence_from_evidence(base: RunEvidence,
                              doubled_by_axis: Mapping,
                              seed_runs: Mapping) -> ConvergenceReport:
    """Compute MC SS5 rules (a)-(d) FROM run evidence (R2 PHASE E):

    (a) doubled runs for EXACTLY the axes B, M and K, each provenance- and
        scale-checked, each reproducing the base verdict category (the
        category is COMPUTED from each run's own results);
    (b) seed runs for EXACTLY the frozen seeds 7/13/31, categories
        computed and compared;
    (c) per-axis quantile drift maps with EXACT key-set equality against
        the base map (one shared mapping cannot represent three axes);
    (d) MCSE from the base run's ACTUAL samples (EpistemicResult carries
        max_within_world_se / between_world_sd computed in run_epistemic).

    NOTE — M axis: MC SS5 fixes M as the exhaustively enumerated start
    phases; doubling it has no unique frozen meaning
    (M_AXIS_DOUBLING_STATUS = DECISION_REQUIRED_M_AXIS). Production
    cannot assemble a legal `doubled_by_axis['M']`, so this function is
    structurally unsatisfiable until Aaron rules — that is the honest
    fail-closed state, not a gap."""
    if base.axis != "base":
        raise MCInputError("axis_identity_mismatch",
                           f"base run carries axis={base.axis!r}")
    if set(doubled_by_axis) != DOUBLING_AXES:
        raise MCInputError("doubling_axes_violation",
                           f"need exactly {sorted(DOUBLING_AXES)}, got "
                           f"{sorted(doubled_by_axis)}")
    base_verdict = base.verdict().verdict
    base_q = base.quantile_map()
    if not base_q:
        raise MCInputError("quantile_comparison_empty")
    drift_by_axis = {}
    doubled_ok = True
    drift_ok = True
    for axis in sorted(DOUBLING_AXES):
        run = doubled_by_axis[axis]
        _check_run_provenance(base, run, axis)
        if run.verdict().verdict != base_verdict:
            doubled_ok = False
        run_q = run.quantile_map()
        if set(run_q) != set(base_q):
            raise MCInputError("quantile_keyset_violation",
                               f"axis {axis}")
        drift = {k: abs(float(run_q[k]) - float(base_q[k]))
                 for k in sorted(base_q)}
        drift_by_axis[axis] = MappingProxyType(drift)
        for k, d in drift.items():
            tol = max(CONV_ABS_USD, CONV_REL * abs(float(base_q[k])))
            if d > tol:
                drift_ok = False
    if set(seed_runs) != set(RESEARCH_BOOTSTRAP_SEEDS):
        raise MCInputError("seed_set_violation",
                           f"need exactly {tuple(RESEARCH_BOOTSTRAP_SEEDS)},"
                           f" got {sorted(seed_runs)}")
    seed_cats = set()
    for seed, run in seed_runs.items():
        if run.prepared_digest != base.prepared_digest:
            raise MCInputError("provenance_mismatch", f"seed_{seed}")
        if run.master_seed != seed:
            raise MCInputError("axis_identity_mismatch",
                               f"seed run {seed} carries master_seed="
                               f"{run.master_seed}")
        seed_cats.add(run.verdict().verdict)
    mcse_ok = all(cons.mcse_ok and stress.mcse_ok
                  for cons, stress in base.results.values())
    return ConvergenceReport(
        category_stable_under_doubling=doubled_ok,
        category_same_across_seeds=(len(seed_cats) == 1),
        quantile_drift_ok=drift_ok,
        mcse_ok=mcse_ok,
        drift_by_axis=MappingProxyType(drift_by_axis))


def verdict_or_refuse(primary_inputs: Mapping,
                      convergence: ConvergenceReport):
    """The ONLY path to a Checkpoint-0 verdict.

    Refuses (review H2) unless the input grid covers EXACTLY the frozen
    Primary verdict grid — both lifecycles x P2 x BOTH engines (MC SS0
    quantifier scope; S0 SS10.4 row 1 quantifies over "E1 与 E2 的所有预
    注册组合" and row 3's first arm needs the E2 combos present) — with
    every combo id matching its VerdictInput's own labels; and refuses
    without convergence (MC SS5 rule (e))."""
    from itsf.mc.verdict import apply_verdict
    if set(primary_inputs) != PRIMARY_VERDICT_GRID:
        raise MCInputError(
            "primary_grid_coverage_violation",
            f"need exactly {sorted(PRIMARY_VERDICT_GRID)}, got "
            f"{sorted(primary_inputs)}")
    for cid, v in primary_inputs.items():
        platform, engine, _policy = cid.split("|")
        if v.platform != platform or v.engine != engine:
            raise MCInputError("primary_grid_label_mismatch",
                               f"{cid} carries {v.platform}/{v.engine}")
        # R2 PHASE B: Checkpoint-0 accepts ONLY the frozen primary theta
        # channel (S0 §7 L133); a secondary-channel input refuses here
        # even if every other gate is green.
        if v.channel != PRIMARY_THETA_CHANNEL:
            raise MCInputError("theta_channel_not_primary",
                               f"{cid} carries channel={v.channel!r}")
    if not convergence.converged:
        raise MCNotConverged(
            "MC SS5 convergence rules not satisfied "
            f"(a={convergence.category_stable_under_doubling} "
            f"b={convergence.category_same_across_seeds} "
            f"c={convergence.quantile_drift_ok} d={convergence.mcse_ok}) "
            "— doubling rerun required, verdict refused")
    return apply_verdict(dict(primary_inputs))


def render_verdict_inputs(prepared: PreparedMCInput,
                          primary_inputs: Mapping,
                          convergence: ConvergenceReport) -> dict:
    """MC SS6 `verdict_inputs.json` seal CANDIDATE: the Primary combos'
    epistemic P5/median/P95 + feasibility flags + the mechanical verdict,
    bound to the prepared input's identity. Refuses without convergence
    (through verdict_or_refuse) — an unconverged candidate cannot render."""
    digest_before = prepared_digest(prepared)
    verdict = verdict_or_refuse(primary_inputs, convergence)
    digest_after = prepared_digest(prepared)
    if digest_before != digest_after:
        raise MCInputError("prepared_digest_instability",
                           f"{digest_before[:12]} -> {digest_after[:12]}")
    return {
        "schema": "mc_verdict_inputs.v2",
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "method_digest": prepared.method_digest,
        "prepared_digest": digest_before,
        "primary_theta_channel": PRIMARY_THETA_CHANNEL,
        # provenance (review LOW): the sealed numbers are bound to the
        # exact bundle bytes they were computed from.
        "bundle_file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "primary": {
            cid: {"p5_cons": v.p5_cons, "median_cons": v.median_cons,
                  "median_stress": v.median_stress, "p95_cons": v.p95_cons,
                  "feasible": v.feasible, "platform": v.platform,
                  "engine": v.engine, "channel": v.channel}
            for cid, v in sorted(primary_inputs.items())},
        "convergence": {
            "a_category_stable_under_doubling":
                convergence.category_stable_under_doubling,
            "b_category_same_across_seeds":
                convergence.category_same_across_seeds,
            "c_quantile_drift_ok": convergence.quantile_drift_ok,
            "d_mcse_ok": convergence.mcse_ok},
        "verdict": {"category": verdict.verdict, "reason": verdict.reason},
    }


# ---------------------------------------------------------------------------
# Real-MC authorization (default refuse; no vocabulary exists yet)
# ---------------------------------------------------------------------------

MC_AUTHORIZATION_EVENT = "MC_RUN_AUTHORIZED"     # future registry vocabulary


def authorize_real_mc(registry_text: str) -> "NoReturn":
    """Deterministic refusal today: the registry vocabulary contains no
    MC_RUN_AUTHORIZED event type, and this gate does NOT best-effort parse
    one into existence. A future real-MC round must extend the registry
    grammar + this gate DELIBERATELY (reviewed change), mirroring the S0
    SS10 discipline. Grid replay (source matrix R12) must also land before
    the deployable_region layer may run."""
    from itsf.s0.handoff import McConsumerAbsent
    marker = f"**{MC_AUTHORIZATION_EVENT}**"
    raise McConsumerAbsent(
        "real MC remains NOT authorized: registry grammar has no "
        f"{MC_AUTHORIZATION_EVENT} vocabulary"
        + (" (a lookalike token appears in the registry text but no "
           "parser/grammar accepts it — refusal stands)"
           if marker in registry_text else "")
        + "; Aaron + Codex must gate the first real MC explicitly")


def run_real_mc(*_args, **_kwargs) -> "NoReturn":
    """Public real-MC entry: guards first, then the authorization gate —
    which refuses deterministically today. Unreachable beyond the gate."""
    from itsf.guards import G9_FLAG, SECOND_COPY_FLAG, assert_real_run_allowed
    assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)
    from pathlib import Path
    registry = Path("ops/TRIAL_REGISTRY.md")
    text = registry.read_text(encoding="utf-8") if registry.exists() else ""
    authorize_real_mc(text)
    raise AssertionError("unreachable: authorize_real_mc always raises")
