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

# N01 PHASE D6: numpy is no longer imported here. Every statistic is
# reduced by `itsf.mc.atoms` in plain float arithmetic so the INDEPENDENT
# `itsf.mc.cold_reducer` can agree bitwise; numpy remains where it
# belongs, inside `itsf.mc.bootstrap`'s PCG64 world construction.

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS, TradePathRecord
from itsf.mc import atoms as mc_atoms
from itsf.mc import bootstrap as mc_bootstrap
from itsf.mc import cold_reducer as mc_cold
from itsf.mc import orchestrator as orch
from itsf.mc.account import PRIMARY_POLICY
# NOT_APPLICABLE / PENDING_RULING / PENDING_ENGINEERING are imported for
# RE-EXPORT: report and decision-packet code reads them as
# `consumer.<TOKEN>` and must never re-spell the tokens as bare strings.
from itsf.mc.atoms import (NOT_APPLICABLE, PENDING_ENGINEERING,  # noqa: F401
                           PENDING_RULING, MCInputError, ObservationSet,
                           SimulationPathObservation)
from itsf.s0.study import THETA_PRIMARY, THETA_SECONDARY

# frozen: S0 §7 L133 — "θ 主 0.5、副 0.3（完整报告，不得事后升格）".
# Checkpoint-0 accepts ONLY the primary channel; the secondary channel is
# report/sensitivity-only and can NEVER be promoted into the verdict.
PRIMARY_THETA_CHANNEL = f"theta_{THETA_PRIMARY}"        # 'theta_0.5'
SECONDARY_THETA_CHANNEL = f"theta_{THETA_SECONDARY}"    # 'theta_0.3'

# --- frozen axes (MC SS2.5 / SS4.1 / SS5) ----------------------------------
# N01 PHASE D1: the axes now have ONE definition, in the atom layer; these
# names remain as re-exports so existing consumers keep working.
ENGINES = mc_atoms.ENGINES
SCENARIOS = mc_atoms.SCENARIOS
PLATFORMS = mc_atoms.PLATFORMS
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


# `MCInputError` (fail-closed refusal carrying a machine-readable `code`,
# source matrix R13) now LIVES in itsf.mc.atoms so the atom layer and the
# consumer raise ONE type without an import cycle. Imported above and
# re-exported here under its historical name — `consumer.MCInputError`
# remains the same class object every existing caller already catches.
__all_error__ = MCInputError


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
# _usd = 150. Re-exported from the atom layer (single definition).
QUALIFYING_DAY_MIN_PROFIT_USD = mc_atoms.QUALIFYING_DAY_MIN_PROFIT_USD


def lifecycle_config_for(platform: str):
    """THE lifecycle configuration every Primary path runs under. One
    definition, used by the forward run AND by the cold replay."""
    if platform not in PLATFORMS:
        raise MCInputError("axis_violation", platform)
    return orch.LifecycleConfig(platform=platform,
                                sizing_policy=PRIMARY_POLICY)


def _run_path_atom(prepared: PreparedMCInput, *, platform: str,
                   engine: str, scenario: str, channel: str,
                   world: Sequence[str], world_index: int,
                   phase_offset: int, lifecycle_config_digest: str,
                   master_seed: int, prepared_digest_value: str
                   ) -> SimulationPathObservation:
    """Run ONE (world, start-phase) lifecycle and emit ONE atom.

    THE only place a lifecycle is executed. The forward run and the cold
    replay both call this, so a divergence between them can only come
    from the inputs — never from two code paths.

    Day facts come from `atoms.path_facts_from_events`, the ONE narrow
    adapter over lane S2's platform-authoritative event fields. The
    former neighbouring-balance-delta derivation is DELETED: it double-
    counted payout debits and produced phantom deltas across account
    generations."""
    cfg = lifecycle_config_for(platform)
    days = list(prepared.calendar.days)
    window = days[phase_offset:]
    paths = _paths_for_world(prepared, world, channel, engine, scenario)
    res = orch.run_lifecycle(cfg, days, paths, start_offset=phase_offset)
    facts = mc_atoms.path_facts_from_events(res.events, engine=engine,
                                            platform=platform)
    # WINDOW-scoped offered/ambiguous counts. The R2.3 code counted over
    # the WHOLE calendar's path map, which over-counted whenever
    # start_offset > 0 (the trimmed prefix days can never be offered).
    window_ids = {td.day_id for td in window}
    offered = sum(1 for d in paths if d in window_ids)
    ambiguous = sum(1 for d, p in paths.items()
                    if d in window_ids and p.ambiguous_stop_vs_floor)
    if facts["event_days"] > len(window):
        raise MCInputError(
            "atom_event_days_exceed_window",
            f"{facts['event_days']} events > window {len(window)}")
    return SimulationPathObservation(
        prepared_digest=prepared_digest_value,
        lifecycle_config_digest=lifecycle_config_digest,
        world_index=int(world_index),
        world_digest=mc_atoms.world_digest(world),
        phase_offset=int(phase_offset),
        platform=platform, engine=engine, scenario=scenario,
        theta_channel=channel, master_seed=int(master_seed),
        monthly_prop_operating_ev=float(
            res.ledger_report["prop_operating_ev_monthly"]),
        days_in_window=len(window),
        offered_days=offered,
        executed_trade_days=facts["executed_trade_days"],
        skips_n0=int(res.skips_n0),
        payout_count=facts["payout_count"],
        winning_days=facts["winning_days"],
        days_profit_ge_150=facts["days_profit_ge_150"],
        qualifying_days=facts["qualifying_days"],
        exhausted=bool(res.terminated_by_exhaustion),
        ambiguous_days=ambiguous,
        attempts_used=int(res.attempts_used),
        b2f_used=int(res.b2f_used_total),
        contract_cap_hits=facts["contract_cap_hits"],
        e2_over_budget_days=facts["e2_over_budget_days"])


# R2.1 PHASE G: the R2 necessary-conditions boolean ("any payout AND not
# all skipped") is RETRACTED as a verdict gate — mechanical METRICS stay,
# the reduction rule is Aaron's to freeze. Until then no feasibility
# boolean may enter a VerdictInput, which keeps the Checkpoint-0 verdict
# unreachable (see epistemic_go_gate_input).
FEASIBILITY_GATE_STATUS = "DECISION_REQUIRED"

