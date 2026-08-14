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
# MC SS5 rule (a) as amended by IR-29 (Aaron, R2.3 named prompt): B and K
# keep their doubling obligation; M — the exhaustively enumerated start-
# phase set — is EXEMPT from doubling and instead owes an
# EXHAUSTIVE_SUPPORT_CERTIFICATE (complete/unique/each-phase-exactly-once
# over the prepared calendar's legal first-month offsets).
DOUBLING_AXES = frozenset({"B", "K"})
M_AXIS_RULING = ("FINITE_SUPPORT_EXHAUSTIVE_ENUMERATION_EXEMPT_FROM_"
                 "DOUBLING (IR-29, R2.3)")
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


# HISTORICAL (R2.1/R2.2): "doubling M" had no frozen meaning and the axis
# was DECISION_REQUIRED. RESOLVED by IR-29 (R2.3): M is exempt from
# doubling and owes an ExhaustiveSupportCertificate instead — see
# M_AXIS_RULING and convergence_from_evidence.
M_AXIS_DOUBLING_STATUS = "RESOLVED_BY_IR29_EXHAUSTIVE_SUPPORT_CERTIFICATE"


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


def _unfreeze(node):
    """Inverse of _deep_freeze for canonical JSON serialisation."""
    if isinstance(node, Mapping):
        return {k: _unfreeze(v) for k, v in node.items()}
    if isinstance(node, tuple):
        return [_unfreeze(v) for v in node]
    return node


def prepared_digest(prepared: "PreparedMCInput") -> str:
    """Deterministic identity digest of a prepared input — bound into
    every RunEvidence and the seal candidate, and re-checked pre/post
    seal.

    R2.1 PHASE E: binds FULL CONTENT, not lengths — every calendar
    day_id + cal_offset + the complete first_month_offsets, the complete
    day sequences and traded sets per channel, and the canonicalised
    authorization snapshot. Two calendars of equal length but different
    dates/offsets produce different digests."""
    ident = {
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "k_per_seed": prepared.k_per_seed,
        "method_digest": prepared.method_digest,
        "day_sequences": {ch: list(seq)
                          for ch, seq in
                          sorted(prepared.day_sequences.items())},
        "traded_day_sets": {ch: sorted(days)
                            for ch, days in
                            sorted(prepared.traded_day_sets.items())},
        "calendar_days": [[d.day_id, d.cal_offset]
                          for d in prepared.calendar.days],
        "first_month_offsets": list(prepared.calendar.first_month_offsets),
        "authorization_snapshot": _unfreeze(
            prepared.authorization_snapshot),
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

@dataclass(frozen=True, slots=True)
class CustodyAuthority:
    """Typed EXTERNAL custody authority (R2.1 PHASE F): the per-file
    digest table plus its own provenance — which artifact it came from
    and that artifact's digest. Production authorities come from
    `load_custody_authority_from_attestation`; test conveniences are
    explicitly `test_only` and the PRODUCTION prepare entry refuses
    them."""
    trial_id: str
    authorized_commit: str
    source_artifact_id: str
    source_artifact_sha256: str
    file_sha256: Mapping
    test_only: bool

    @staticmethod
    def for_tests(bundle: Mapping, *, trial_id: str | None = None,
                  authorized_commit: str | None = None
                  ) -> "CustodyAuthority":
        """TEST_ONLY convenience — digests computed from the given bytes;
        trial/commit default to the bundle's OWN registry snapshot (the
        binding check is unconditional, so a coherent test authority must
        agree with the bundle it certifies). Never accepted by the
        production prepare entry."""
        if trial_id is None or authorized_commit is None:
            try:
                snap = json.loads(
                    bundle["REGISTRY_AFTER_RUN_STARTED.json"]
                ).get("snapshot_before", {})
            except Exception:                    # noqa: BLE001
                snap = {}
            trial_id = trial_id or str(snap.get("trial_id", "S0-T001"))
            authorized_commit = (authorized_commit
                                 or str(snap.get("authorized_commit",
                                                 "0" * 40)))
        return CustodyAuthority(
            trial_id=trial_id, authorized_commit=authorized_commit,
            source_artifact_id="TEST_ONLY_SYNTHETIC",
            source_artifact_sha256="0" * 64,
            file_sha256=MappingProxyType(
                {n: hashlib.sha256(b).hexdigest()
                 for n, b in bundle.items()}),
            test_only=True)


# The production custody source: the S0-T001 blind post-run attestation
# (written and committed BEFORE any reveal; its hash table is the
# independent record of the sealed bundle's bytes).
ATTESTATION_PATH = "ops/S0_T001_POST_RUN_ATTESTATION.md"
# R2.2 PHASE E — the attestation document's OWN digest, pinned in CODE
# (commit-bound): a synchronized rewrite of attestation + bundle +
# manifest still fails against this constant. Any legitimate future
# change to the attestation requires a reviewed code change here.
ATTESTATION_SHA256_PINNED = (
    "d839b965a35e749f0a9052cc3fb85f9b4032ed5d412043f36ac3349779941805")


def load_custody_authority_from_attestation(
        path: str = ATTESTATION_PATH,
        attestation_bytes: bytes | None = None) -> CustodyAuthority:
    """Parse the blind post-run attestation into a typed production
    authority (test_only=False). Fail-closed (R2.2 PHASE E): the RAW
    BYTES must hash to the CODE-PINNED attestation digest, the source id
    must be the approved path, the table must yield EXACTLY the bundle
    exact-set with well-formed digests, and the trial/commit lines must
    be present. This is the ONLY constructor of a non-test authority the
    production prepare entry will honour."""
    if path != ATTESTATION_PATH:
        raise MCInputError("custody_authority_source_violation",
                           f"source id {path!r} != approved "
                           f"{ATTESTATION_PATH!r}")
    raw = (attestation_bytes if attestation_bytes is not None
           else (_REPO_ROOT / path).read_bytes())
    got_sha = hashlib.sha256(raw).hexdigest()
    if got_sha != ATTESTATION_SHA256_PINNED:
        raise MCInputError(
            "custody_authority_source_digest_mismatch",
            f"attestation bytes hash {got_sha[:12]} != pinned "
            f"{ATTESTATION_SHA256_PINNED[:12]}")
    text = raw.decode("utf-8")
    trial = re.search(r"TRIAL_ID=(\S+)", text)
    commit = re.search(r"AUTHORIZED_COMMIT=([0-9a-f]{40})", text)
    if not trial or not commit:
        raise MCInputError("custody_authority_malformed",
                           "attestation lacks trial/commit lines")
    digests: dict[str, str] = {}
    for m in re.finditer(r"^\|\s*(\S+)\s*\|\s*\d+\s*\|\s*([0-9a-f]{64})"
                         r"\s*\|\s*$", text, re.MULTILINE):
        digests[m.group(1)] = m.group(2)
    if set(digests) != BUNDLE_EXACT_SET:
        raise MCInputError(
            "custody_authority_keyset_violation",
            f"attestation table names {sorted(set(digests))[:4]}... "
            f"({len(digests)} files) != bundle exact-set")
    return CustodyAuthority(
        trial_id=trial.group(1),
        authorized_commit=commit.group(1),
        source_artifact_id=path,
        source_artifact_sha256=hashlib.sha256(raw).hexdigest(),
        file_sha256=MappingProxyType(digests),
        test_only=False)


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
                     attestation_bytes: bytes,
                     ) -> PreparedMCInput:
    """PRODUCTION prepare entry (R2.2 PHASE E — non-self-authenticating):
    accepts the RAW attestation bytes, never a caller-built authority
    object. The authority is constructed INTERNALLY by
    `load_custody_authority_from_attestation`, which pins the source id
    AND the source document digest in code — a hand-built
    CustodyAuthority(test_only=False) has NO production entry, and a
    synchronized attestation+bundle+manifest rewrite still fails against
    the code pin. The frozen-window calendar is built here (no injection
    seam). Tests use `prepare_mc_input_for_tests`."""
    authority = load_custody_authority_from_attestation(
        attestation_bytes=attestation_bytes)
    return _prepare_mc_input_impl(bundle,
                                  authorization_snapshot=
                                  authorization_snapshot,
                                  custody_authority=authority,
                                  calendar=None)