# N01 PHASE D1: per-metric readiness. Every metric is now reduced from
# the SAME atom set; the ones marked PENDING_LANE_S2 are computable the
# moment lane S2 (node N02) emits the platform-authoritative day fields —
# until then the seam adapter REFUSES rather than approximating, so no
# metric is ever silently wrong.
FEASIBILITY_METRICS_STATUS = MappingProxyType({
    "payout_events": "COMPUTED",             # AccountEvent.payout_gross
    "n0_skip_rate": "COMPUTED",              # LifecycleResult.skips_n0
    "ambiguous_share": "COMPUTED",           # sealed record flag
    "exhaustion_share": "COMPUTED",          # LifecycleResult
    "attempts_used": "COMPUTED",             # LifecycleResult
    "b2f_used": "COMPUTED",                  # LifecycleResult
    "winning_days": "COMPUTED",              # AccountEvent.day_net_usd
    "days_profit_ge_150": "COMPUTED",        # AccountEvent.day_net_usd
    "qualifying_days": "COMPUTED",           # platform's OWN counter
    "contract_cap_hits": "COMPUTED",         # AccountEvent.cap_applied
    "e2_over_budget_days": "DECISION_REQUIRED",  # predicate unruled (S2)
    "qualifying_distribution_vs_payout_requirements":
        "DECISION_REQUIRED",                 # the RULE is Aaron's (N-D2)
})


@dataclass(frozen=True)
class FeasibilityEvidence:
    """RAW feasibility metrics reduced from the SAME `ObservationSet`
    every other statistic comes from (N01 PHASE D1).

    There is no `expected_n` (the expected count is a CONSEQUENCE of the
    B x legal-phase-support grid the ObservationSet already enforces),
    no caller-supplied observation tuple, and no identity field that can
    disagree with the trace — every identity is READ from the set.

    `__post_init__` is the in-type reducer: it recomputes the whole
    metric mapping from the atoms and refuses any disagreement. No
    `feasible` boolean exists anywhere in this type: the metric->boolean
    reduction rule stays DECISION_REQUIRED for Aaron (D7)."""
    observations: ObservationSet
    metrics: Mapping
    gate_status: str = FEASIBILITY_GATE_STATUS

    def __post_init__(self):
        if type(self.observations) is not ObservationSet:
            raise MCInputError(
                "feasibility_observations_invalid",
                f"{type(self.observations).__name__} is not an "
                "ObservationSet — feasibility has no other source")
        want = self.observations.feasibility_counts()
        got = dict(self.metrics)
        missing = sorted(set(want) - set(got))
        extra = sorted(set(got) - set(want))
        if missing or extra:
            raise MCInputError(
                "feasibility_derived_stats_mismatch",
                f"metric key set: missing={missing} extra={extra}")
        for name, expected in want.items():
            # TYPE-EXACT (N01 fix D-1): `n_paths=True` must not pass just
            # because the derived count happens to be 1.
            if not mc_atoms.strict_scalar_equal(got[name], expected):
                raise MCInputError(
                    "feasibility_derived_stats_mismatch",
                    f"{name}: declared {got[name]!r} "
                    f"({type(got[name]).__name__}) != derived "
                    f"{expected!r} ({type(expected).__name__}) from the "
                    "atom trace")
        object.__setattr__(self, "metrics", MappingProxyType(dict(want)))
        if self.gate_status != FEASIBILITY_GATE_STATUS:
            raise MCInputError("feasibility_gate_status_invalid",
                               self.gate_status)

    # identity is READ from the trace; nothing here can be declared
    @property
    def prepared_digest(self) -> str:
        return self.observations.prepared_digest

    @property
    def platform(self) -> str:
        return self.observations.platform

    @property
    def engine(self) -> str:
        return self.observations.engine

    @property
    def scenario(self) -> str:
        return self.observations.scenario

    @property
    def channel(self) -> str:
        return self.observations.theta_channel

    @property
    def B(self) -> int:
        return self.observations.B

    @property
    def M(self) -> int:
        return self.observations.M

    @property
    def master_seed(self) -> int:
        return self.observations.master_seed

    @staticmethod
    def from_observations(observations: ObservationSet
                          ) -> "FeasibilityEvidence":
        if type(observations) is not ObservationSet:
            raise MCInputError(
                "feasibility_observations_invalid",
                f"{type(observations).__name__} is not an ObservationSet")
        return FeasibilityEvidence(
            observations=observations,
            metrics=observations.feasibility_counts())


def _type_label(value) -> str:
    """Diagnostic type name. For a sequence it also names the ELEMENT
    types, because that is where a bool-as-float impersonation hides —
    `(True, False)` and `(1.0, 0.0)` are both `tuple`."""
    name = type(value).__name__
    if isinstance(value, tuple):
        inner = sorted({type(x).__name__ for x in value})
        return f"{name}[{','.join(inner) or 'empty'}]"
    return name


def _epistemic_derived(observations: ObservationSet) -> dict:
    """THE ONE derivation of every epistemic statistic — reduced from the
    ATOM TRACE, never from caller-supplied sample containers.

    Quantiles use the frozen type-7 linear estimator implemented in plain
    float arithmetic (`atoms.percentile_linear`), so the INDEPENDENT cold
    reducer can agree BITWISE without sharing a line of code. (The R2.3
    code used `numpy.percentile`, whose internal lerp switches expression
    form at t >= 0.5 and cannot be reproduced bit-for-bit by an honest
    reimplementation; the estimator is the same, the evaluation order is
    now specified.)"""
    if type(observations) is not ObservationSet:
        raise MCInputError("epistemic_samples_invalid",
                           f"{type(observations).__name__} is not an "
                           "ObservationSet")
    means = observations.world_means()
    ses = observations.within_world_ses()
    if len(means) != observations.B or len(ses) != observations.B:
        # unreachable via ObservationSet (the key grid already proves the
        # world domain); kept as a belt-and-braces refusal.
        raise MCInputError("epistemic_samples_invalid",
                           f"len(world_means)={len(means)} "
                           f"len(within_world_ses)={len(ses)} != "
                           f"B={observations.B}")
    for x in means:
        if not math.isfinite(x):
            raise MCInputError("epistemic_samples_invalid",
                               "world means non-finite")
    for s in ses:
        if (not math.isfinite(s)) or s < 0.0:
            raise MCInputError("epistemic_samples_invalid",
                               "within-world SEs negative or non-finite")
    ordered = sorted(means)
    between_sd = mc_atoms.sample_sd(means)
    max_se = max(ses) if ses else 0.0
    # frozen: MC SS5 rule (d) — within-world MCSE <= 10% of the
    # between-world SD, computed from ACTUAL samples (never declared).
    # Zero between-world variance passes ONLY with zero within-world MCSE.
    if between_sd == 0.0:
        mcse_ok = (max_se == 0.0)
    else:
        mcse_ok = max_se <= MCSE_MAX_FRACTION * between_sd
    return {
        "world_means": tuple(means),
        "within_world_ses": tuple(ses),
        "p5": mc_atoms.percentile_linear(ordered, 5),
        "median": mc_atoms.percentile_linear(ordered, 50),
        "p95": mc_atoms.percentile_linear(ordered, 95),
        "between_world_sd": between_sd,
        "max_within_world_se": max_se,
        "mcse_ok": mcse_ok,
    }


@dataclass(frozen=True)
class EpistemicResult:
    """B world-level mean monthly prop_operating_EVs + decision quantiles,
    REDUCED FROM THE ATOM TRACE. THE ONLY object Checkpoint-0 statistics
    may be read from.

    N01 PHASE D1 — the R2.3 constructor `from_world_means(world_means=...,
    within_world_ses=..., feasibility=...)` is DELETED. It accepted THREE
    independent caller inputs that were only cross-checked against each
    other; a caller who supplied a coherent triple could describe a run
    that never happened. There is now exactly ONE input: the
    `ObservationSet`. Every statistic, the feasibility evidence and every
    identity field are derived from it, and `__post_init__` re-derives
    them all and refuses any disagreement (`dataclasses.replace` of a
    derived field fails the same way)."""
    observations: ObservationSet
    world_means: tuple
    within_world_ses: tuple           # COMPLETE per-world SEs (len == B)
    p5: float
    median: float
    p95: float
    mcse_ok: bool
    max_within_world_se: float
    between_world_sd: float
    feasibility: FeasibilityEvidence

    def __post_init__(self):
        if type(self.observations) is not ObservationSet:
            raise MCInputError(
                "epistemic_samples_invalid",
                f"{type(self.observations).__name__} is not an "
                "ObservationSet — there is no other statistic source")
        want = _epistemic_derived(self.observations)
        for field_name, expected in want.items():
            got = getattr(self, field_name)
            if isinstance(expected, tuple):
                # container canonicalisation (a caller list becomes a
                # tuple) is allowed; ELEMENT types are not negotiable.
                got = tuple(got)
                object.__setattr__(self, field_name, got)
                ok = mc_atoms.strict_float_sequence_equal(got, expected)
            else:
                ok = mc_atoms.strict_scalar_equal(got, expected)
            if not ok:
                raise MCInputError(
                    "epistemic_derived_stats_mismatch",
                    f"{field_name}: declared {got!r} "
                    f"({_type_label(got)}) != derived {expected!r} "
                    f"({_type_label(expected)}) from the atom trace")
        # the feasibility evidence must be reduced from THE SAME trace —
        # identity comparison is not enough, the OBJECT must match.
        fe = self.feasibility
        if type(fe) is not FeasibilityEvidence:
            raise MCInputError("feasibility_binding_mismatch",
                               "feasibility is not a FeasibilityEvidence")
        if fe.observations is not self.observations:
            if fe.observations.observations_digest != \
                    self.observations.observations_digest:
                raise MCInputError(
                    "feasibility_binding_mismatch",
                    f"feasibility trace "
                    f"{fe.observations.observations_digest[:12]} != "
                    f"result trace "
                    f"{self.observations.observations_digest[:12]}")

    # identity READ from the trace — nothing declarable
    @property
    def platform(self) -> str:
        return self.observations.platform

    @property
    def engine(self) -> str:
        return self.observations.engine

    @property
    def scenario(self) -> str:
        return self.observations.scenario

    @property
    def channel(self) -> str:
        return self.observations.theta_channel

    @property
    def B(self) -> int:
        return self.observations.B

    @property
    def M(self) -> int:
        """Start-phase count ACTUALLY executed (a consequence of the
        prepared calendar's legal support, never a declared scalar)."""
        return self.observations.M

    @property
    def master_seed(self) -> int:
        return self.observations.master_seed

    @property
    def prepared_digest(self) -> str:
        return self.observations.prepared_digest

    @property
    def lifecycle_config_digest(self) -> str:
        return self.observations.lifecycle_config_digest

    @property
    def observations_digest(self) -> str:
        return self.observations.observations_digest

    @staticmethod
    def from_observations(observations: ObservationSet
                          ) -> "EpistemicResult":
        """THE only constructor helper. One input, everything derived."""
        d = _epistemic_derived(observations)
        return EpistemicResult(
            observations=observations,
            feasibility=FeasibilityEvidence.from_observations(
                observations),
            **d)


def build_world_table(prepared: PreparedMCInput, *, channel: str, B: int,
                      master_seed: int) -> tuple:
    """COLD-REBUILD the world table from (prepared, seed, B, block,
    length) — the complete deterministic input set of
    `bootstrap.build_worlds`. Returns the worlds themselves; their
    content digests are what every atom binds to.

    The pool is the channel's ordered day sequence; the OUTPUT length is
    the full template slot count (MC SS4.1: the bootstrap fills EVERY
    template trading day)."""
    if channel not in prepared.day_sequences:
        raise MCInputError("axis_violation", f"channel {channel!r}")
    day_ids = prepared.day_sequences[channel]
    n_slots = len(prepared.calendar.days)
    worlds = mc_bootstrap.build_worlds(day_ids, B, master_seed,
                                       length=n_slots)
    for w in worlds:
        if len(w) != n_slots:
            raise MCInputError("world_length_mismatch",
                               f"{len(w)} != {n_slots}")
    return tuple(tuple(w) for w in worlds)