def prepare_mc_input_for_tests(bundle: Mapping[str, bytes], *,
                               authorization_snapshot: Mapping,
                               custody_authority: CustodyAuthority,
                               test_only_calendar:
                               "TemplateCalendar | None" = None,
                               ) -> PreparedMCInput:
    """TEST_ONLY seam (R2.1 PHASE E.5/F; hardened R2.2): accepts ONLY
    test_only authorities — a caller-built test_only=False authority has
    no entry here either (production non-test authorities exist solely
    via the internal attestation constructor)."""
    if not isinstance(custody_authority, CustodyAuthority):
        raise MCInputError("custody_authority_missing")
    if not custody_authority.test_only:
        raise MCInputError(
            "custody_authority_production_object_in_test_entry",
            "non-test authorities are constructed ONLY inside "
            "prepare_mc_input from pinned attestation bytes")
    return _prepare_mc_input_impl(bundle,
                                  authorization_snapshot=
                                  authorization_snapshot,
                                  custody_authority=custody_authority,
                                  calendar=test_only_calendar)


def _prepare_mc_input_impl(bundle: Mapping[str, bytes], *,
                           authorization_snapshot: Mapping,
                           custody_authority: CustodyAuthority,
                           calendar: "TemplateCalendar | None",
                           ) -> PreparedMCInput:
    """Shared battery. `authority` is the EXTERNAL custody record — per-
    file digests recorded OUTSIDE the bundle under review (production:
    the blind post-run attestation). Key set must equal the full bundle
    exact-set INCLUDING manifest.jsonl; a payload-plus-internal-manifest
    rewrite therefore cannot self-certify."""
    expected_file_sha256 = custody_authority.file_sha256
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
    # R2.1 PHASE F: the custody authority's OWN trial/commit must agree
    # with the bundle's registry custody snapshot — an authority lifted
    # from some other trial's attestation cannot certify this bundle.
    # UNCONDITIONAL: test authorities get no exemption.
    if (custody_authority.trial_id != snap.get("trial_id")
            or custody_authority.authorized_commit
            != snap.get("authorized_commit")):
        raise MCInputError("custody_authority_binding_violation",
                           f"authority {custody_authority.trial_id}/"
                           f"{custody_authority.authorized_commit[:12]} vs "
                           f"bundle snapshot")

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

    # calendar (R2.1 PHASE E): the injected TEST_ONLY calendar is COPIED
    # and tuple-ized — no caller list survives into the prepared object;
    # the production path builds the frozen window.
    if calendar is not None:
        cal = TemplateCalendar(
            days=tuple(calendar.days),
            first_month_offsets=tuple(int(i) for i in
                                      calendar.first_month_offsets))
    else:
        cal = build_template_calendar()
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