def run_observation_set(prepared: PreparedMCInput, *, run_label: str,
                        platform: str, engine: str, scenario: str,
                        channel: str, B: int,
                        master_seed: int) -> ObservationSet:
    """Execute the COMPLETE B x legal-phase-support grid and emit the
    atom trace. This is the ONE producer of atoms.

    `legal_phase_support` comes ONLY from the prepared authority
    (`prepared.calendar.first_month_offsets`); no caller may narrow,
    widen or reorder it, and no caller supplies an expected count — the
    count is a consequence of the grid.

    CRN: worlds derive ONLY from (day_ids, B, master_seed) via the frozen
    builder, so every (platform, engine, scenario) evaluated with the
    same arguments sees IDENTICAL worlds by construction."""
    if platform not in PLATFORMS:
        raise MCInputError("axis_violation", platform)
    if (engine, scenario) not in prepared.records:
        raise MCInputError("axis_violation", f"{engine}|{scenario}")
    support = tuple(prepared.calendar.first_month_offsets)
    worlds = build_world_table(prepared, channel=channel, B=B,
                               master_seed=master_seed)
    pdig = prepared_digest(prepared)
    cfg_digest = mc_atoms.lifecycle_config_digest_for(
        lifecycle_config_for(platform), engine=engine, scenario=scenario,
        theta_channel=channel)
    atoms = []
    for wi, world in enumerate(worlds):
        for off in support:
            atoms.append(_run_path_atom(
                prepared, platform=platform, engine=engine,
                scenario=scenario, channel=channel, world=world,
                world_index=wi, phase_offset=int(off),
                lifecycle_config_digest=cfg_digest,
                master_seed=master_seed, prepared_digest_value=pdig))
    obs = ObservationSet.from_atoms(
        atoms, run_label=run_label, platform=platform, engine=engine,
        scenario=scenario, theta_channel=channel,
        sizing_policy=PRIMARY_POLICY, B=B, master_seed=master_seed,
        prepared_digest=pdig, lifecycle_config_digest=cfg_digest,
        legal_phase_support=support)
    _bind_world_content(obs, worlds)
    return obs


def _bind_world_content(observations: ObservationSet,
                        worlds: Sequence[Sequence[str]]) -> None:
    """D4: each atom's `world_digest` must equal the COLD-REBUILT world
    table's corresponding entry. A trace that claims world b but carries
    another world's content refuses."""
    want = [mc_atoms.world_digest(w) for w in worlds]
    if len(want) != observations.B:
        raise MCInputError(
            "world_content_binding_mismatch",
            f"rebuilt table has {len(want)} worlds != B="
            f"{observations.B}")
    got = observations.world_digests()
    for i, (a, b) in enumerate(zip(got, want)):
        if a != b:
            raise MCInputError(
                "world_content_binding_mismatch",
                f"world {i}: trace {a[:12]} != cold-rebuilt {b[:12]}")


def run_epistemic(prepared: PreparedMCInput, *, platform: str, engine: str,
                  scenario: str, channel: str, B: int, master_seed: int,
                  run_label: str = "base") -> EpistemicResult:
    """Thin reduction over `run_observation_set` — kept as the historical
    public name. Every number it returns is reduced from the atoms."""
    return EpistemicResult.from_observations(run_observation_set(
        prepared, run_label=run_label, platform=platform, engine=engine,
        scenario=scenario, channel=channel, B=B,
        master_seed=master_seed))


@dataclass(frozen=True)
class AleatoricResult:
    """CONDITIONAL aleatoric distribution (MC SS5): the M single-attempt
    paths WITHIN ONE FIXED bootstrap world — reporting only, never a GO
    gate input. Binds the fixed world by digest.

    N01 PHASE D1: reduced from the SAME atom trace as the epistemic
    layer. It no longer re-executes lifecycles from a caller-supplied
    world (that was a PARALLEL simulation path whose numbers nothing
    forced to agree with the epistemic run)."""
    platform: str
    engine: str
    scenario: str
    channel: str
    world_index: int
    world_digest: str
    attempt_monthly_evs: tuple
    observations_digest: str


@dataclass(frozen=True)
class TotalPredictiveResult:
    """The B x M MIXTURE (MC SS5 total_predictive) — explicitly labelled
    a mixture, reduced from the SAME atoms. Reporting only."""
    platform: str
    engine: str
    scenario: str
    channel: str
    B: int
    M: int
    mixture_monthly_evs: tuple
    observations_digest: str


def run_conditional_aleatoric(observations: ObservationSet, *,
                              world_index: int) -> AleatoricResult:
    """M attempt paths inside ONE FIXED world (frozen: MC SS5 conditional
    aleatoric — "固定世界内 M 条账户路径的结果分布"), sliced out of the
    executed atom trace.

    D7: the caller NAMES the world; no fixed-world SELECTION rule exists
    here. Which world(s) the report fixes is Aaron's ruling (master plan
    N-D2: single pre-registered world / P5-P50-P95 neighbourhood / report
    every world), and inventing one would be a decision leak."""
    if type(observations) is not ObservationSet:
        raise MCInputError("aleatoric_source_invalid",
                           f"{type(observations).__name__} is not an "
                           "ObservationSet")
    evs = observations.conditional_aleatoric_evs(int(world_index))
    digests = observations.world_digests()
    return AleatoricResult(
        platform=observations.platform, engine=observations.engine,
        scenario=observations.scenario,
        channel=observations.theta_channel, world_index=int(world_index),
        world_digest=digests[int(world_index)],
        attempt_monthly_evs=evs,
        observations_digest=observations.observations_digest)


def run_total_predictive(observations: ObservationSet
                         ) -> TotalPredictiveResult:
    """The B x M mixture, reduced from the SAME atoms."""
    if type(observations) is not ObservationSet:
        raise MCInputError("aleatoric_source_invalid",
                           f"{type(observations).__name__} is not an "
                           "ObservationSet")
    return TotalPredictiveResult(
        platform=observations.platform, engine=observations.engine,
        scenario=observations.scenario,
        channel=observations.theta_channel, B=observations.B,
        M=observations.M,
        mixture_monthly_evs=observations.total_predictive_evs(),
        observations_digest=observations.observations_digest)


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

def _assert_config_digest(result: "EpistemicResult", *, layer: str,
                          where: str = "") -> str:
    """FOUR-LAYER exact equality of `lifecycle_config_digest` (D2).

    Layer 1 is enforced inside `ObservationSet` (atom vs set). Layers 2-4
    (container / cold-replay / seal) all call THIS function, which
    re-derives the digest from the LIVE frozen modules for the result's
    own axes — so a constant that moved between producing the evidence
    and sealing it is caught, with a per-layer refusal code."""
    if layer not in ("container", "cold_replay", "seal"):
        raise MCInputError("lifecycle_config_layer_unknown", layer)
    want = mc_atoms.lifecycle_config_digest_for(
        lifecycle_config_for(result.platform), engine=result.engine,
        scenario=result.scenario, theta_channel=result.channel)
    got = result.lifecycle_config_digest
    if got != want:
        raise MCInputError(
            f"lifecycle_config_digest_mismatch:{layer}",
            f"{where}: trace carries {got[:12]} != digest re-derived "
            f"from the live frozen configuration {want[:12]}")
    return want


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
                # LAYER 2 of the four-layer lifecycle-config equality:
                # the container re-derives the digest from the LIVE
                # frozen modules for this result's own axes and requires
                # the trace to carry exactly it.
                _assert_config_digest(r, layer="container",
                                      where=f"{self.run_label}:{cid}")
            # N01 PHASE D2: `combo` is a DISPLAY LABEL. It is RENDERED
            # from the inner authoritative fields and compared; it is
            # never split back into platform/engine/policy (that made the
            # string the sole authority for sizing + payout path).
            for r in (cons, stress):
                want = mc_atoms.combo_label(
                    r.platform, r.engine, r.observations.sizing_policy)
                if cid != want:
                    raise MCInputError(
                        "combo_label_not_authoritative",
                        f"{self.run_label}: label {cid!r} != label "
                        f"rendered from the authoritative fields "
                        f"{want!r}")
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

    def observation_sets(self) -> dict:
        """set_key -> ObservationSet for every (combo, scenario) of this
        run. THE index the cold replay and the M certificate consume."""
        out = {}
        for cid, (cons, stress) in sorted(self.results.items()):
            for r in (cons, stress):
                out[r.observations.set_key] = r.observations
        return out

    def trace_digests(self) -> dict:
        """LEVEL-1 flat digests: one per (run_label, combo, scenario)."""
        return {k: s.observations_digest
                for k, s in sorted(self.observation_sets().items())}

    def trace_digest_of_digests(self) -> str:
        """LEVEL-2 container digest (D6 two-level flattening)."""
        return mc_atoms.digest_of_digests(self.trace_digests())


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
    """IR-29 — the M axis's convergence obligation: PROOF that the
    exhaustively enumerated start-phase support was covered completely,
    uniquely, and exactly once per phase, by every Primary combo and
    every scenario, on the SAME prepared calendar. Replaces "M doubling";
    never a pseudo-2M.

    N01 PHASE D4: this object is DERIVED, not accepted. It is built ONLY
    by `derive_support_certificate`, which reduces
    `actual_phase_keys_by_world` out of the real atom trace — world by
    world, combo by combo, scenario by scenario. The R2.3 version
    validated a CALLER-SUPPLIED support tuple against `base.M`, i.e. it
    proved a declared scalar against another declared scalar; a run that
    executed the wrong phases while reporting the right count passed.

    `trace_digests` is the witness of WHICH BYTES' execution trace the
    proof was reduced from."""
    prepared_digest: str
    support: tuple                    # the legal enumeration (authority)
    trace_digests: Mapping            # set_key -> level-1 trace digest
    trace_digest_of_digests: str      # level-2 container digest

    def __post_init__(self):
        object.__setattr__(self, "support",
                           tuple(int(i) for i in self.support))
        object.__setattr__(self, "trace_digests",
                           MappingProxyType(dict(self.trace_digests)))
        want = mc_atoms.digest_of_digests(dict(self.trace_digests))
        if self.trace_digest_of_digests != want:
            raise MCInputError(
                "m_support_trace_digest_mismatch",
                f"declared {str(self.trace_digest_of_digests)[:12]} != "
                f"recomputed {want[:12]}")


def derive_support_certificate(base: RunEvidence,
                               prepared: "PreparedMCInput"
                               ) -> ExhaustiveSupportCertificate:
    """Reduce the M exhaustive-support certificate FROM THE ATOM TRACE.

    The legal enumeration comes from the prepared authority. For EVERY
    Primary combo x scenario, and within it for EVERY world, the ACTUAL
    executed phase keys must equal that enumeration exactly once, in
    order. Every violation keeps its IR-29-pinned refusal code."""
    if base.prepared_digest != prepared_digest(prepared):
        raise MCInputError("m_support_wrong_calendar",
                           "base evidence is bound to a different "
                           "prepared input")
    legal = tuple(int(i) for i in prepared.calendar.first_month_offsets)
    if len(set(legal)) != len(legal):
        raise MCInputError("m_support_duplicate_phase",
                           f"prepared authority itself repeats: {legal}")
    sets = base.observation_sets()
    if not sets:
        raise MCInputError("m_support_execution_mismatch",
                           "no observation sets in the base run")
    for key, obs in sorted(sets.items()):
        support = tuple(obs.legal_phase_support)
        if len(set(support)) != len(support):
            raise MCInputError("m_support_duplicate_phase",
                               f"{key}: {support}")
        missing = sorted(set(legal) - set(support))
        extra = sorted(set(support) - set(legal))
        if missing:
            raise MCInputError("m_support_incomplete",
                               f"{key}: missing={missing}")
        if extra:
            raise MCInputError("m_support_extra",
                               f"{key}: extra={extra}")
        if support != legal:
            raise MCInputError(
                "m_support_order_violation",
                f"{key}: {support} != legal enumeration {legal}")
        # THE reduction from the real trace: per world, per combo, per
        # scenario — actual == legal, each phase exactly once.
        actual = obs.actual_phase_keys_by_world()
        if sorted(actual) != list(range(obs.B)):
            raise MCInputError(
                "m_support_execution_mismatch",
                f"{key}: worlds executed {sorted(actual)[:4]}... != "
                f"range({obs.B})")
        for w, phases in sorted(actual.items()):
            if tuple(sorted(phases)) != legal:
                raise MCInputError(
                    "m_support_execution_mismatch",
                    f"{key} world {w}: executed phases "
                    f"{tuple(sorted(phases))} != legal {legal}")
            if len(phases) != len(legal):
                raise MCInputError(
                    "m_support_execution_mismatch",
                    f"{key} world {w}: {len(phases)} executions != "
                    f"|support|={len(legal)}")
    if base.M != len(legal):
        raise MCInputError("m_support_execution_mismatch",
                           f"base M={base.M} != |support|={len(legal)}")
    digests = base.trace_digests()
    return ExhaustiveSupportCertificate(
        prepared_digest=base.prepared_digest, support=legal,
        trace_digests=digests,
        trace_digest_of_digests=mc_atoms.digest_of_digests(digests))