# frozen: platform_params lucidflex_50k payouts.qualifying_day_min_profit
# _usd = 150 (每次批准 payout 后重置重计) — the ledger's daily balance
# delta is the mechanical read of a day's net profit (fee events also move
# the balance; disclosed derivation, no invention).
QUALIFYING_DAY_MIN_PROFIT_USD = 150.0


def _lifecycle_stats(prepared: PreparedMCInput, platform: str,
                     paths_by_day: dict, start_offset: int) -> dict:
    cfg = orch.LifecycleConfig(platform=platform,
                               sizing_policy=PRIMARY_POLICY)
    res = orch.run_lifecycle(cfg, list(prepared.calendar.days),
                             paths_by_day, start_offset=start_offset)
    rep = res.ledger_report
    payout_count = 0
    winning_days = 0
    days_ge_150 = 0
    prev_balance = None
    for ev in res.events:
        if ev.payout_gross > 0.0:
            payout_count += 1
        if prev_balance is not None:
            delta = ev.balance - prev_balance
            if delta > 0.0:
                winning_days += 1
            if delta >= QUALIFYING_DAY_MIN_PROFIT_USD:
                days_ge_150 += 1
        prev_balance = ev.balance
    return {
        "monthly_ev": float(rep["prop_operating_ev_monthly"]),
        "payout_realized": float(rep["payout_cash_total"]) > 0.0,
        "payout_count": payout_count,
        "winning_days": winning_days,
        "days_profit_ge_150": days_ge_150,
        "skips_n0": int(res.skips_n0),
        "exhausted": bool(res.terminated_by_exhaustion),
        "n_offered": len(paths_by_day),
        "n_ambiguous": sum(1 for p in paths_by_day.values()
                           if p.ambiguous_stop_vs_floor),
    }


# R2.1 PHASE G: the R2 necessary-conditions boolean ("any payout AND not
# all skipped") is RETRACTED as a verdict gate — mechanical METRICS stay,
# the reduction rule is Aaron's to freeze. Until then no feasibility
# boolean may enter a VerdictInput, which keeps the Checkpoint-0 verdict
# unreachable (see epistemic_go_gate_input).
FEASIBILITY_GATE_STATUS = "DECISION_REQUIRED"

# R2.3 PHASE D: per-metric readiness — replaces the blanket YES.
FEASIBILITY_METRICS_STATUS = MappingProxyType({
    "payout_realization": "COMPUTED",
    "payout_count": "COMPUTED",
    "n0_skip_rate": "COMPUTED",
    "ambiguous_share": "COMPUTED",
    "exhaustion_share": "COMPUTED",
    "winning_days": "COMPUTED",              # ledger daily balance delta
    "days_profit_ge_150": "COMPUTED",        # frozen Lucid qualifying floor
    "contract_cap_hits": "PENDING_ENGINEERING",   # no per-day n on events
    "e2_over_budget_days": "PENDING_ENGINEERING",  # needs record-level pipe
    "qualifying_distribution_vs_payout_requirements":
        "PENDING_ENGINEERING",
})


def _nonneg_int(v, allow_none=False):
    if v is None and allow_none:
        return True
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


@dataclass(frozen=True, slots=True)
class FeasibilityObservation:
    """ONE raw feasibility observation for one (world, start-phase) path
    (R2.3 PHASE D) — the atoms every FeasibilityEvidence scalar is
    recomputed from. `contract_cap_hits` / `e2_over_budget_days` are None
    while their event plumbing is PENDING_ENGINEERING — never a forged 0.
    """
    world_index: int
    phase_offset: int
    offered: int
    skips_n0: int
    payout_realized: bool
    payout_count: int
    winning_days: int
    days_profit_ge_150: int
    exhausted: bool
    ambiguous_days: int
    contract_cap_hits: object = None
    e2_over_budget_days: object = None

    def __post_init__(self):
        ok = (_nonneg_int(self.world_index)
              and _nonneg_int(self.phase_offset)
              and _nonneg_int(self.offered)
              and _nonneg_int(self.skips_n0)
              and _nonneg_int(self.payout_count)
              and _nonneg_int(self.winning_days)
              and _nonneg_int(self.days_profit_ge_150)
              and _nonneg_int(self.ambiguous_days)
              and isinstance(self.payout_realized, bool)
              and isinstance(self.exhausted, bool)
              and _nonneg_int(self.contract_cap_hits, allow_none=True)
              and _nonneg_int(self.e2_over_budget_days, allow_none=True)
              and self.skips_n0 <= self.offered
              and self.ambiguous_days <= self.offered)
        if not ok:
            raise MCInputError("feasibility_observation_invalid",
                               f"world={self.world_index!r} "
                               f"phase={self.phase_offset!r}")