def _check_b_doubling_world_prefix(base: RunEvidence,
                                   doubled: RunEvidence) -> None:
    """D4 — CONTENT-level witness of the B-doubling relation.

    `numpy.random.SeedSequence(seed).spawn(2B)` yields child sequences
    whose first B entries are IDENTICAL to `spawn(B)` (verified against
    THIS repository's `bootstrap.build_worlds`, see
    tests/test_mc_cold_replay.py::test_seedsequence_spawn_prefix_property
    _holds_in_this_repo). A genuine double-B run therefore reuses the
    base run's worlds verbatim as its first B worlds — a re-drawn or
    re-seeded "double" cannot fake that."""
    base_sets = base.observation_sets()
    for key, dbl in sorted(doubled.observation_sets().items()):
        base_key = key.replace(f"{doubled.run_label}/",
                               f"{base.run_label}/", 1)
        b_obs = base_sets.get(base_key)
        if b_obs is None:
            raise MCInputError(
                "b_doubling_world_prefix_violation",
                f"{key}: no matching base observation set {base_key!r}")
        b_digests = b_obs.world_digests()
        d_digests = dbl.world_digests()
        if len(d_digests) < len(b_digests):
            raise MCInputError(
                "b_doubling_world_prefix_violation",
                f"{key}: doubled run has {len(d_digests)} worlds < base "
                f"{len(b_digests)}")
        for i, (a, b) in enumerate(zip(b_digests, d_digests)):
            if a != b:
                raise MCInputError(
                    "b_doubling_world_prefix_violation",
                    f"{key}: world {i} of the double-B run "
                    f"({b[:12]}) differs from the base run ({a[:12]}) — "
                    "a genuine B doubling extends the world table, it "
                    "does not redraw it")


def convergence_from_evidence(base: RunEvidence,
                              doubled_by_axis: Mapping,
                              seed_runs: Mapping, *,
                              prepared: "PreparedMCInput",
                              ) -> ConvergenceReport:
    """Compute MC SS5 rules (a)-(d) FROM run evidence. Validation order
    (so every violation surfaces with its OWN code):

    1. inner/outer binding of EVERY supplied run (RunEvidence.
       validate_inner_binding — outer metadata cannot impersonate);
    2. B-axis provenance/scale relations PLUS the CONTENT-level world
       prefix witness (`b_doubling_world_prefix_violation`);
    3. seed-run set/identity, and the FROZEN base scales (B=1000, K=200,
       base seed 7, primary theta) — a small-scale or off-seed base
       refuses with "frozen_scale_violation";
    4. M axis: doubling FORBIDDEN (IR-29a); the exhaustive-support
       certificate is DERIVED HERE from the actual atom trace — the
       caller can no longer supply one (N01 PHASE D4);
    5. K axis: REFUSED — grid replay is BLOCKED (missing per-day
       DAY_STRATA), so no ACTUAL K-doubled evidence can exist; outer
       metadata may not impersonate it.

    Production convergence is therefore STRUCTURALLY UNSATISFIABLE until
    the GRID-B supplement executes — the honest fail-closed state."""
    if base.axis != "base":
        raise MCInputError("axis_identity_mismatch",
                           f"base run carries axis={base.axis!r}")
    if not isinstance(prepared, PreparedMCInput):
        raise MCInputError(
            "prepared_authority_missing",
            "convergence needs the prepared input: the M support "
            "certificate is DERIVED from its legal enumeration and the "
            "actual trace, never accepted from a caller")
    base.validate_inner_binding()
    # (1) inner/outer binding + B-axis relations for every SUPPLIED run —
    # a tampered outer number surfaces its own code before anything else.
    for axis in sorted(doubled_by_axis):
        run = doubled_by_axis[axis]
        run.validate_inner_binding()
        if axis == "B":
            _check_run_provenance(base, run, "B")
            _check_b_doubling_world_prefix(base, run)
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
            "IR-29: M is exempt from doubling — its obligation is the "
            "DERIVED ExhaustiveSupportCertificate")
    # N01 PHASE D4: DERIVED from the actual atom trace. There is no
    # caller-supplied certificate parameter any more, so a hand-built
    # "complete support" object has no callable path into convergence.
    derive_support_certificate(base, prepared)
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
    # N01 fix D-4: this arm was an AssertionError, which is only correct
    # while DOUBLING_AXES permanently contains "K". The moment the K axis
    # is unblocked (GRID-B supplement sealed + KReplayEvidence wired),
    # this path becomes reachable and an AssertionError would escape the
    # fail-closed vocabulary entirely — it is not an MCInputError, so no
    # caller's refusal handling would catch it and it carries no machine-
    # readable code. It is now a normal fail-closed refusal.
    raise MCInputError(
        "convergence_unreachable_state",
        "every legal axes-set carries a K entry and must refuse above "
        f"until the GRID-B supplement executes; reaching here means "
        f"DOUBLING_AXES={sorted(DOUBLING_AXES)} no longer implies a K "
        "refusal and the rule (a)-(d) computation below has not been "
        "wired yet — no verdict may be produced from this state")


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


# ---------------------------------------------------------------------------
# Cold replay (N01 PHASE D3): the seal gate re-executes EVERYTHING from a
# cold start, every call. No serialisable caller conclusion exists.
# ---------------------------------------------------------------------------

def prepared_identity_bytes(prepared: PreparedMCInput) -> bytes:
    """The PINNED prepared bytes the cold replay starts from: the exact
    canonical preimage `prepared_digest` hashes. Re-deriving the digest
    from these bytes is what makes the replay "cold" rather than a reuse
    of the in-memory object's claim about itself.

    The preimage construction is DELIBERATELY written out a second time
    rather than shared with `prepared_digest`: if the two ever drift,
    `cold_replay_observation_set` refuses with
    `prepared_identity_bytes_unstable` instead of both sides agreeing on
    a silently changed identity."""
    ident = {
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "k_per_seed": prepared.k_per_seed,
        "method_digest": prepared.method_digest,
        "day_sequences": {ch: list(seq) for ch, seq in
                          sorted(prepared.day_sequences.items())},
        "traded_day_sets": {ch: sorted(days) for ch, days in
                            sorted(prepared.traded_day_sets.items())},
        "calendar_days": [[d.day_id, d.cal_offset]
                          for d in prepared.calendar.days],
        "first_month_offsets": list(prepared.calendar.first_month_offsets),
        "authorization_snapshot": _unfreeze(
            prepared.authorization_snapshot),
    }
    return json.dumps(ident, sort_keys=True).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ReplaySpec:
    """The COMPLETE cold-start specification of ONE observation set. It
    carries no statistic and no conclusion — only what is needed to
    re-execute the run from scratch."""
    run_label: str
    platform: str
    engine: str
    scenario: str
    theta_channel: str
    B: int
    master_seed: int
    prepared_digest: str
    lifecycle_config_digest: str
    rng_spec: str
    method_version: str

    @staticmethod
    def from_observations(obs: ObservationSet) -> "ReplaySpec":
        return ReplaySpec(
            run_label=obs.run_label, platform=obs.platform,
            engine=obs.engine, scenario=obs.scenario,
            theta_channel=obs.theta_channel, B=obs.B,
            master_seed=obs.master_seed,
            prepared_digest=obs.prepared_digest,
            lifecycle_config_digest=obs.lifecycle_config_digest,
            rng_spec=mc_atoms.RNG_SPEC,
            method_version=mc_atoms.METHOD_VERSION)


def cold_replay_observation_set(prepared: PreparedMCInput,
                                spec: ReplaySpec) -> ObservationSet:
    """Re-execute ONE observation set from a COLD START.

    Cold start = the identity is re-derived from the PINNED prepared
    bytes, the config digest is re-derived from the LIVE frozen modules,
    the RNG spec and method version are re-checked, the world table is
    rebuilt from (prepared, seed, B, block, length), and every lifecycle
    is run again. Nothing from the forward run is reused."""
    if type(spec) is not ReplaySpec:
        raise MCInputError("cold_replay_spec_invalid",
                           f"{type(spec).__name__} is not a ReplaySpec")
    cold_digest = hashlib.sha256(
        prepared_identity_bytes(prepared)).hexdigest()
    if cold_digest != prepared_digest(prepared):
        raise MCInputError(
            "prepared_identity_bytes_unstable",
            "the pinned prepared bytes do not reproduce the prepared "
            "digest — the cold-start preimage and the live digest have "
            "diverged")
    if spec.prepared_digest != cold_digest:
        raise MCInputError(
            "cold_replay_prepared_binding_mismatch",
            f"spec {spec.prepared_digest[:12]} != cold-derived "
            f"{cold_digest[:12]}")
    if spec.rng_spec != mc_atoms.RNG_SPEC:
        raise MCInputError("cold_replay_rng_spec_mismatch",
                           "the randomness specification moved")
    if spec.method_version != mc_atoms.METHOD_VERSION:
        raise MCInputError("cold_replay_method_version_mismatch",
                           f"{spec.method_version!r} != "
                           f"{mc_atoms.METHOD_VERSION!r}")
    want_cfg = mc_atoms.lifecycle_config_digest_for(
        lifecycle_config_for(spec.platform), engine=spec.engine,
        scenario=spec.scenario, theta_channel=spec.theta_channel)
    if spec.lifecycle_config_digest != want_cfg:
        raise MCInputError(
            "lifecycle_config_digest_mismatch:cold_replay",
            f"{spec.run_label}: spec carries "
            f"{spec.lifecycle_config_digest[:12]} != live "
            f"{want_cfg[:12]}")
    return run_observation_set(
        prepared, run_label=spec.run_label, platform=spec.platform,
        engine=spec.engine, scenario=spec.scenario,
        channel=spec.theta_channel, B=spec.B,
        master_seed=spec.master_seed)


def compare_atom_tables(produced: ObservationSet,
                        replayed: ObservationSet) -> dict:
    """Two-sided comparison of a forward run against its cold replay.

    Compares (a) the COMPLETE Cartesian key set and (b) the PER-ATOM
    canonical digest, and returns both digest tables plus the mismatch
    list. It never raises on divergence — the caller refuses; this
    function exists so the evidence of divergence is inspectable."""
    left = produced.atom_digest_table()
    right = replayed.atom_digest_table()
    mismatches = []
    for key in sorted(set(left) - set(right)):
        mismatches.append({"key": list(key), "kind": "missing_in_replay",
                           "produced": left[key], "replayed": None})
    for key in sorted(set(right) - set(left)):
        mismatches.append({"key": list(key), "kind": "extra_in_replay",
                           "produced": None, "replayed": right[key]})
    for key in sorted(set(left) & set(right)):
        if left[key] != right[key]:
            mismatches.append({"key": list(key), "kind": "digest_differs",
                               "produced": left[key],
                               "replayed": right[key]})
    return {
        "set_key": produced.set_key,
        "key_set_equal": set(left) == set(right),
        "produced_set_digest": produced.observations_digest,
        "replayed_set_digest": replayed.observations_digest,
        "produced_atom_digests": {f"{w}:{p}": d
                                  for (w, p), d in sorted(left.items())},
        "replayed_atom_digests": {f"{w}:{p}": d
                                  for (w, p), d in sorted(right.items())},
        "mismatches": mismatches,
    }


def _dual_reducer_check(observations: ObservationSet) -> dict:
    """Run BOTH reducers over the same trace and refuse any disagreement.

    Production side: the in-type reducer (`_epistemic_derived` +
    `feasibility_counts`, which recompute from live atoms).
    Independent side: `itsf.mc.cold_reducer`, which starts from the
    SERIALISED canonical JSONL and shares no helper with production
    (import-graph pinned in tests)."""
    hot = _epistemic_derived(observations)
    hot_feas = observations.feasibility_counts()
    try:
        cold = mc_cold.reduce_trace(observations.to_jsonl())
    except mc_cold.ColdReducerError as exc:
        raise MCInputError("reducer_disagreement",
                           f"{observations.set_key}: independent reducer "
                           f"refused the sealed trace ({exc})") from exc
    disagreements = []
    for name in ("world_means", "within_world_ses", "p5", "median",
                 "p95", "between_world_sd", "max_within_world_se"):
        if hot[name] != cold[name]:
            disagreements.append(f"{name}: {hot[name]!r} != {cold[name]!r}")
    if cold["observations_digest"] != observations.observations_digest:
        disagreements.append(
            f"observations_digest: "
            f"{observations.observations_digest[:12]} != "
            f"{cold['observations_digest'][:12]}")
    for name, value in sorted(hot_feas.items()):
        other = cold["feasibility"].get(name, "<absent>")
        if isinstance(value, mc_atoms.AbsentQuantity):
            value = value.token
        if value != other:
            disagreements.append(f"feasibility.{name}: {value!r} != "
                                 f"{other!r}")
    if observations.actual_phase_keys_by_world() != \
            cold["actual_phase_keys_by_world"]:
        disagreements.append("actual_phase_keys_by_world")
    if disagreements:
        raise MCInputError(
            "reducer_disagreement",
            f"{observations.set_key}: {disagreements[:3]}")
    return cold