def _feasibility_derived(observations: tuple, expected_n: int) -> dict:
    """The ONE derivation of every feasibility scalar from observations."""
    if len(observations) != int(expected_n):
        raise MCInputError(
            "feasibility_observations_incomplete",
            f"{len(observations)} observations != expected {expected_n}")
    keys = [(o.world_index, o.phase_offset) for o in observations]
    if len(set(keys)) != len(keys):
        raise MCInputError("feasibility_observations_duplicate",
                           "repeated (world, phase) observation")
    n = len(observations)
    offered = sum(o.offered for o in observations)
    return {
        "n_paths": n,
        "payout_realized_share": (sum(1 for o in observations
                                      if o.payout_realized) / n
                                  if n else 0.0),
        "total_skips_n0": sum(o.skips_n0 for o in observations),
        "total_offered": offered,
        "exhausted_share": (sum(1 for o in observations if o.exhausted) / n
                            if n else 0.0),
        "ambiguous_share": (sum(o.ambiguous_days for o in observations)
                            / offered if offered else 0.0),
    }


@dataclass(frozen=True)
class FeasibilityEvidence:
    """Feasibility METRICS recomputed from the COMPLETE immutable raw
    observations (R2.3 PHASE D — no caller-declared scalar can exist:
    `__post_init__` re-derives everything and refuses mismatches; a
    removed, duplicated or tampered observation is caught by the same
    derivation). Bound to prepared_digest + combo + scenario + theta +
    B + M + seed. No `feasible` boolean exists anywhere: the reduction
    rule stays DECISION_REQUIRED for Aaron."""
    observations: tuple
    expected_n: int
    n_paths: int
    payout_realized_share: float
    total_skips_n0: int
    total_offered: int
    exhausted_share: float
    ambiguous_share: float
    prepared_digest: str
    platform: str
    engine: str
    scenario: str
    channel: str
    B: int
    M: int
    master_seed: int
    gate_status: str = FEASIBILITY_GATE_STATUS

    def __post_init__(self):
        obs = tuple(self.observations)
        object.__setattr__(self, "observations", obs)
        for o in obs:
            if type(o) is not FeasibilityObservation:
                raise MCInputError("feasibility_observation_invalid",
                                   f"non-observation element {type(o)}")
        want = _feasibility_derived(obs, self.expected_n)
        for field_name, expected in want.items():
            if getattr(self, field_name) != expected:
                raise MCInputError(
                    "feasibility_derived_stats_mismatch",
                    f"{field_name}: declared "
                    f"{getattr(self, field_name)!r} != derived "
                    f"{expected!r}")
        if self.gate_status != FEASIBILITY_GATE_STATUS:
            raise MCInputError("feasibility_gate_status_invalid",
                               self.gate_status)

    @staticmethod
    def from_observations(observations, expected_n, *, prepared_digest,
                          platform, engine, scenario, channel, B, M,
                          master_seed) -> "FeasibilityEvidence":
        obs = tuple(observations)
        d = _feasibility_derived(obs, expected_n)
        return FeasibilityEvidence(
            observations=obs, expected_n=int(expected_n),
            prepared_digest=prepared_digest, platform=platform,
            engine=engine, scenario=scenario, channel=channel,
            B=int(B), M=int(M), master_seed=int(master_seed), **d)


def _canonical_float_tuple(values, what: str) -> tuple:
    """R2.3 PHASE C/D: canonicalize a sample container to a PLAIN-FLOAT
    tuple — breaking any aliasing with the caller's container — refusing
    bools (a bool is not a sample), non-numerics and non-finite values."""
    out = []
    for x in values:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise MCInputError("epistemic_samples_invalid",
                               f"{what}: non-numeric entry {x!r}")
        f = float(x)
        if not math.isfinite(f):
            raise MCInputError("epistemic_samples_invalid",
                               f"{what}: non-finite entry {x!r}")
        out.append(f)
    return tuple(out)


def _epistemic_derived(world_means: tuple, within_world_ses: tuple,
                       B: int) -> dict:
    """The ONE derivation of every epistemic statistic from raw samples —
    used by BOTH the constructor helper and the self-authentication check
    (R2.2 PHASE C), so a declared statistic can never disagree silently."""
    arr = np.asarray(world_means, dtype=float)
    # R2.1 PHASE D: NaN/inf/empty samples and negative/non-finite SEs are
    # refusals — a quantile computed over garbage is not evidence.
    if arr.size == 0 or not np.isfinite(arr).all():
        raise MCInputError("epistemic_samples_invalid",
                           "world means empty or non-finite")
    ses = [float(s) for s in within_world_ses]
    if any((not math.isfinite(s)) or s < 0.0 for s in ses):
        raise MCInputError("epistemic_samples_invalid",
                           "within-world SEs negative or non-finite")
    # R2.2 PHASE C: sample counts must equal B — one mean and one SE per
    # world, no truncation, no padding.
    if arr.size != int(B) or len(ses) != int(B):
        raise MCInputError("epistemic_samples_invalid",
                           f"len(world_means)={arr.size} "
                           f"len(within_world_ses)={len(ses)} != B={B}")
    between_sd = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
    max_se = max(ses) if ses else 0.0
    # frozen: MC SS5 rule (d) — within-world MCSE <= 10% of the
    # between-world SD, computed from ACTUAL samples (never declared).
    # R2.1 PHASE D: zero between-world variance passes ONLY with zero
    # within-world MCSE.
    if between_sd == 0.0:
        mcse_ok = (max_se == 0.0)
    else:
        mcse_ok = max_se <= MCSE_MAX_FRACTION * between_sd
    return {
        "p5": float(np.percentile(arr, 5)),
        "median": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "between_world_sd": between_sd,
        "max_within_world_se": max_se,
        "mcse_ok": mcse_ok,
    }