def cold_replay_evidence(prepared: PreparedMCInput,
                         runs: Sequence[RunEvidence]) -> dict:
    """Cold-replay EVERY observation set of EVERY supplied run and refuse
    on ANY divergence. Returns the AUDIT DESCRIPTION (two-sided digest
    tables + mismatch lists).

    The returned mapping is a receipt in the strict sense: it DESCRIBES
    what happened. It is not accepted back as an input anywhere — there
    is no parameter on this module's seal entry that takes one, so a
    receipt rewritten to be "all green" cannot skip a single replay."""
    legal = tuple(prepared.calendar.first_month_offsets)
    comparisons = {}
    config_digests = {}
    for run in runs:
        for key, obs in sorted(run.observation_sets().items()):
            # D4: the legal start-phase support is the PREPARED
            # authority's, never the trace's own claim.
            if tuple(obs.legal_phase_support) != legal:
                raise MCInputError(
                    "legal_phase_support_not_from_prepared",
                    f"{key}: trace claims {tuple(obs.legal_phase_support)}"
                    f" but the prepared calendar enumerates {legal}")
            spec = ReplaySpec.from_observations(obs)
            replayed = cold_replay_observation_set(prepared, spec)
            cmp = compare_atom_tables(obs, replayed)
            if not cmp["key_set_equal"] or cmp["mismatches"]:
                raise MCInputError(
                    "cold_replay_divergence",
                    f"{key}: key_set_equal={cmp['key_set_equal']} "
                    f"mismatches={cmp['mismatches'][:2]}")
            _dual_reducer_check(obs)
            _dual_reducer_check(replayed)
            comparisons[key] = cmp
            config_digests[key] = obs.lifecycle_config_digest
    return {
        "schema": "mc_cold_replay_receipt.v1",
        "replay_algo_version": mc_atoms.REPLAY_ALGO_VERSION,
        "cold_reducer_version": mc_cold.COLD_REDUCER_VERSION,
        "rng_spec": mc_atoms.RNG_SPEC,
        "method_version": mc_atoms.METHOD_VERSION,
        "prepared_digest": prepared_digest(prepared),
        "prepared_identity_bytes_sha256": hashlib.sha256(
            prepared_identity_bytes(prepared)).hexdigest(),
        "legal_phase_support": list(legal),
        "lifecycle_config_digests": config_digests,
        "n_sets_replayed": len(comparisons),
        "comparisons": comparisons,
    }


def verdict_and_seal_from_evidence(prepared: PreparedMCInput, *,
                                   base: RunEvidence,
                                   doubled_by_axis: Mapping,
                                   seed_runs: Mapping) -> dict:
    """The ONLY path to a Checkpoint-0 verdict AND its seal candidate.

    N01 PHASE D3 — EVERY call, unconditionally:
      1. cold-starts from the PINNED prepared bytes + the full lifecycle
         config preimage + the RNG spec + the method version;
      2. INDEPENDENTLY replays every lifecycle of every supplied run;
      3. compares the COMPLETE Cartesian key set;
      4. compares the PER-ATOM canonical digest;
      5. produces two-sided digest tables and a mismatch list;
      6. refuses to seal (`cold_replay_divergence`) on any mismatch;
      7. runs BOTH reducers over both traces and refuses any
         disagreement (`reducer_disagreement`).

    This doubles the computation (see the node receipt for the magnitude)
    and that is the price of the guarantee. There is NO parameter that
    accepts a prior receipt, a `match=True`, or any other caller
    conclusion: the replay cannot be skipped.

    Structurally unreachable today: the reduction refuses at the
    feasibility gate (DECISION_REQUIRED), convergence refuses at K —
    every refusal is the honest missing decision, not a gap."""
    from itsf.mc.verdict import apply_verdict
    if base.prepared_digest != prepared_digest(prepared):
        raise MCInputError("provenance_mismatch",
                           "base evidence was not computed from THIS "
                           "prepared input")
    digest_before = prepared_digest(prepared)
    base.validate_inner_binding()
    runs = [base]
    for _axis, run in sorted(doubled_by_axis.items()):
        run.validate_inner_binding()
        runs.append(run)
    for _seed, run in sorted(seed_runs.items()):
        run.validate_inner_binding()
        runs.append(run)
    # (1)-(7) UNCONDITIONAL cold replay, before anything is reduced.
    replay_receipt = cold_replay_evidence(prepared, runs)
    # LAYER 4 of the four-layer config equality: the seal boundary.
    for run in runs:
        for _cid, (cons, stress) in sorted(run.results.items()):
            for r in (cons, stress):
                _assert_config_digest(r, layer="seal",
                                      where=f"{run.run_label}:{r.platform}"
                                            f"/{r.engine}/{r.scenario}")
    reduction = _reduce_primary_from_base(base)
    convergence_from_evidence(base, doubled_by_axis, seed_runs,
                              prepared=prepared)
    verdict = apply_verdict(dict(reduction))
    digest_after = prepared_digest(prepared)
    if digest_before != digest_after:
        raise MCInputError("prepared_digest_instability",
                           f"{digest_before[:12]} -> {digest_after[:12]}")
    return {
        "schema": "mc_verdict_inputs.v4",
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "method_digest": prepared.method_digest,
        "method_version": mc_atoms.METHOD_VERSION,
        "prepared_digest": digest_before,
        "primary_theta_channel": PRIMARY_THETA_CHANNEL,
        "bundle_file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "trace_digests": base.trace_digests(),
        "trace_digest_of_digests": base.trace_digest_of_digests(),
        "cold_replay_receipt": replay_receipt,
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