@dataclass(frozen=True)
class EpistemicResult:
    """B world-level mean monthly prop_operating_EVs + decision quantiles.
    THE ONLY object Checkpoint-0 statistics may be read from. Carries its
    own provenance (prepared digest, B, master seed), the COMPLETE raw
    within-world SEs and the mechanically computed feasibility evidence.

    SELF-AUTHENTICATING (R2.2 PHASE C): `__post_init__` re-derives every
    statistic from the raw samples and refuses any disagreement — direct
    construction with forged p5/median/p95/mcse_ok, and
    `dataclasses.replace` of any derived field, both fail
    deterministically. There is no bypass: the check lives on the type."""
    platform: str
    engine: str
    scenario: str
    channel: str
    world_means: tuple
    within_world_ses: tuple           # COMPLETE per-world SEs (len == B)
    p5: float
    median: float
    p95: float
    mcse_ok: bool
    max_within_world_se: float
    between_world_sd: float
    B: int
    M: int                            # start-phase count ACTUALLY used
    master_seed: int
    prepared_digest: str
    feasibility: FeasibilityEvidence

    def __post_init__(self):
        # R2.3 PHASE D.1: CANONICALIZE FIRST — the samples become plain-
        # float tuples on the instance BEFORE the first derivation, so a
        # list-constructed instance shares no container with the caller
        # and post-construction source mutation cannot diverge anything.
        object.__setattr__(self, "world_means",
                           _canonical_float_tuple(self.world_means,
                                                  "world_means"))
        object.__setattr__(self, "within_world_ses",
                           _canonical_float_tuple(self.within_world_ses,
                                                  "within_world_ses"))
        if not self.world_means:
            raise MCInputError("epistemic_samples_invalid",
                               "world means empty")
        # R2.3 PHASE D.2: canonical identity invariants.
        for name, v in (("B", self.B), ("M", self.M),
                        ("master_seed", self.master_seed)):
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise MCInputError("epistemic_identity_invalid",
                                   f"{name}={v!r}")
        if not isinstance(self.prepared_digest, str) \
                or len(self.prepared_digest) != 64:
            raise MCInputError("epistemic_identity_invalid",
                               "prepared_digest not 64-hex")
        want = _epistemic_derived(self.world_means, self.within_world_ses,
                                  self.B)
        for field_name, expected in want.items():
            got = getattr(self, field_name)
            if got != expected:
                raise MCInputError(
                    "epistemic_derived_stats_mismatch",
                    f"{field_name}: declared {got!r} != derived "
                    f"{expected!r} from the raw samples")
        # R2.3 PHASE D.6: the feasibility evidence must be BOUND to this
        # exact result identity — a foreign combo's observations refuse.
        fe = self.feasibility
        if type(fe) is not FeasibilityEvidence:
            raise MCInputError("feasibility_binding_mismatch",
                               "feasibility is not a FeasibilityEvidence")
        binding = (fe.prepared_digest, fe.platform, fe.engine, fe.scenario,
                   fe.channel, fe.B, fe.M, fe.master_seed)
        own = (self.prepared_digest, self.platform, self.engine,
               self.scenario, self.channel, self.B, self.M,
               self.master_seed)
        if binding != own:
            raise MCInputError("feasibility_binding_mismatch",
                               f"{binding} != {own}")

    @staticmethod
    def from_world_means(platform, engine, scenario, channel, world_means,
                         *, within_world_ses, B, M, master_seed,
                         prepared_digest_value,
                         feasibility) -> "EpistemicResult":
        wm = tuple(float(x) for x in world_means)
        ses = tuple(float(s) for s in (within_world_ses or ()))
        d = _epistemic_derived(wm, ses, B)
        return EpistemicResult(
            platform=platform, engine=engine, scenario=scenario,
            channel=channel, world_means=wm, within_world_ses=ses,
            p5=d["p5"], median=d["median"], p95=d["p95"],
            mcse_ok=d["mcse_ok"],
            max_within_world_se=d["max_within_world_se"],
            between_world_sd=d["between_world_sd"], B=int(B), M=int(M),
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
    pdig = prepared_digest(prepared)
    world_means = []
    ses = []
    observations = []
    for wi, world in enumerate(worlds):
        if len(world) != n_slots:
            raise MCInputError("world_length_mismatch",
                               f"{len(world)} != {n_slots}")
        paths = _paths_for_world(prepared, world, channel, engine, scenario)
        evs = []
        for off in offsets:
            s = _lifecycle_stats(prepared, platform, paths, off)
            evs.append(s["monthly_ev"])
            observations.append(FeasibilityObservation(
                world_index=wi, phase_offset=int(off),
                offered=s["n_offered"], skips_n0=s["skips_n0"],
                payout_realized=s["payout_realized"],
                payout_count=s["payout_count"],
                winning_days=s["winning_days"],
                days_profit_ge_150=s["days_profit_ge_150"],
                exhausted=s["exhausted"],
                ambiguous_days=s["n_ambiguous"]))
        world_means.append(float(np.mean(evs)))
        n = len(evs)
        ses.append(float(np.std(evs, ddof=1) / math.sqrt(n))
                   if n > 1 else 0.0)
    feasibility = FeasibilityEvidence.from_observations(
        observations, expected_n=B * len(offsets), prepared_digest=pdig,
        platform=platform, engine=engine, scenario=scenario,
        channel=channel, B=B, M=len(offsets), master_seed=master_seed)
    return EpistemicResult.from_world_means(
        platform, engine, scenario, channel, world_means,
        within_world_ses=ses, B=B, M=len(offsets),
        master_seed=master_seed,
        prepared_digest_value=pdig,
        feasibility=feasibility)


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
    # R2.1 PHASE G: NO feasibility boolean exists until Aaron freezes the
    # metric->boolean reduction rule — the gate refuses HERE, which keeps
    # every Checkpoint-0 verdict unreachable (CHECKPOINT0_VERDICT_
    # REACHABLE=NO). The metrics themselves live on
    # cons.feasibility/stress.feasibility for the decision packet.
    raise MCInputError(
        "feasibility_gate_decision_required",
        "the feasibility metric->boolean rule is not frozen anywhere; "
        "Aaron must rule (see MC_DR5_BUILD_PACKET feasibility decision "
        "packet) before any VerdictInput can be built")


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
    grid, with provenance (R2 PHASE E; hardened R2.1 PHASE C): the OUTER
    metadata is never trusted — `validate_inner_binding` cross-checks
    every claim against the INNER EpistemicResults, so changing an outer
    number cannot impersonate a differently-scaled run."""
    run_label: str                # 'base' | 'double_B' | 'double_K' |
    #                               'seed_<n>'
    axis: str                     # 'base' | 'B' | 'K' | 'seed'
    B: int
    M: int                        # start-phase count actually used
    K: int                        # grid repeats per seed (frozen 200)
    master_seed: int
    prepared_digest: str
    results: Mapping              # combo_id -> (cons: EpistemicResult,
    #                                            stress: EpistemicResult)

    def __post_init__(self):
        # R2.3 PHASE D.3: DEEP-FREEZE the results mapping — a plain dict
        # of [cons, stress] lists becomes an immutable mapping of tuples,
        # sharing no container with the caller.
        frozen = {}
        for cid, pair in dict(self.results).items():
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise MCInputError("run_evidence_inner_mismatch:combo",
                                   f"{self.run_label}:{cid} not a "
                                   "(cons, stress) pair")
            frozen[cid] = (pair[0], pair[1])
        object.__setattr__(self, "results",
                           MappingProxyType(frozen))

    def validate_inner_binding(self) -> None:
        """R2.1 PHASE C: every OUTER field must agree with every INNER
        result — B (and the actual world_means length), M, master_seed,
        prepared_digest, the primary theta channel, the combo labels and
        the scenario roles. Refusal codes are per-field."""
        for cid, pair in self.results.items():
            if not (isinstance(pair, tuple) and len(pair) == 2):
                raise MCInputError("run_evidence_inner_mismatch:combo",
                                   f"{self.run_label}:{cid} not a "
                                   "(cons, stress) pair")
            cons, stress = pair
            for r in (cons, stress):
                if type(r) is not EpistemicResult:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:combo",
                        f"{self.run_label}:{cid} carries a non-epistemic "
                        "object")
                if r.B != self.B or len(r.world_means) != self.B:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:B",
                        f"{self.run_label}:{cid} outer B={self.B} inner "
                        f"B={r.B} len={len(r.world_means)}")
                if r.M != self.M:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:M",
                        f"{self.run_label}:{cid} outer M={self.M} inner "
                        f"M={r.M}")
                if r.master_seed != self.master_seed:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:master_seed",
                        f"{self.run_label}:{cid} outer "
                        f"{self.master_seed} inner {r.master_seed}")
                if r.prepared_digest != self.prepared_digest:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:prepared_digest",
                        f"{self.run_label}:{cid}")
                if r.channel != PRIMARY_THETA_CHANNEL:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:channel",
                        f"{self.run_label}:{cid} carries {r.channel!r}")
            platform, engine, _policy = cid.split("|")
            for r in (cons, stress):
                if r.platform != platform or r.engine != engine:
                    raise MCInputError(
                        "run_evidence_inner_mismatch:combo",
                        f"{self.run_label}:{cid} inner labels "
                        f"{r.platform}/{r.engine}")
            if cons.scenario != "Conservative" or \
                    stress.scenario != "Stress":
                raise MCInputError(
                    "run_evidence_inner_mismatch:scenario",
                    f"{self.run_label}:{cid} roles "
                    f"{cons.scenario}/{stress.scenario}")
        if set(self.results) != PRIMARY_VERDICT_GRID:
            raise MCInputError(
                "primary_grid_coverage_violation",
                f"run {self.run_label}: got {sorted(self.results)}")

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


# frozen: SEED_MANIFEST quoted_seed_convention — the base/quoted seed is
# the FIRST frozen master seed, fixed before any data was seen.
BASE_MASTER_SEED = RESEARCH_BOOTSTRAP_SEEDS[0]        # 7


@dataclass(frozen=True, slots=True)
class ExhaustiveSupportCertificate:
    """IR-29 (R2.3) — the M axis's convergence obligation: PROOF that the
    exhaustively enumerated start-phase support was covered completely,
    uniquely, and exactly once per phase, by every Primary combo, on the
    SAME prepared calendar. Replaces "M doubling"; never a pseudo-2M."""
    prepared_digest: str
    support: tuple                    # the claimed start-phase offsets

    def validate(self, base: RunEvidence,
                 prepared: "PreparedMCInput") -> None:
        if self.prepared_digest != prepared_digest(prepared):
            raise MCInputError("m_support_wrong_calendar",
                               "certificate bound to a different "
                               "prepared input")
        legal = tuple(prepared.calendar.first_month_offsets)
        support = tuple(int(i) for i in self.support)
        if len(set(support)) != len(support):
            raise MCInputError("m_support_duplicate_phase",
                               f"{support}")
        missing = sorted(set(legal) - set(support))
        extra = sorted(set(support) - set(legal))
        if missing or extra:
            raise MCInputError(
                "m_support_incomplete" if missing else "m_support_extra",
                f"missing={missing} extra={extra}")
        if support != legal:
            raise MCInputError("m_support_order_violation",
                               f"{support} != legal enumeration {legal}")
        # every phase executed exactly once by every Primary combo: each
        # inner result's M is the actual offset count used, and its
        # prepared digest binds it to the SAME calendar (offsets are part
        # of the digest preimage) — so M == len(legal) proves one-pass
        # exhaustive execution, and duplication cannot fake a "2M" (the
        # duplicate would break the unique-support check above).
        if base.M != len(legal):
            raise MCInputError("m_support_execution_mismatch",
                               f"base M={base.M} != |support|={len(legal)}")
        for cid, (cons, stress) in base.results.items():
            for r in (cons, stress):
                if r.M != len(legal):
                    raise MCInputError(
                        "m_support_execution_mismatch",
                        f"{cid}: inner M={r.M} != |support|={len(legal)}")


def convergence_from_evidence(base: RunEvidence,
                              doubled_by_axis: Mapping,
                              seed_runs: Mapping, *,
                              m_support_certificate:
                              "ExhaustiveSupportCertificate | None" = None,
                              prepared: "PreparedMCInput | None" = None,
                              ) -> ConvergenceReport:
    """Compute MC SS5 rules (a)-(d) FROM run evidence (R2 PHASE E,
    hardened R2.1 PHASE C). Validation order (so every violation surfaces
    with its OWN code):

    1. inner/outer binding of EVERY supplied run (RunEvidence.
       validate_inner_binding — outer metadata cannot impersonate);
    2. doubling axes set == {B, M, K};
    3. B-axis provenance/scale relations, seed-run set/identity, and the
       FROZEN base scales (B=1000, K=200, base seed 7, primary theta) —
       a small-scale or off-seed base refuses with
       "frozen_scale_violation";
    4. M axis: REFUSED — MC SS5 fixes M as the exhaustively enumerated
       start-phase set; doubling has no unique frozen meaning
       (DECISION_REQUIRED_M_AXIS; nothing is invented here);
    5. K axis: REFUSED — grid replay is BLOCKED (missing per-day
       DAY_STRATA), so no ACTUAL K-doubled evidence can exist; outer
       metadata may not impersonate it.

    Production convergence is therefore STRUCTURALLY UNSATISFIABLE until
    Aaron rules on M and the grid authority — the honest fail-closed
    state. Categories/drift/MCSE computation below steps 4-5 is retained
    for the post-ruling wiring and is unreachable today."""
    if base.axis != "base":
        raise MCInputError("axis_identity_mismatch",
                           f"base run carries axis={base.axis!r}")
    base.validate_inner_binding()
    # (1) inner/outer binding + B-axis relations for every SUPPLIED run —
    # a tampered outer number surfaces its own code before anything else.
    for axis in sorted(doubled_by_axis):
        run = doubled_by_axis[axis]
        run.validate_inner_binding()
        if axis == "B":
            _check_run_provenance(base, run, "B")
    if isinstance(seed_runs, Mapping):
        for seed, run in seed_runs.items():
            run.validate_inner_binding()
            if run.prepared_digest != base.prepared_digest:
                raise MCInputError("provenance_mismatch", f"seed_{seed}")
            if run.master_seed != seed:
                raise MCInputError(
                    "run_evidence_inner_mismatch:master_seed",
                    f"seed run {seed} carries master_seed="
                    f"{run.master_seed}")
    # (1b) seed-SET completeness — an identity-level requirement, checked
    # BEFORE the structural M/K refusals so a wrong seed set surfaces
    # with its own code.
    if set(seed_runs) != set(RESEARCH_BOOTSTRAP_SEEDS):
        raise MCInputError("seed_set_violation",
                           f"need exactly {tuple(RESEARCH_BOOTSTRAP_SEEDS)},"
                           f" got {sorted(seed_runs)}")
    # (2) frozen production scales for the BASE run (R2.1 PHASE C.3)
    if (base.B != B_WORLDS_FROZEN or base.K != K_PER_SEED_FROZEN
            or base.master_seed != BASE_MASTER_SEED):
        raise MCInputError(
            "frozen_scale_violation",
            f"base must run B={B_WORLDS_FROZEN}, K={K_PER_SEED_FROZEN}, "
            f"master_seed={BASE_MASTER_SEED}; got B={base.B}, "
            f"K={base.K}, seed={base.master_seed}")
    # (3) IR-29: M owes an EXHAUSTIVE SUPPORT CERTIFICATE, not a doubled
    # run — an M entry in doubled_by_axis is a ruling violation; the
    # certificate is validated against the prepared input's own legal
    # enumeration (missing/extra/duplicate/order/wrong-calendar refuse).
    if "M" in doubled_by_axis:
        raise MCInputError(
            "m_axis_doubling_forbidden_by_ir29",
            "IR-29: M is exempt from doubling — supply an "
            "ExhaustiveSupportCertificate instead")
    if m_support_certificate is None or prepared is None:
        raise MCInputError(
            "m_support_certificate_missing",
            "IR-29 requires an ExhaustiveSupportCertificate plus the "
            "prepared input it binds to")
    if type(m_support_certificate) is not ExhaustiveSupportCertificate:
        raise MCInputError("m_support_certificate_missing",
                           "wrong certificate type")
    m_support_certificate.validate(base, prepared)
    # (4) K — grid replay BLOCKED (GRID Option B tooling exists but the
    # supplement is UNEXECUTED): no actual K-doubled evidence can exist
    # and metadata may not impersonate it.
    if "K" in doubled_by_axis:
        raise MCInputError(
            "k_axis_evidence_blocked_grid_replay",
            "grid replay is BLOCKED (EXACT_PER_DAY_DAY_STRATA supplement "
            "MC-DS-S001 not yet executed) — no actual K-doubled evidence "
            "can exist and metadata may not impersonate it")
    # (5) axes-set completeness — reachable only when no K entry was
    # supplied at all.
    if set(doubled_by_axis) != DOUBLING_AXES:
        raise MCInputError("doubling_axes_violation",
                           f"need exactly {sorted(DOUBLING_AXES)}, got "
                           f"{sorted(doubled_by_axis)}")
    raise AssertionError(
        "unreachable: every legal axes-set carries a K entry and "
        "refuses above until the GRID-B supplement executes")


def _reduce_primary_from_base(base: RunEvidence) -> dict:
    """R2.2 PHASE D — THE single internal reduction: Primary VerdictInputs
    are derived EXCLUSIVELY from `base.results` (Conservative/Stress,
    platform, engine, theta channel and prepared digest all come from the
    same RunEvidence). There is no public entry that accepts externally
    built VerdictInputs, so a hand-made positive grid has no callable
    path into the verdict or the seal.

    Today this reduction refuses deterministically at the feasibility
    gate inside `epistemic_go_gate_input` (FEASIBILITY_GATE=
    DECISION_REQUIRED) — CHECKPOINT0_VERDICT_REACHABLE=NO. When Aaron
    freezes the feasibility rule, the ONLY legal extension is a typed,
    provenance-bound decision-evidence object attached to this same
    reduction — never a reopened boolean."""
    base.validate_inner_binding()
    return {cid: epistemic_go_gate_input(cons, stress)
            for cid, (cons, stress) in sorted(base.results.items())}


def verdict_and_seal_from_evidence(prepared: PreparedMCInput, *,
                                   base: RunEvidence,
                                   doubled_by_axis: Mapping,
                                   seed_runs: Mapping,
                                   m_support_certificate:
                                   "ExhaustiveSupportCertificate | None"
                                   = None) -> dict:
    """The ONLY path to a Checkpoint-0 verdict AND its seal candidate
    (R2.2 PHASE D — the sealed `primary` table and the mechanical verdict
    are read from the SAME internal reduction object; convergence is
    recomputed from evidence inside; nothing caller-declared survives).

    Structurally unreachable today: the reduction refuses at the
    feasibility gate, convergence refuses at M/K — every refusal is the
    honest missing-decision, not a gap."""
    from itsf.mc.verdict import apply_verdict
    if base.prepared_digest != prepared_digest(prepared):
        raise MCInputError("provenance_mismatch",
                           "base evidence was not computed from THIS "
                           "prepared input")
    digest_before = prepared_digest(prepared)
    reduction = _reduce_primary_from_base(base)
    convergence_from_evidence(base, doubled_by_axis, seed_runs,
                              m_support_certificate=m_support_certificate,
                              prepared=prepared)
    verdict = apply_verdict(dict(reduction))
    digest_after = prepared_digest(prepared)
    if digest_before != digest_after:
        raise MCInputError("prepared_digest_instability",
                           f"{digest_before[:12]} -> {digest_after[:12]}")
    return {
        "schema": "mc_verdict_inputs.v3",
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "method_digest": prepared.method_digest,
        "prepared_digest": digest_before,
        "primary_theta_channel": PRIMARY_THETA_CHANNEL,
        "bundle_file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "primary": {
            cid: {"p5_cons": v.p5_cons, "median_cons": v.median_cons,
                  "median_stress": v.median_stress, "p95_cons": v.p95_cons,
                  "feasible": v.feasible, "platform": v.platform,
                  "engine": v.engine, "channel": v.channel}
            for cid, v in sorted(reduction.items())},
        "convergence_evidence": {
            "base_run": base.run_label,
            "doubled_axes": sorted(doubled_by_axis),
            "seed_runs": sorted(seed_runs)},
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
