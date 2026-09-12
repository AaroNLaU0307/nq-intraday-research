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
lets the COMPUTATION read a repository path after the prepared input is
built (exposure freeze: the epistemic / aleatoric drivers and the replay
consume ONLY the immutable prepared object; the sole post-prepare read is
B-PROV's re-verification of the blind attestation at the seal boundary,
which is custody metadata carrying zero research values), and
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
# The PUBLISHED §10.1 record contract. Imported rather than restated: S0
# owns what a sealed handoff line is called, and this module reads those
# lines. Names only -- no S0 computation is reached from here.
from itsf.s0.report import FORMAL_RECORD_FIELDS, _TS_RENAME
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

# The eight per-(engine, scenario) atomic-record files. These are the ONLY
# bundle members whose RAW BYTES the prepared input retains (N01 C1): they
# are the numerical authority every lifecycle consumes, so the replay must
# be able to re-parse them from custody-checked bytes rather than trusting
# a live mapping. The other six members are consumed ONCE during the
# battery (governance, seeds, counts, day universes) and are NOT retained —
# S0_REPORT.json alone is 349 MB against ~92 MB for all eight handoff
# files, and its content is already pinned by `file_sha256` inside the
# prepared identity, so retaining it would multiply the footprint ~4.8x to
# re-prove something the digest already proves.
HANDOFF_FILES = tuple(f"MC_HANDOFF_{e}_{s}.jsonl"
                      for e in ENGINES for s in SCENARIOS)
HANDOFF_FILE_SET = frozenset(HANDOFF_FILES)

# The sealed-bundle exact set (S0-T001 layout; runner-side custody files
# included — the consumer re-derives day universes and governance identity
# from the SAME bytes the S0 seal proved).
BUNDLE_EXACT_SET = frozenset(
    list(HANDOFF_FILES)
    + ["S0_REPORT.json", "S0_REPORT.md", "HANDOFF_ADMISSION.json",
       "SEED_MANIFEST.json", "REGISTRY_AFTER_RUN_STARTED.json",
       "manifest.jsonl"])

#: S0's `infrastructure_files`: written by the RUN INFRASTRUCTURE, not by the
#: renderer. `s0/output_proof.py` says they "must not appear in
#: `sealed_files`", and the real run declares exactly these two
#: (`scripts/s0_real_run.py`, the `prove_governance(...)` call site).
#:
#: WHY THIS EXISTS, measured 2026-09-05 on the first real N09 attempt. The
#: coverage loop below used to exempt only `manifest.jsonl`, so it demanded a
#: sealed-manifest digest for a file S0 had deliberately kept out of that
#: manifest -- two ratified classifications contradicting each other over one
#: file, and the real bundle refused with `bundle_manifest_coverage`. It had
#: never surfaced because every synthetic bundle in the suite builds its
#: manifest over ALL non-manifest files, which is MORE complete than what S0
#: actually seals.
#:
#: THE EXEMPTION IS NARROW, and none of the protection is lost:
#:   present    -- still required, by `BUNDLE_EXACT_SET` above and by the
#:                 external key-set check (`custody_authority_keyset_violation`)
#:   authentic  -- still digest-checked, by the EXTERNAL custody attestation,
#:                 whose key set must EQUAL `BUNDLE_EXACT_SET`; a missing,
#:                 extra, malformed or mismatched entry all refuse. That source
#:                 lives outside the bundle under review, so it is the stronger
#:                 of the two, and it is already the ONLY digest source for
#:                 `manifest.jsonl` today.
#:   well-formed-- still parsed and cross-checked below: valid JSON, and its
#:                 `snapshot_before` must agree with the authorization
#:                 snapshot, the custody authority, and `S0_REPORT.json`.
#: What is dropped is one redundant digest from a source that was never going
#: to carry it.
S0_INFRASTRUCTURE_FILES = frozenset({"manifest.jsonl",
                                     "REGISTRY_AFTER_RUN_STARTED.json"})

_RECORD_FIELDS = tuple(TradePathRecord.__dataclass_fields__)  # 19 fields

#: The two spellings of one record, and which side of the seal each lives on.
#: INTERNAL (`_RECORD_FIELDS`, the dataclass) is what this module carries in
#: `FrozenTradePath`, in `_record_canonical_row` and in the records custody
#: digest. PUBLISHED (`FORMAL_RECORD_FIELDS`, from `s0.report`) is what a
#: sealed `MC_HANDOFF_*` line actually holds. They differ in exactly two
#: names; `record_to_formal_dict` states that "every other field keeps its
#: internal name", and 17 of 19 are verbatim identical -- measured, not
#: assumed.
#:
#: TAKEN FROM S0, NOT RESTATED. A second hand-written map is a second thing
#: to keep in agreement, and this repository has paid for that shape before.
_PUBLISHED_TO_INTERNAL = {v: k for k, v in _TS_RENAME.items()}
_HEX64_RE = re.compile(r"^[0-9a-f]{64}\Z")
RECORDS_DIGEST_SCHEMA = "mc_records_custody.v1"


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


def _record_canonical_row(rec, *, where: str) -> dict:
    """Canonical JSON-shaped mapping of ONE atomic record, over the
    COMPLETE frozen field set.

    The field names are enumerated MECHANICALLY from the contracts
    dataclass (`_RECORD_FIELDS`), never spelled here — a field lane S0
    adds enters the custody digest automatically, and this module still
    names no diagnostic field. Presence in an IDENTITY digest is not
    consumption: nothing downstream reads these values, they only make a
    substituted record impossible to hide."""
    row = {}
    for name in _RECORD_FIELDS:
        try:
            value = getattr(rec, name)
        except AttributeError as exc:
            raise MCInputError(
                "records_custody_row_malformed",
                f"{where}: record has no field {name!r} — it is not a "
                "TradePathRecord-shaped row") from exc
        row[name] = mc_atoms.jsonable(value)
    return row


def records_canonical_digest(records: Mapping) -> str:
    """Deterministic digest over the COMPLETE parsed record set: every
    (engine, scenario) file, every trade date, every field.

    This is the link the R2.3 identity was missing. `prepared_digest`
    covered the bundle FILE digests but nothing about the PARSED records,
    so a `PreparedMCInput` whose identity fields were copied verbatim
    while its `records` mapping was swapped produced a bit-identical
    digest, and the forged trace replayed green (the replay consumed the
    same live object). Content now enters the identity.

    The rows are STREAMED into the hash (one canonical JSON object per
    row, newline separated — the same discipline as the atom trace's
    JSONL) rather than materialised into a list: at production scale the
    eight handoff files are ~92 MB of source and a materialised preimage
    would double the transient footprint for no added strength. Canonical
    JSON is ASCII with no raw newline, so the separator is unambiguous."""
    if not isinstance(records, Mapping):
        raise MCInputError("records_custody_shape",
                           f"{type(records).__name__} is not a mapping")
    for key in records:
        if not (isinstance(key, tuple) and len(key) == 2):
            raise MCInputError("records_custody_shape",
                               f"record key {key!r} is not "
                               "(engine, scenario)")
    digest = hashlib.sha256()
    digest.update(mc_atoms.canonical_json(
        {"schema": RECORDS_DIGEST_SCHEMA,
         "fields": list(_RECORD_FIELDS)}).encode("utf-8"))
    for key in sorted(records, key=lambda k: (str(k[0]), str(k[1]))):
        rows = records[key]
        if not isinstance(rows, Mapping):
            raise MCInputError(
                "records_custody_shape",
                f"{key[0]}|{key[1]} is not a date->record mapping")
        engine, scenario = str(key[0]), str(key[1])
        for date in sorted(rows):
            digest.update(b"\n")
            digest.update(mc_atoms.canonical_json({
                "engine": engine, "scenario": scenario,
                "trade_date": str(date),
                "record": _record_canonical_row(
                    rows[date],
                    where=f"{engine}|{scenario}:{date}"),
            }).encode("utf-8"))
    return digest.hexdigest()


def records_key_index(records: Mapping) -> dict:
    """The COMPLETE engine/scenario/date key set, canonically ordered.

    Carried in the identity preimage ALONGSIDE the content digest: a
    dropped or added trade date is then visible as a key-set change even
    to a reader who never recomputes the content digest."""
    out = {}
    for key in sorted(records, key=lambda k: (str(k[0]), str(k[1]))):
        out[f"{key[0]}|{key[1]}"] = sorted(str(d) for d in records[key])
    return out


def _parse_handoff_file(raw: bytes, *, name: str, engine: str,
                        scenario: str) -> Mapping:
    """Parse ONE MC_HANDOFF_* blob into {trade_date -> FrozenTradePath}.

    THE single parser. `_prepare_mc_input_impl` and the cold replay both
    reach the records through it, so the forward run and the replay can
    only disagree about records if the BYTES disagree."""
    if not isinstance(raw, (bytes, bytearray)):
        raise MCInputError("records_custody_source_not_bytes",
                           f"{name}: {type(raw).__name__}")
    rows: dict = {}
    for i, line in enumerate(bytes(raw).decode("utf-8").splitlines()):
        if not line.strip():
            continue
        rec = _parse_record(json.loads(line), name, i)
        if rec.engine != engine or rec.cost_scenario != scenario:
            raise MCInputError("axis_violation",
                               f"{name}:{i} carries "
                               f"{rec.engine}/{rec.cost_scenario}")
        if rec.trade_date in rows:
            raise MCInputError("duplicate_record_date",
                               f"{name}:{rec.trade_date}")
        rows[rec.trade_date] = rec           # FrozenTradePath (deep)
    return MappingProxyType(rows)


def records_from_handoff_bytes(handoff_bytes: Mapping) -> Mapping:
    """Re-parse the COMPLETE record set from custody-held raw bytes.

    The bytes are the authority. Nothing here reads a live mapping, a
    forward observation, or any caller-declared snapshot."""
    if not isinstance(handoff_bytes, Mapping):
        raise MCInputError("records_custody_shape",
                           f"{type(handoff_bytes).__name__} is not a "
                           "mapping of handoff bytes")
    names = set(handoff_bytes)
    if names != HANDOFF_FILE_SET:
        raise MCInputError(
            "records_custody_source_keyset",
            f"missing={sorted(HANDOFF_FILE_SET - names)} "
            f"extra={sorted(names - HANDOFF_FILE_SET)}")
    out: dict = {}
    for e in ENGINES:
        for s in SCENARIOS:
            name = f"MC_HANDOFF_{e}_{s}.jsonl"
            out[(e, s)] = _parse_handoff_file(handoff_bytes[name],
                                              name=name, engine=e,
                                              scenario=s)
    return MappingProxyType(out)


@dataclass(frozen=True, slots=True)
class PreparedMCInput:
    """Run-scoped immutable MC input (source matrix R13/R14).

    Built ONCE by `prepare_mc_input` from bundle BYTES; the epistemic /
    aleatoric drivers consume ONLY this object — they carry no paths, no
    handles, no registry access (exposure freeze by construction).

    N01 C1 — RECORDS CUSTODY. The object retains the CUSTODY-CHECKED RAW
    BYTES of the eight MC_HANDOFF_* files, and `records` is DERIVED from
    them inside `__post_init__`, every single time an instance is built.
    There is no construction path that installs a caller's record mapping:
    a supplied one is declare-and-verify (it must reproduce the bytes'
    canonical digest) and is then REPLACED by the bytes-derived mapping.
    The numerical authority is therefore the bytes, not any live object,
    and the identity digest covers the parsed content.

    B-PROV — CUSTODY PROVENANCE. The object also retains the three facts
    that say WHICH authority certified it (`source_artifact_id`,
    `source_artifact_sha256`, `test_only`), and `prepared_digest` binds
    them. Before this they were consumed by the battery and dropped: a
    TEST_ONLY_SYNTHETIC authority's product and the code-pinned
    production attestation's product were indistinguishable objects with
    identical identities, so the seal had nothing to check. They are
    MANDATORY fields — a prepared input with no declared provenance is
    not constructible, which is what closes the hand-assembled path.

    THE FACTORY BOUNDARY (this round). B-PROV made the custody ROOT
    decisive but left the object's ORIGIN undecided: every field above
    is a public constructor parameter, so a caller who supplies a
    provenance triple and a digest table consistent with the attestation
    obtains a seal-admissible object the ten-check battery never touched
    — and may then choose `method_digest`, `seeds`, `k_per_seed`,
    `day_sequences`, `traded_day_sets`, `calendar` and
    `authorization_snapshot` freely, because nothing downstream
    re-derives them. `battery_receipt` closes that: it is NOT an init
    parameter, it can only be minted by the battery, and it BINDS the
    prepared identity, so `PreparedMCInput(...)` and
    `dataclasses.replace(prepared, ...)` both yield objects the seal
    refuses. Construction itself stays public and unchanged — the
    ten-check battery's refusal codes are still reachable by tests, and
    the cold replay still rebuilds a prepared input from custody bytes;
    what is no longer reachable is SEAL ADMISSIBILITY without the
    battery."""
    trial_id: str
    authorized_commit: str
    file_sha256: Mapping             # name -> hex digest (exact set)
    handoff_bytes: Mapping           # name -> RAW custody-checked bytes
    day_sequences: Mapping           # channel -> ordered tuple of dates
    traded_day_sets: Mapping         # channel -> frozenset of dates
    seeds: tuple
    k_per_seed: int
    method_digest: str               # sha256 over frozen method sources
    authorization_snapshot: Mapping  # injected at build; deeply frozen
    calendar: TemplateCalendar
    # B-PROV: the certifying authority's OWN provenance, carried through.
    # `source_artifact_id` is an IDENTIFIER, never a handle — nothing in
    # this module opens it; the seal compares it against the code pin.
    source_artifact_id: str
    source_artifact_sha256: str
    test_only: bool
    # DERIVED, never authoritative-from-the-caller. `None` is the normal
    # value at construction; anything else is declare-and-verify.
    records: Mapping | None = None   # (engine, scenario) -> {date: record}
    records_digest: str | None = None
    # NOT an init parameter and never a caller's to supply: the ONLY
    # writer is `_issue_battery_receipt`, which the completed battery
    # calls on its own product. `dataclasses.replace` skips init=False
    # fields, so a replaced object is receipt-LESS by construction — a
    # no-op replace included.
    #
    # `default_factory`, not a plain default, is REQUIRED here: with
    # `slots=True` the dataclass machinery deletes class-level defaults,
    # and an `init=False` field with a plain default is read from
    # exactly that deleted class attribute — the combination leaves the
    # slot unset and every access raises AttributeError.
    battery_receipt: "BatteryReceipt | None" = _dc.field(
        init=False, repr=False, compare=False, default_factory=lambda: None)

    def __post_init__(self):
        # --- custody link 0a (B-PROV): the provenance triple is well
        # formed. A malformed claim is a refusal, not a coerced value.
        if type(self.test_only) is not bool:
            raise MCInputError(
                "prepared_provenance_malformed",
                f"test_only carries {type(self.test_only).__name__} — the "
                "custody provenance must be an explicit bool")
        if not isinstance(self.source_artifact_id, str) or \
                not self.source_artifact_id:
            raise MCInputError(
                "prepared_provenance_malformed",
                f"source_artifact_id={self.source_artifact_id!r}")
        if not isinstance(self.source_artifact_sha256, str) or \
                not _HEX64_RE.match(self.source_artifact_sha256):
            raise MCInputError(
                "prepared_provenance_malformed",
                f"source_artifact_sha256={self.source_artifact_sha256!r}")
        # --- custody link 1: raw bytes -> the pinned per-file digests ---
        if not isinstance(self.file_sha256, Mapping):
            raise MCInputError("custody_authority_missing",
                               "file_sha256 is not a mapping")
        # --- custody link 0b (B-PROV): the identity must pin the COMPLETE
        # sealed bundle, not just the eight files whose bytes are kept.
        # The loop below only walks HANDOFF_FILE_SET, so an identity
        # covering 8 of the 14 exact-set members used to be legal — and
        # the seal's `bundle_file_sha256` table inherited the hole.
        if set(self.file_sha256) != BUNDLE_EXACT_SET:
            raise MCInputError(
                "prepared_bundle_coverage_violation",
                f"missing={sorted(BUNDLE_EXACT_SET - set(self.file_sha256))} "
                f"extra={sorted(set(self.file_sha256) - BUNDLE_EXACT_SET)}")
        if not isinstance(self.handoff_bytes, Mapping):
            raise MCInputError("records_custody_shape",
                               "handoff_bytes is not a mapping")
        names = set(self.handoff_bytes)
        if names != HANDOFF_FILE_SET:
            raise MCInputError(
                "records_custody_source_keyset",
                f"missing={sorted(HANDOFF_FILE_SET - names)} "
                f"extra={sorted(names - HANDOFF_FILE_SET)}")
        held = {}
        for name in sorted(names):
            raw = self.handoff_bytes[name]
            if not isinstance(raw, (bytes, bytearray)):
                raise MCInputError("records_custody_source_not_bytes",
                                   f"{name}: {type(raw).__name__}")
            raw = bytes(raw)                      # immutable copy
            got = hashlib.sha256(raw).hexdigest()
            want = self.file_sha256.get(name)
            if not isinstance(want, str) or not _HEX64_RE.match(want):
                raise MCInputError(
                    "records_custody_bytes_unpinned",
                    f"{name}: file_sha256 carries {want!r} — the records "
                    "source bytes are not pinned by the identity")
            if got != want:
                raise MCInputError(
                    "records_custody_bytes_mismatch",
                    f"{name}: retained bytes hash {got[:12]} != pinned "
                    f"{want[:12]} — the record source is not the file the "
                    "custody battery certified")
            held[name] = raw
        object.__setattr__(self, "handoff_bytes", MappingProxyType(held))

        # --- custody link 2: those bytes -> the parsed record content ---
        derived = records_from_handoff_bytes(self.handoff_bytes)
        derived_digest = records_canonical_digest(derived)
        if self.records is not None:
            # declare-and-verify: a caller MAY hand over the mapping it
            # parsed, but only if it is the SAME content the custody
            # bytes yield. The R2.3 attack (identity fields copied,
            # records swapped) dies exactly here.
            got_digest = records_canonical_digest(self.records)
            if got_digest != derived_digest:
                raise MCInputError(
                    "records_custody_content_mismatch",
                    f"supplied records digest {got_digest[:12]} != "
                    f"{derived_digest[:12]} re-parsed from the "
                    "custody-checked handoff bytes")
        if self.records_digest is not None and \
                self.records_digest != derived_digest:
            raise MCInputError(
                "records_custody_digest_mismatch",
                f"declared records_digest "
                f"{str(self.records_digest)[:12]} != "
                f"{derived_digest[:12]} re-derived from the bytes")
        # the LIFECYCLE reads the bytes-derived mapping, never a caller's
        object.__setattr__(self, "records", derived)
        object.__setattr__(self, "records_digest", derived_digest)


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
    dates/offsets produce different digests.

    N01 C1: the preimage now also binds the RECORDS — their canonical
    full-field content digest and the complete engine/scenario/date key
    index — on top of the raw handoff FILE digests already carried by
    `file_sha256`. Before this, two prepared inputs that disagreed about
    every number the lifecycles consume could share one identity.

    B-PROV: and the CUSTODY PROVENANCE. Before this, the same synthetic
    bundle certified by a TEST_ONLY_SYNTHETIC authority and by the
    code-pinned production attestation produced the SAME digest, so no
    downstream check — including the cold replay, which re-derives the
    identity from the preimage bytes — could see the difference."""
    ident = {
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "file_sha256": dict(prepared.file_sha256),
        "records_digest": prepared.records_digest,
        "record_keys": records_key_index(prepared.records),
        "seeds": list(prepared.seeds),
        "k_per_seed": prepared.k_per_seed,
        "method_digest": prepared.method_digest,
        # B-PROV. Spelled out literally here AND in
        # `prepared_identity_bytes` — see that function's docstring for
        # why the two preimages are deliberately not shared.
        "provenance": {
            "source_artifact_id": prepared.source_artifact_id,
            "source_artifact_sha256": prepared.source_artifact_sha256,
            "test_only": prepared.test_only},
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
# THE FACTORY BOUNDARY: a typed, unforgeable BATTERY RECEIPT
#
# The question B-PROV could not answer. `_assert_seal_provenance` proves
# WHICH custody authority a prepared input claims, and re-derives that
# authority from code pins so the claim cannot be a copied string. It
# does not — and with a public dataclass constructor cannot — prove that
# the object in front of it is the OUTPUT of `_prepare_mc_input_impl`.
# Given a bundle and an attestation that agree (the production case, and
# any production-LIKE test case), a caller could hand-assemble a prepared
# input, or `dataclasses.replace` a genuine one, choose the
# battery-DERIVED fields at will, and be stopped only by the UNRELATED
# feasibility gate. "Stopped by an unrelated gate" is not a refusal.
#
# What a receipt has to be, to be worth anything:
#   (a) UNFORGEABLE — not a caller-supplied boolean or string. Minting
#       one requires a module-private capability that no instance
#       retains, so holding a genuine receipt does not let a caller make
#       a second one;
#   (b) BOUND — it carries the digests of every battery-derived
#       component AND the prepared identity, so a receipt lifted off a
#       genuine object and grafted onto a mutated one fails to verify;
#   (c) NON-DECLARABLE THROUGH `__init__` — see `PreparedMCInput`'s
#       `battery_receipt` field: `init=False` means neither the public
#       constructor nor `dataclasses.replace` can carry one across.
# ---------------------------------------------------------------------------

BATTERY_RECEIPT_SCHEMA = "mc_battery_receipt.v1"
# The battery-derived components the receipt binds, each digested on its
# OWN canonical preimage. Deliberately not reduced to the single prepared
# digest (which would bind the same facts): a mismatch must be able to
# NAME the component that moved instead of reporting "identity changed".
BATTERY_RECEIPT_COMPONENTS = (
    "authorization_snapshot", "bundle_file_sha256", "calendar",
    "day_sequences", "method_digest", "provenance", "record_keys",
    "records_digest", "seeds_k_crn", "traded_day_sets", "trial_commit")


class _BatteryCapability:
    """Module-private construction capability for `BatteryReceipt`.

    ONE instance exists, created at import time, and it is passed to
    exactly one call site (`_issue_battery_receipt`). It is never stored
    on an instance — `BatteryReceipt.__post_init__` drops it the moment
    it has been checked — so a caller holding a genuine receipt cannot
    read the token back out and mint another."""
    __slots__ = ()


_BATTERY_CAPABILITY = _BatteryCapability()


def _battery_component_digests(prepared: "PreparedMCInput") -> dict:
    """Digest each battery-DERIVED component of a prepared input.

    Every field `_prepare_mc_input_impl` derives appears in exactly one
    component; `handoff_bytes` does not need one because `__post_init__`
    already pins those bytes to `file_sha256` bit for bit, and `records`
    / `records_digest` are re-derived from those same bytes on every
    construction."""
    parts = {
        "trial_commit": {"trial_id": prepared.trial_id,
                         "authorized_commit": prepared.authorized_commit},
        "provenance": {
            "source_artifact_id": prepared.source_artifact_id,
            "source_artifact_sha256": prepared.source_artifact_sha256,
            "test_only": prepared.test_only},
        "bundle_file_sha256": dict(prepared.file_sha256),
        "records_digest": prepared.records_digest,
        "record_keys": records_key_index(prepared.records),
        "method_digest": prepared.method_digest,
        "seeds_k_crn": {"seeds": list(prepared.seeds),
                        "k_per_seed": prepared.k_per_seed,
                        "crn_scope": CRN_SCOPE_FROZEN},
        "day_sequences": {ch: list(seq) for ch, seq in
                          sorted(prepared.day_sequences.items())},
        "traded_day_sets": {ch: sorted(days) for ch, days in
                            sorted(prepared.traded_day_sets.items())},
        "calendar": {
            "days": [[d.day_id, d.cal_offset]
                     for d in prepared.calendar.days],
            "first_month_offsets": list(
                prepared.calendar.first_month_offsets)},
        "authorization_snapshot": _unfreeze(
            prepared.authorization_snapshot),
    }
    if set(parts) != set(BATTERY_RECEIPT_COMPONENTS):
        raise MCInputError(
            "battery_receipt_component_set_drift",
            f"{sorted(set(parts) ^ set(BATTERY_RECEIPT_COMPONENTS))}")
    return {name: hashlib.sha256(
        json.dumps({"component": name, "value": value},
                   sort_keys=True).encode("utf-8")).hexdigest()
        for name, value in parts.items()}


@dataclass(frozen=True, slots=True)
class BatteryReceipt:
    """TYPED PROOF that the ten-check battery produced a prepared input.

    Issued ONCE, by `_issue_battery_receipt`, at the end of
    `_prepare_mc_input_impl`. It records the certifying authority's own
    identity and the digest of every battery-derived component, plus the
    prepared identity in both its forms (the digest and the sha256 of
    the pinned preimage bytes the cold replay starts from).

    It is a CERTIFICATE, not an input: nothing reads a field of it as
    permission. `verify_battery_receipt` recomputes every component from
    the live object and compares — a receipt that says "all good" over
    an object that has since changed is exactly what refuses."""
    capability: object
    schema: str
    authority_source_artifact_id: str
    authority_source_artifact_sha256: str
    authority_test_only: bool
    authority_trial_id: str
    authority_authorized_commit: str
    component_digests: Mapping
    prepared_digest: str
    prepared_identity_sha256: str

    def __post_init__(self):
        if self.capability is not _BATTERY_CAPABILITY:
            raise MCInputError(
                "battery_receipt_capability_required",
                "a battery receipt is ISSUED by the prepare battery; it "
                "cannot be constructed, copied or `dataclasses.replace`d "
                "by a caller")
        # the token never survives on an instance — see _BatteryCapability
        object.__setattr__(self, "capability", None)
        if self.schema != BATTERY_RECEIPT_SCHEMA:
            raise MCInputError("battery_receipt_malformed",
                               f"schema={self.schema!r}")
        digests = dict(self.component_digests)
        if set(digests) != set(BATTERY_RECEIPT_COMPONENTS):
            raise MCInputError(
                "battery_receipt_malformed",
                f"component set {sorted(digests)} != "
                f"{sorted(BATTERY_RECEIPT_COMPONENTS)}")
        for name, value in sorted(digests.items()):
            if not isinstance(value, str) or not _HEX64_RE.match(value):
                raise MCInputError("battery_receipt_malformed",
                                   f"component {name}={value!r}")
        for name in ("prepared_digest", "prepared_identity_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _HEX64_RE.match(value):
                raise MCInputError("battery_receipt_malformed",
                                   f"{name}={value!r}")
        if type(self.authority_test_only) is not bool:
            raise MCInputError(
                "battery_receipt_malformed",
                f"authority_test_only carries "
                f"{type(self.authority_test_only).__name__}")
        object.__setattr__(self, "component_digests",
                           MappingProxyType(digests))


def _issue_battery_receipt(prepared: "PreparedMCInput",
                           authority: "CustodyAuthority"
                           ) -> "BatteryReceipt":
    """Mint the receipt and ATTACH it. The ONLY caller is
    `_prepare_mc_input_impl`, after all ten checks have passed."""
    receipt = BatteryReceipt(
        capability=_BATTERY_CAPABILITY,
        schema=BATTERY_RECEIPT_SCHEMA,
        authority_source_artifact_id=str(authority.source_artifact_id),
        authority_source_artifact_sha256=str(
            authority.source_artifact_sha256),
        authority_test_only=bool(authority.test_only),
        authority_trial_id=str(authority.trial_id),
        authority_authorized_commit=str(authority.authorized_commit),
        component_digests=_battery_component_digests(prepared),
        prepared_digest=prepared_digest(prepared),
        prepared_identity_sha256=hashlib.sha256(
            prepared_identity_bytes(prepared)).hexdigest())
    object.__setattr__(prepared, "battery_receipt", receipt)
    return receipt


def verify_battery_receipt(prepared: "PreparedMCInput") -> "BatteryReceipt":
    """Prove the prepared input in hand IS the battery's product, and
    still carries the content the battery certified.

    Two machine-distinguishable refusals:
      `seal_prepared_not_battery_validated` — no receipt at all (the
          public constructor and `dataclasses.replace` both land here);
      `seal_battery_receipt_mismatch`       — a receipt that does not
          describe THIS object (a genuine receipt grafted onto a mutated
          one, or an object mutated after its receipt was issued).

    Every component is recomputed from the live object; the receipt is
    never consulted for a value, only compared against."""
    receipt = getattr(prepared, "battery_receipt", None)
    if type(receipt) is not BatteryReceipt:
        raise MCInputError(
            "seal_prepared_not_battery_validated",
            "the prepared input carries no battery receipt — it was not "
            "produced by the ten-check prepare battery (a hand-built "
            "object, or a `dataclasses.replace` of a genuine one)")
    if receipt.schema != BATTERY_RECEIPT_SCHEMA:
        raise MCInputError("seal_battery_receipt_mismatch",
                           f"receipt schema {receipt.schema!r}")
    live = _battery_component_digests(prepared)
    for name in BATTERY_RECEIPT_COMPONENTS:
        want = receipt.component_digests.get(name)
        if want != live[name]:
            raise MCInputError(
                "seal_battery_receipt_mismatch",
                f"the prepared input's {name} is not what the battery "
                f"certified ({str(want)[:12]} != {live[name][:12]})")
    if receipt.prepared_digest != prepared_digest(prepared):
        raise MCInputError(
            "seal_battery_receipt_mismatch",
            f"receipt binds prepared digest "
            f"{receipt.prepared_digest[:12]} != "
            f"{prepared_digest(prepared)[:12]}")
    identity_sha = hashlib.sha256(
        prepared_identity_bytes(prepared)).hexdigest()
    if receipt.prepared_identity_sha256 != identity_sha:
        raise MCInputError(
            "seal_battery_receipt_mismatch",
            f"receipt binds identity bytes "
            f"{receipt.prepared_identity_sha256[:12]} != "
            f"{identity_sha[:12]}")
    if (receipt.authority_source_artifact_id != prepared.source_artifact_id
            or receipt.authority_source_artifact_sha256
            != prepared.source_artifact_sha256
            or receipt.authority_test_only is not prepared.test_only
            or receipt.authority_trial_id != prepared.trial_id
            or receipt.authority_authorized_commit
            != prepared.authorized_commit):
        raise MCInputError(
            "seal_battery_receipt_mismatch",
            "the receipt's certifying authority is not the authority the "
            "prepared input claims")
    return receipt


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
    """One sealed `MC_HANDOFF_*` line -> `FrozenTradePath`.

    THE BOUNDARY IS A RENAME, and it is S0's, not ours. `record_to_formal_dict`
    publishes the §10.1 record under `FORMAL_RECORD_FIELDS`, where the only
    difference from the internal dataclass is `entry_ts`/`exit_ts` ->
    `entry_timestamp`/`exit_timestamp` -- "every other field keeps its
    internal name". S0 goes further and treats the internal names appearing
    on a sealed line as a LEAK ("never silently accepted as a synonym"), so
    the published names are not one of two accepted spellings; they are the
    only legal one.

    This function used to validate against the INTERNAL dataclass, which is
    the wrong side of that boundary: it demanded names S0 guarantees will
    never be there. Measured on the sealed S0-T001 bundle -- 8 files, 22736
    lines -- every line matches `FORMAL_RECORD_FIELDS` and
    `_SEALED_RECORD_FIELD_TYPES` exactly, with zero internal-name leaks. The
    values were never in question: the rename does not touch them.

    NOTHING DOWNSTREAM MOVES. `FrozenTradePath`, `_record_canonical_row` and
    the records custody digest all keep the internal names, so no custody
    digest changes. The adapter is exactly the inverse of S0's own map, taken
    FROM S0 rather than written out again here.
    """
    if not isinstance(row, dict) or set(row) != set(FORMAL_RECORD_FIELDS):
        raise MCInputError(
            "record_schema_violation",
            f"{name}:{i} field set != FORMAL_RECORD_FIELDS(19)")
    if not isinstance(row["ambiguous_stop_vs_floor"], bool):
        raise MCInputError("record_ambiguous_flag_not_bool", f"{name}:{i}")
    row = {_PUBLISHED_TO_INTERNAL.get(k, k): v for k, v in row.items()}
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
    seam). Tests use `prepare_mc_input_for_tests`.

    This is also the ONLY production route to a seal-admissible prepared
    input: the battery receipt that `verify_battery_receipt` demands is
    minted at the end of `_prepare_mc_input_impl` and nowhere else."""
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
    hex64 = re.compile(r"^[0-9a-f]{64}\Z")
    # RENDERER-produced files only. S0's infrastructure files are exempt
    # BECAUSE S0 deliberately keeps them out of this manifest; they are still
    # required present and still digest-checked externally. See
    # `S0_INFRASTRUCTURE_FILES`.
    for n in sorted(names - S0_INFRASTRUCTURE_FILES):
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

    # (4) engine/scenario/platform axis — exact. N01 C1: the records are
    # parsed from the SAME custody-checked bytes the prepared input will
    # RETAIN, through the SAME parser the cold replay re-runs.
    handoff_bytes = MappingProxyType(
        {name: bytes(bundle[name]) for name in HANDOFF_FILES})
    records = dict(records_from_handoff_bytes(handoff_bytes))
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

    # (6)+(7) date order and TP/FP disjointness per theta channel, PLUS
    # (N01 C6) the day-universe ENGINEERING EQUALITY.
    #
    # Producer-side fact (S0 §5/App A as implemented in itsf.s0.study, not
    # a method choice re-made here): `is_direction_tradeable` IS the oracle
    # candidate predicate; `_partition` splits the tradeable population
    # EXHAUSTIVELY into `y_cont >= θ` / `y_cont < θ` with no third bucket;
    # the atomic records are built for EVERY constructible day, both
    # engines, every scenario, TP and FP alike; and each θ's tp/fp lists
    # are filtered to that SAME traded set. Therefore, in any sealed
    # bundle:
    #
    #     for every θ:   set(tp) | set(fp)  ==  ref_dates       (BOTH ways)
    #     for every θ:   set(tp) & set(fp)  ==  {}
    #     across θ:      the (tp | fp) population is ONE set
    #
    # This is a completeness property the seal must satisfy, not an option.
    # A violation is a SEALED-INPUT INTEGRITY FAILURE: it refuses here, in
    # the prepare battery, before any supplement, any exposure and any
    # research output — and it never "picks another universe and carries
    # on".
    oracle = report.get("oracle_daily", {})
    day_sequences: dict = {}
    traded: dict = {}
    theta_population: dict = {}
    if not isinstance(oracle, dict) or not oracle:
        raise MCInputError("day_universe_missing", "oracle_daily absent")
    # (C6b, added 2026-08-26) WHICH channels, not just what is in them.
    #
    # The loop below took whatever key set the bundle happened to carry.
    # Measured on a LEGITIMATELY sealed bundle — manifest refreshed, custody
    # clean, so `bundle_hash_mismatch` has nothing to say — all three of
    # these passed the whole ten-check battery: the frozen primary renamed
    # to an unruled channel, the primary absent entirely, and an extra
    # unruled channel added. `traded_day_sets` then came out keyed by
    # whatever was there.
    #
    # The primary is frozen (S0 §7 L133: 主 0.5 副 0.3, no post-hoc
    # promotion) and `epistemic_go_gate` accepts exactly it — but that is
    # the VERDICT layer, thousands of lines and one real run too late. A
    # bundle with no primary prepared cleanly and failed only there.
    #
    # The secondary is NOT required here: the frozen text names it, but
    # nothing the builder can point to makes its presence mandatory, and
    # inventing a requirement is the failure this codebase keeps paying
    # for. Required: the primary present. Forbidden: anything outside the
    # ruled pair.
    channels = set(oracle)
    if PRIMARY_THETA_CHANNEL not in channels:
        raise MCInputError(
            "primary_theta_channel_absent",
            f"oracle_daily carries {sorted(channels)} and not "
            f"{PRIMARY_THETA_CHANNEL!r}; the primary is frozen and the "
            "verdict gate accepts no other, so a bundle without it can "
            "never reach a verdict")
    unruled = sorted(channels - {PRIMARY_THETA_CHANNEL,
                                 SECONDARY_THETA_CHANNEL})
    if unruled:
        raise MCInputError(
            "theta_channel_outside_ruled_set",
            f"{unruled} is outside the ruled pair "
            f"{[PRIMARY_THETA_CHANNEL, SECONDARY_THETA_CHANNEL]}; an "
            "unruled channel would enter day_sequences, traded_day_sets "
            "and the prepared identity without anyone having ruled it")
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
                               f"{theta}: {len(missing_tp)} of "
                               f"{len(tp)} tp days lack a record: "
                               f"{missing_tp[:3]}")
        # C6 (i) — the SAME obligation on the FP side. It was never
        # checked: an FP day without a record is silently a no-trade day
        # in every world that draws it, which biases every path metric
        # downward while the day universe still claims the day exists.
        missing_fp = sorted(set(fp) - ref_dates)
        if missing_fp:
            raise MCInputError("fp_day_without_record",
                               f"{theta}: {len(missing_fp)} of "
                               f"{len(fp)} fp days lack a record: "
                               f"{missing_fp[:3]}")
        day_sequences[theta] = ordered
        traded[theta] = frozenset(tp)
        theta_population[theta] = frozenset(set(tp) | set(fp))

    # C6 (iii) — cross-θ population identity. Checked BEFORE the
    # record-side half of the equality so a genuine θ-population drift
    # surfaces under its OWN code instead of being reported as one θ's
    # unclassified records.
    populations = {frozenset(p) for p in theta_population.values()}
    if len(populations) > 1:
        sizes = {th: len(p) for th, p in sorted(theta_population.items())}
        sample = sorted(set().union(*populations)
                        - set().intersection(*populations))
        raise MCInputError(
            "theta_population_drift",
            f"θ channels disagree about the day population {sizes}; "
            f"{len(sample)} day(s) appear in some channels only: "
            f"{sample[:3]}")
    # C6 (ii) — the other half of the equality: every record day must be
    # CLASSIFIED by the oracle. A record with no tp/fp class is a day the
    # bundle can trade but the day universe never accounted for, i.e. the
    # producer's exhaustive TP/FP partition did not hold.
    for theta, population in sorted(theta_population.items()):
        unclassified = sorted(ref_dates - population)
        if unclassified:
            raise MCInputError(
                "record_without_oracle_class",
                f"{theta}: {len(unclassified)} of {len(ref_dates)} record "
                f"days are in neither tp_days nor fp_days: "
                f"{unclassified[:3]}")

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
    prepared = PreparedMCInput(
        trial_id=str(snap["trial_id"]),
        authorized_commit=str(snap["authorized_commit"]),
        file_sha256=MappingProxyType(dict(sha)),
        # N01 C1: the RAW custody-checked record bytes travel with the
        # prepared input, and `records` is re-derived from them inside
        # __post_init__ (the mapping below is declare-and-verify only).
        handoff_bytes=handoff_bytes,
        records=MappingProxyType(records),
        day_sequences=MappingProxyType(day_sequences),
        traded_day_sets=MappingProxyType(traded),
        seeds=seeds,
        k_per_seed=K_PER_SEED_FROZEN,
        method_digest=method_digest,
        authorization_snapshot=frozen_snap,
        calendar=cal,
        # B-PROV: WHICH authority certified this input travels with it.
        # Copied from the authority the entry point constructed — the
        # test entry can only ever supply a test_only one, and non-test
        # authorities exist ONLY inside
        # `load_custody_authority_from_attestation`.
        source_artifact_id=str(custody_authority.source_artifact_id),
        source_artifact_sha256=str(custody_authority.source_artifact_sha256),
        test_only=bool(custody_authority.test_only))
    # THE FACTORY BOUNDARY. The receipt is minted HERE and nowhere else,
    # on the far side of all ten checks, so "this object came out of the
    # battery" stops being a comment and becomes a verifiable fact the
    # seal can re-check (see `verify_battery_receipt`).
    _issue_battery_receipt(prepared, custody_authority)
    return prepared


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
                     channel: str, engine: str, scenario: str, *,
                     traded_selector=None) -> dict:
    """Map template slots to the drawn historical day's path record.

    A slot trades iff the drawn day is in the SELECTED set AND a sealed
    record exists for it (frozen: MC SS4.1 — bootstrap fills outcomes onto
    template slots, never invents trades).

    `traded_selector` is the B-27 seam and the ONLY thing a GRID cell
    changes. With None — every Oracle main-channel path, unchanged — the
    selected set is the channel's ORACLE-SELECTED set. A GRID-channel
    evaluation passes that cell draw's authorized marker sequence instead.
    Everything else stays: the same prepared authority, the same day
    population, the same calendar, the same sealed records, and the same
    "a slot trades only if a record exists" rule, so a selector can narrow
    which slots trade but can never invent a trade or reach a day the
    sealed population does not contain.
    """
    recs = prepared.records[(engine, scenario)]
    sel = (prepared.traded_day_sets[channel] if traded_selector is None
           else traded_selector)
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


# ---------------------------------------------------------------------------
# C4 — lane S2' authoritative fact-verification seam (consumer side)
# ---------------------------------------------------------------------------
# The production chain's ONE fact-verification entry, owned by lane S2' in
# `itsf.mc.platforms.authoritative`:
#
#     verify_event_stream(events, *, engine, platform) -> None
#         first violation raises AuthoritativeFactError(code, detail);
#         success returns None and NEVER a statistic.
#
# It is called UNCONDITIONALLY in `_run_path_atom` — after the lifecycle
# has run, before any fact is reduced. There is no caller flag, no config
# and no receipt that can skip it.
AUTHORITATIVE_VERIFIER_NAME = "verify_event_stream"
# CROSS-LANE JOIN STATE. The consumer ships NO stand-in: a local
# re-implementation would be a SECOND interpretation of the platform's
# facts, which is the exact defect the single-adapter rule exists to
# prevent. This flag was written while lane S2' was still in flight; the
# entry has since landed, so the join is CLOSED and an absent verifier is
# now a hard refusal rather than a tolerated pending state.
AUTHORITATIVE_VERIFIER_REQUIRED = True


def _verify_event_stream(events: Sequence, *, engine: str,
                         platform: str) -> None:
    """Call lane S2's verifier on an emitted event stream.

    Resolved by NAME at call time so the join is observable: the wiring
    exists whether or not the symbol does, and `AuthoritativeFactError`
    propagates untouched (it is lane S2's vocabulary, not ours — swallowing
    or re-wrapping it would hide which fact failed)."""
    from itsf.mc.platforms import authoritative as _auth
    verify = getattr(_auth, AUTHORITATIVE_VERIFIER_NAME, None)
    if verify is None:
        if AUTHORITATIVE_VERIFIER_REQUIRED:
            raise MCInputError(
                "authoritative_verifier_absent",
                f"itsf.mc.platforms.authoritative."
                f"{AUTHORITATIVE_VERIFIER_NAME} is required but absent — "
                "the consumer refuses rather than running unverified "
                "event streams")
        return None                       # PENDING lane S2' (see above)
    verify(events, engine=engine, platform=platform)
    return None


def _run_path_atom(prepared: PreparedMCInput, *, platform: str,
                   engine: str, scenario: str, channel: str,
                   world: Sequence[str], world_index: int,
                   phase_offset: int, lifecycle_config_digest: str,
                   master_seed: int, prepared_digest_value: str,
                   traded_selector=None
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
    paths = _paths_for_world(prepared, world, channel, engine,
                             scenario,
                             traded_selector=traded_selector)
    res = orch.run_lifecycle(cfg, days, paths, start_offset=phase_offset)
    # C4: lane S2's single fact-verification entry, UNCONDITIONALLY, on
    # every emitted stream, before a single fact is reduced.
    _verify_event_stream(res.events, engine=engine, platform=platform)
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
        e2_over_budget_days=facts["e2_over_budget_days"],
        e2_intraday_over_budget_days=facts[
            "e2_intraday_over_budget_days"])


# R2.1 PHASE G retracted the R2 necessary-conditions boolean ("any payout
# AND not all skipped") as a verdict gate: the metrics stayed mechanical
# and the reduction rule was left unfrozen, which kept the Checkpoint-0
# verdict unreachable by construction.
#
# RULED 2026-08-24 (M1-M5, delegated to Codex GPT-5.6 Sol under Aaron's
# named batch delegation). The reduction now exists, in
# `itsf.mc.feasibility`, and this constant records WHICH ruling -- not
# merely that one happened. A later ruling changes this string, and every
# FeasibilityEvidence carrying the old one is rejected rather than
# silently reinterpreted under a rule it was never evaluated against.
FEASIBILITY_GATE_STATUS = "RULED_ND2_ND3_2026-08-24"

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
    # D1 (2026-08-24) ruled the predicate, so both are counted now.
    "e2_over_budget_days": "COMPUTED",
    "e2_intraday_over_budget_days": "COMPUTED",
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
    # N01 C1 — the records custody chain is proven BEFORE the first
    # lifecycle of EVERY execution, forward run and replay alike. A
    # prepared input whose live record mapping is not what its
    # custody-checked bytes yield cannot run at all, so a forged input
    # cannot "pass on both sides" by being handed to both.
    verify_records_custody_chain(
        prepared, where=f"{run_label}/{platform}|{engine}/{scenario}")
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


def fixed_world_reports(observations: ObservationSet) -> tuple:
    """The three conditional-aleatoric reports M11 fixes, low -> mid -> high.

    The SELECTION is not made here and must never be: it lives in
    `itsf.mc.fixed_world`, which turns world-mean EV into three order
    statistics, and this function only carries the resulting indices into
    `run_conditional_aleatoric` one at a time. Keeping the two apart is
    what lets a reader check WHICH worlds were reported and why -- the
    indices are visible in between rather than chosen inside a call.

    Before M11 the guard here asserted that no selection rule existed
    anywhere. It now asserts that this module still makes none, which is
    the half of that guarantee that survived the ruling."""
    from .fixed_world import select_fixed_worlds
    picked = select_fixed_worlds(observations.world_means())
    return tuple(run_conditional_aleatoric(observations, world_index=w)
                 for w in picked)


def run_conditional_aleatoric(observations: ObservationSet, *,
                              world_index: int) -> AleatoricResult:
    """M attempt paths inside ONE FIXED world (frozen: MC SS5 conditional
    aleatoric — "固定世界内 M 条账户路径的结果分布"), sliced out of the
    executed atom trace.

    The caller NAMES the world, and still does. Which world(s) the
    report fixes was undecided when this was written; M11 ratified it on
    2026-08-24 as an order statistic over world-mean EV, and it lives in
    `itsf.mc.fixed_world`. Keeping it out of this function is the point:
    the selection arrives as an explicit index that a reader can check."""
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
                            stress: EpistemicResult,
                            *, feasibility=None):
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
    # R2.1 PHASE G left the metric->boolean reduction unfrozen and refused
    # HERE, which kept every Checkpoint-0 verdict unreachable. M1-M5 ruled
    # it on 2026-08-24, so the gate can now be crossed -- but only with the
    # composed evidence, never with a caller's assertion.
    from .feasibility import ComboFeasibility, FEASIBILITY_RULING
    from .verdict import VerdictInput
    if feasibility is None:
        raise MCInputError(
            "feasibility_gate_input_absent",
            "the feasibility reduction is ruled (M1-M5, 2026-08-24) but "
            "this call supplied none; pass the ComboFeasibility that "
            "itsf.mc.feasibility.combo_feasibility computed for THIS combo")
    # A BARE BOOLEAN IS REFUSED, and this is the point of the type. `True`
    # carries no gate outcomes, no scenario set and no ruling id, so a
    # caller could assert feasibility that nothing measured -- which is
    # exactly what R2's retracted necessary-conditions boolean did.
    if not isinstance(feasibility, ComboFeasibility):
        raise MCInputError(
            "feasibility_not_composed_evidence",
            f"feasibility={type(feasibility).__name__}; Checkpoint-0 takes "
            "a ComboFeasibility carrying the gate outcomes it was composed "
            "from, never a bare boolean a caller can assert")
    if feasibility.ruling != FEASIBILITY_RULING:
        raise MCInputError(
            "feasibility_ruling_mismatch",
            f"evidence carries {feasibility.ruling!r}, this build rules "
            f"{FEASIBILITY_RULING!r}; a verdict must not be assembled from "
            "gates evaluated under a different ruling")
    return VerdictInput(
        p5_cons=cons.p5, median_cons=cons.median,
        median_stress=stress.median, p95_cons=cons.p95,
        feasible=feasibility.feasible,
        platform=cons.platform, engine=cons.engine, channel=cons.channel)


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
    category_stable_under_doubling: bool     # rule (a) — the B arm
    category_same_across_seeds: bool         # rule (b) — seeds 7/13/31
    quantile_drift_ok: bool                  # rule (c)
    mcse_ok: bool                            # rule (d)
    drift_by_axis: Mapping                   # axis -> {quantile: |delta|}
    #: THE GRID SECTION'S OWN STANDING, reported BESIDE the four rules and
    #: deliberately not inside them.
    #:
    #: It used to be ANDed into `category_stable_under_doubling`, which made
    #: one boolean mean two incompatible things: a MAIN-channel condition
    #: whose failure must withhold the judgment, and a GRID condition whose
    #: failure M7 says must NOT (it seals the grid section NON_CONVERGED and
    #: withdraws `deployable_region`'s right to support H1 entry, and nothing
    #: more). Folded together, neither consequence could be applied without
    #: applying the other -- so neither was applied at all, and a failed main
    #: channel still produced an admissible category.
    grid_converged: bool = True

    @property
    def converged(self) -> bool:
        """THE MAIN CHANNEL, and only it. Rules (a)-(d) of MC SS5.

        `grid_converged` is excluded on purpose: see the field above. A
        reader that wants both facts reads both fields, which is what the
        seal candidate now records.
        """
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
                              k_witness=None,
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
    5. K axis (N11): admitted ONLY against a `KReplayEvidence` witness
       minted from a `GridReplayAuthority`. The epistemic layer is B
       worlds x M start phases and does not consume K at all, so a
       `double_K` label has NO counterpart inside `results`; the only
       honest witness is the pair of Appendix-A region maps at K and 2K
       (N-D2 M6), and this is where the outer K is bound to it. A K pass
       must also leave the Oracle main channel bit-identical, because K
       is inner random source (2), "grid analysis ONLY";
    6. rules (a)-(d) are then computed and returned.

    WHAT THE K ARM DOES *NOT* DO (N-D2 M7): a non-converged grid does not
    withhold the Checkpoint-0 verdict. The two regions are report items
    that take no part in GO/STOP; their K-convergence is the grid
    section's own validity precondition, so failure seals that section
    NON_CONVERGED and withdraws `deployable_region`'s right to support
    H1 entry, and nothing more."""
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
    # (4) K — the axis the sealed GRID-B supplement unblocked (N11).
    # `k_axis_evidence_blocked_grid_replay` used to fire here
    # unconditionally. It is now conditional on the witness being absent:
    # the refusal's REASON was never "K is forbidden", it was "no actual
    # K-doubled evidence can exist", and a sealed per-day DAY_STRATA
    # authority is exactly what made it able to exist.
    admitted_witness = None
    if "K" in doubled_by_axis:
        from itsf.mc import grid_replay as _gr
        if k_witness is None:
            raise MCInputError(
                "k_axis_evidence_blocked_grid_replay",
                "a K entry needs its KReplayEvidence witness: the region "
                "maps at K and 2K are the ONLY inner witness a K-doubled "
                "pass has (N-D2 M6) — outer metadata may not impersonate "
                "it. Mint one with grid_replay.derive_k_replay_evidence "
                "from a GridReplayAuthority over the sealed supplement")
        _gr.verify_k_replay_evidence(k_witness)
        k_run = doubled_by_axis["K"]
        # scale + provenance: K doubles, B and M do not move.
        _check_run_provenance(base, k_run, "K")
        # THE OUTER/INNER K BINDING. This is what the pre-N11 guard
        # `test_the_outer_k_has_no_inner_witness_and_that_is_deliberate`
        # demanded, placed at the layer where the witness actually lives.
        if k_witness.prepared_digest != base.prepared_digest:
            raise MCInputError("provenance_mismatch",
                               "k_witness vs base prepared digest")
        if k_witness.master_seed != base.master_seed:
            raise MCInputError(
                "k_replay_inner_mismatch:master_seed",
                f"witness carries {k_witness.master_seed}, base run "
                f"{base.master_seed}")
        if k_witness.k != base.K:
            raise MCInputError(
                "k_replay_inner_mismatch:K",
                f"witness base arm K={k_witness.k}, base run K={base.K}")
        if k_witness.k_doubled != k_run.K:
            raise MCInputError(
                "k_replay_inner_mismatch:K",
                f"witness doubled arm K={k_witness.k_doubled}, "
                f"{k_run.run_label} K={k_run.K}")
        # K is inner random source (2), "grid analysis ONLY", and M10
        # reruns the grid channel alone — so a K pass MUST leave the
        # Oracle main channel bit-identical. A K run whose Checkpoint
        # statistics moved either did not hold K to the grid, or is not
        # the run it claims to be.
        for cid in sorted(base.results):
            if cid not in k_run.results:
                raise MCInputError(
                    "run_evidence_inner_mismatch:combo",
                    f"{k_run.run_label} is missing combo {cid}")
            for role, b_r, k_r in (
                    ("Conservative", base.results[cid][0],
                     k_run.results[cid][0]),
                    ("Stress", base.results[cid][1],
                     k_run.results[cid][1])):
                for field in ("p5", "median", "p95", "between_world_sd",
                              "max_within_world_se"):
                    if getattr(b_r, field) != getattr(k_r, field):
                        raise MCInputError(
                            "k_axis_main_channel_not_invariant",
                            f"{k_run.run_label}:{cid}:{role}.{field} moved "
                            f"{getattr(b_r, field)} -> {getattr(k_r, field)} "
                            "on a K-doubling run; K is grid-analysis only "
                            "and may not reach the Oracle main channel")
        admitted_witness = k_witness
    # (5) axes-set completeness.
    if set(doubled_by_axis) != DOUBLING_AXES:
        raise MCInputError("doubling_axes_violation",
                           f"need exactly {sorted(DOUBLING_AXES)}, got "
                           f"{sorted(doubled_by_axis)}")
    return _convergence_rules_a_to_d(base, doubled_by_axis, seed_runs,
                                     k_witness=admitted_witness,
                                     prepared=prepared)


def _run_category(run: RunEvidence, *, prepared) -> str:
    """The Checkpoint-0 decision category of ONE run (STOP/GO/beta/alpha),
    reduced through the SAME single internal path the verdict uses, so
    rule (a)/(b) can never compare a category the verdict would not
    produce — including the feasibility composition (B-26)."""
    from itsf.mc.verdict import apply_verdict
    return apply_verdict(_reduce_primary_from_base(
        run, prepared=prepared)).verdict


#: frozen: the key quantiles rule (c) acts on. MC_METHOD_SPEC SS4.4 fixes
#: the unit (24-month total prop_operating / 24 = USD per calendar month)
#: and names P5/P50/P95 as the decision quantiles.
KEY_QUANTILE_FIELDS = ("p5", "median", "p95")


def _convergence_rules_a_to_d(base: RunEvidence, doubled_by_axis: Mapping,
                              seed_runs: Mapping, *, k_witness, prepared
                              ) -> ConvergenceReport:
    """Rules (a)-(d) of MC SS5, computed from the supplied evidence.

    (a) doubling invariance. The B arm is a CHECKPOINT-category
        obligation. The K arm is NOT: per N-D2 M6 the K object is the two
        frozen Appendix-A region maps, because the Checkpoint layer does
        not consume K and calling a K-blind category twice would be the
        empty verification the master plan prohibits. So K contributes
        its region-map convergence instead -- reported as `grid_converged`,
        BESIDE rule (a) rather than multiplied into it, because M7 gives the
        two failures different consequences and one boolean cannot carry
        both.
    (b) the three master seeds agree on the category.
    (c) key-quantile drift within max($25, relative 5%), measured against
        the base run per combo and per scenario role.
    (d) within-world MCSE <= 10% of the between-world SD — already
        DERIVED on every EpistemicResult from its own atom trace, so this
        reads the derived flag rather than recomputing it from numbers a
        caller could have supplied.
    """
    base_category = _run_category(base, prepared=prepared)
    # --- (a) ----------------------------------------------------------
    category_stable = True
    for axis in sorted(doubled_by_axis):
        if axis == "K":
            continue                      # M6: K's object is the regions
        if _run_category(doubled_by_axis[axis],
                         prepared=prepared) != base_category:
            category_stable = False
    grid_converged = True if k_witness is None else k_witness.grid_converged
    # --- (b) ----------------------------------------------------------
    same_across_seeds = all(
        _run_category(seed_runs[s], prepared=prepared) == base_category
        for s in sorted(seed_runs))
    # --- (c) ----------------------------------------------------------
    drift_by_axis, drift_ok = {}, True
    arms = [(f"double_{axis}", doubled_by_axis[axis])
            for axis in sorted(doubled_by_axis)]
    arms += [(f"seed_{seed}", seed_runs[seed]) for seed in sorted(seed_runs)]
    for label, run in arms:
        per_arm = {}
        for cid in sorted(base.results):
            if cid not in run.results:
                raise MCInputError(
                    "run_evidence_inner_mismatch:combo",
                    f"{run.run_label} is missing combo {cid}")
            for role, b_r, o_r in (("Conservative", base.results[cid][0],
                                    run.results[cid][0]),
                                   ("Stress", base.results[cid][1],
                                    run.results[cid][1])):
                for field in KEY_QUANTILE_FIELDS:
                    b_v, o_v = getattr(b_r, field), getattr(o_r, field)
                    delta = abs(o_v - b_v)
                    per_arm[f"{cid}|{role}|{field}"] = delta
                    if delta > max(CONV_ABS_USD, CONV_REL * abs(b_v)):
                        drift_ok = False
        drift_by_axis[label] = MappingProxyType(per_arm)
    # --- (d) ----------------------------------------------------------
    mcse_ok = True
    for run in [base] + [r for _, r in arms]:
        for pair in run.results.values():
            for r in pair:
                if not r.mcse_ok:
                    mcse_ok = False
    return ConvergenceReport(
        category_stable_under_doubling=category_stable,
        category_same_across_seeds=same_across_seeds,
        quantile_drift_ok=drift_ok,
        mcse_ok=mcse_ok,
        drift_by_axis=MappingProxyType(drift_by_axis),
        grid_converged=grid_converged)


def _reduce_primary_from_base(base: RunEvidence, *,
                              prepared: "PreparedMCInput") -> dict:
    """R2.2 PHASE D — THE single internal reduction: Primary VerdictInputs
    are derived EXCLUSIVELY from `base.results` (Conservative/Stress,
    platform, engine, theta channel and prepared digest all come from the
    same RunEvidence). There is no public entry that accepts externally
    built VerdictInputs, so a hand-made positive grid has no callable
    path into the verdict or the seal.

    B-26: THE FEASIBILITY EVIDENCE IS COMPOSED HERE, and this is the
    extension the earlier draft of this docstring reserved — "a typed,
    provenance-bound decision-evidence object attached to this same
    reduction, never a reopened boolean". M1-M5 ruled the three gates on
    2026-08-24; `feasibility.combo_feasibility` already implemented them
    and already refuses a missing scenario. What was missing was only
    that nobody passed its product in, so `epistemic_go_gate_input`
    refused `feasibility_gate_input_absent` and no Checkpoint-0 category
    was reachable. Nothing about the methodology is decided here.

    WHAT BINDS IT. `prepared` is required and its digest must equal the
    run's, so the gates cannot be evaluated over a different sealed input
    than the one the epistemic results came from. That single check also
    covers the day universe, because `prepared_digest` binds "the
    complete day sequences and traded sets per channel" — a prepared
    input with a different universe cannot carry a matching digest.

    WHERE THE DAY UNIVERSE COMES FROM. `day_sequences[PRIMARY_THETA_
    CHANNEL]` — the sealed day POPULATION for the only channel
    Checkpoint-0 accepts. That is what M2's constant names ("from the
    SEALED DAY UNIVERSE — dates, not results ... an S0-side
    measurement"). It is deliberately NOT `traded_day_sets`: that is the
    ORACLE-SELECTED (TP) subset, so feeding it to the frequency gate
    would make a feasibility gate consume the oracle classification, and
    the gate's whole claim to being computable without touching a
    revealed value is that its input is dates.

    A `FeasibilityGateError` is translated into the fail-closed
    `MCInputError` vocabulary with its own code preserved. It is a
    ValueError but NOT an MCInputError, so letting it escape would be the
    D-4 defect again: a caller's refusal handling would not catch it."""
    base.validate_inner_binding()
    if not isinstance(prepared, PreparedMCInput):
        raise MCInputError(
            "prepared_authority_missing",
            "the reduction needs the prepared input: the feasibility gates "
            "are evaluated over the SEALED day universe, which only the "
            "prepared input carries")
    if prepared_digest(prepared) != base.prepared_digest:
        raise MCInputError(
            "provenance_mismatch",
            f"{base.run_label}: feasibility would be composed over a "
            "different prepared input than the run's own evidence")
    from .feasibility import FeasibilityGateError, combo_feasibility
    day_universe = prepared.day_sequences[PRIMARY_THETA_CHANNEL]
    reduction = {}
    for cid, (cons, stress) in sorted(base.results.items()):
        # keyed by each result's OWN declared scenario, so a mis-roled pair
        # collapses to one key and `combo_feasibility` refuses with
        # `feasibility_scenario_missing` rather than silently evaluating
        # M5's conjunction over whichever scenario happened to be present.
        try:
            feasibility = combo_feasibility(
                {cons.scenario: cons.observations,
                 stress.scenario: stress.observations}, day_universe)
        except FeasibilityGateError as exc:
            raise MCInputError(exc.code, f"{cid}: {exc}") from exc
        reduction[cid] = epistemic_go_gate_input(cons, stress,
                                                feasibility=feasibility)
    return reduction


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
        "records_digest": prepared.records_digest,
        "record_keys": records_key_index(prepared.records),
        "seeds": list(prepared.seeds),
        "k_per_seed": prepared.k_per_seed,
        "method_digest": prepared.method_digest,
        # B-PROV — the custody provenance travels INSIDE the pinned
        # bytes the cold replay starts from, not only on the live object.
        "provenance": {
            "source_artifact_id": prepared.source_artifact_id,
            "source_artifact_sha256": prepared.source_artifact_sha256,
            "test_only": prepared.test_only},
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


def verify_records_custody_chain(prepared: PreparedMCInput, *,
                                 where: str = "") -> dict:
    """Prove that FOUR things are one chain, and return the witness.

      link 1  raw handoff FILE BYTES -> sha256, which must equal the
              `file_sha256` entry the prepared identity hashes;
      link 2  those same bytes, RE-PARSED -> the records canonical
              content digest;
      link 3  that digest must be the one INSIDE the serialised prepared
              identity preimage (read back out of the bytes, not off the
              live attribute), and the preimage must hash to
              `prepared_digest`;
      link 4  the mapping the LIFECYCLE will actually read
              (`prepared.records`) must be that same content.

    Any break refuses with its own code. This is the check that makes
    "the replay re-derived the records" a verifiable claim rather than a
    comment."""
    prefix = f"{where}: " if where else ""
    # link 1 + 2 — from the bytes, never from the live mapping
    reparsed = records_from_handoff_bytes(prepared.handoff_bytes)
    for name in sorted(HANDOFF_FILE_SET):
        got = hashlib.sha256(prepared.handoff_bytes[name]).hexdigest()
        want = prepared.file_sha256.get(name)
        if got != want:
            raise MCInputError(
                "records_custody_bytes_mismatch",
                f"{prefix}{name}: source bytes hash {got[:12]} != "
                f"identity-pinned {str(want)[:12]}")
    reparsed_digest = records_canonical_digest(reparsed)
    # link 3 — read the identity back OUT of the serialised preimage
    raw_identity = prepared_identity_bytes(prepared)
    identity = json.loads(raw_identity.decode("utf-8"))
    if identity.get("records_digest") != reparsed_digest:
        raise MCInputError(
            "records_custody_identity_mismatch",
            f"{prefix}prepared identity carries records_digest "
            f"{str(identity.get('records_digest'))[:12]} != "
            f"{reparsed_digest[:12]} re-parsed from the custody bytes")
    if identity.get("record_keys") != records_key_index(reparsed):
        raise MCInputError(
            "records_custody_identity_mismatch",
            f"{prefix}prepared identity's engine/scenario/date key index "
            "disagrees with the re-parsed records")
    pdig = hashlib.sha256(raw_identity).hexdigest()
    if pdig != prepared_digest(prepared):
        raise MCInputError(
            "prepared_identity_bytes_unstable",
            f"{prefix}the pinned prepared bytes do not reproduce the "
            "prepared digest")
    # link 4 — what the lifecycle reads
    live_digest = records_canonical_digest(prepared.records)
    if live_digest != reparsed_digest:
        raise MCInputError(
            "records_custody_content_mismatch",
            f"{prefix}the records mapping the lifecycle would read "
            f"({live_digest[:12]}) is not the content the custody bytes "
            f"yield ({reparsed_digest[:12]})")
    return {
        "handoff_sha256": {n: prepared.file_sha256[n]
                           for n in sorted(HANDOFF_FILE_SET)},
        "records_digest": reparsed_digest,
        "prepared_identity_records_digest": identity["records_digest"],
        "prepared_digest": pdig,
        "atom_records_digest": live_digest,
    }


def replay_prepared_from_custody_bytes(prepared: PreparedMCInput
                                       ) -> PreparedMCInput:
    """Build a NEW prepared input for the cold replay by RE-PARSING the
    records out of the custody-held raw handoff bytes.

    The replay input takes its numerical authority from EXACTLY ONE
    place: those immutable bytes, whose sha256 is pinned inside the
    prepared identity. It never takes it from
      * the live `records` mapping the caller handed in (the R2.3 defect:
        the same live object was passed straight back, so a forged trace
        replayed against its own forgery),
      * anything reverse-engineered from the forward observations, or
      * a records snapshot the ReplaySpec merely DECLARES (a declared
        digest is checked against this rebuild, never trusted as its
        source).

    The rebuilt object is then required to carry the SAME identity as the
    original — same prepared digest, same records digest — so a rebuild
    that differs in any bound field refuses instead of quietly replaying
    a different world."""
    if not isinstance(prepared, PreparedMCInput):
        raise MCInputError("prepared_authority_missing",
                           f"{type(prepared).__name__} is not a "
                           "PreparedMCInput")
    verify_records_custody_chain(prepared, where="forward input")
    replay = PreparedMCInput(
        trial_id=prepared.trial_id,
        authorized_commit=prepared.authorized_commit,
        file_sha256=MappingProxyType(dict(prepared.file_sha256)),
        handoff_bytes=MappingProxyType(dict(prepared.handoff_bytes)),
        day_sequences=MappingProxyType(dict(prepared.day_sequences)),
        traded_day_sets=MappingProxyType(dict(prepared.traded_day_sets)),
        seeds=tuple(prepared.seeds),
        k_per_seed=prepared.k_per_seed,
        method_digest=prepared.method_digest,
        authorization_snapshot=prepared.authorization_snapshot,
        calendar=TemplateCalendar(
            days=tuple(prepared.calendar.days),
            first_month_offsets=tuple(
                prepared.calendar.first_month_offsets)),
        # B-PROV: the provenance is carried across verbatim. It is bound
        # into the identity, so dropping or altering it here would refuse
        # at the `cold_replay_prepared_binding_mismatch` check below —
        # the replay cannot launder a claim.
        source_artifact_id=prepared.source_artifact_id,
        source_artifact_sha256=prepared.source_artifact_sha256,
        test_only=prepared.test_only,
        # records: DERIVED inside __post_init__ from the bytes above. No
        # value is passed, so no caller mapping can reach the replay.
        records=None, records_digest=None)
    if replay.records is prepared.records:          # pragma: no cover
        raise MCInputError(
            "cold_replay_records_aliased",
            "the replay input shares the forward run's records object — "
            "it must be re-parsed, not aliased")
    if replay.records_digest != prepared.records_digest:
        raise MCInputError(
            "cold_replay_records_digest_mismatch",
            f"re-parsed records {str(replay.records_digest)[:12]} != "
            f"forward records {str(prepared.records_digest)[:12]}")
    if prepared_digest(replay) != prepared_digest(prepared):
        raise MCInputError(
            "cold_replay_prepared_binding_mismatch",
            "the rebuilt replay input does not reproduce the forward "
            "prepared digest")
    # FACTORY BOUNDARY, replay side. The rebuild is a direct
    # construction, so without this it would arrive at the seal
    # receipt-less and the seal would refuse its OWN replay. The receipt
    # is CARRIED, never minted: an input that had none still has none
    # afterwards, so the replay cannot launder an un-battery-validated
    # object into a validated one. Carrying is sound because every
    # component the receipt binds is also bound into the prepared digest,
    # and the two digests were just proven equal above.
    if getattr(prepared, "battery_receipt", None) is not None:
        object.__setattr__(replay, "battery_receipt",
                           prepared.battery_receipt)
    verify_records_custody_chain(replay, where="replay input")
    return replay


@dataclass(frozen=True, slots=True)
class ReplaySpec:
    """The COMPLETE cold-start specification of ONE observation set. It
    carries no statistic and no conclusion — only what is needed to
    re-execute the run from scratch.

    `records_digest` is a BINDING, not a source: the replay re-derives
    the records from the custody bytes and REQUIRES the declared digest
    to match. A caller who rewrites it (or who rewrites it together with
    a swapped live mapping) is refused, never followed."""
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
    records_digest: str | None = None

    @staticmethod
    def from_observations(obs: ObservationSet, *,
                          records_digest: str | None = None
                          ) -> "ReplaySpec":
        return ReplaySpec(
            run_label=obs.run_label, platform=obs.platform,
            engine=obs.engine, scenario=obs.scenario,
            theta_channel=obs.theta_channel, B=obs.B,
            master_seed=obs.master_seed,
            prepared_digest=obs.prepared_digest,
            lifecycle_config_digest=obs.lifecycle_config_digest,
            rng_spec=mc_atoms.RNG_SPEC,
            method_version=mc_atoms.METHOD_VERSION,
            records_digest=records_digest)


def cold_replay_observation_set(prepared: PreparedMCInput,
                                spec: ReplaySpec) -> ObservationSet:
    """Re-execute ONE observation set from a COLD START.

    Cold start = the RECORDS are re-parsed from the custody-checked raw
    handoff bytes into a NEW prepared object, the identity is re-derived
    from the PINNED prepared bytes, the config digest is re-derived from
    the LIVE frozen modules, the RNG spec and method version are
    re-checked, the world table is rebuilt from (prepared, seed, B,
    block, length), and every lifecycle is run again. Nothing from the
    forward run is reused — in particular NOT its records mapping, which
    the R2.3 implementation handed straight back to
    `run_observation_set`."""
    if type(spec) is not ReplaySpec:
        raise MCInputError("cold_replay_spec_invalid",
                           f"{type(spec).__name__} is not a ReplaySpec")
    # N01 C1 — BEFORE any lifecycle executes: rebuild the numerical
    # authority from the custody bytes and prove the four-link chain.
    replay_input = replay_prepared_from_custody_bytes(prepared)
    if spec.records_digest is not None and \
            spec.records_digest != replay_input.records_digest:
        raise MCInputError(
            "cold_replay_records_digest_mismatch",
            f"spec declares records {str(spec.records_digest)[:12]} != "
            f"{str(replay_input.records_digest)[:12]} re-parsed from the "
            "custody bytes")
    cold_digest = hashlib.sha256(
        prepared_identity_bytes(replay_input)).hexdigest()
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
    # EXECUTE ON THE REBUILT INPUT — the whole point of C1: the lifecycles
    # consume records that were re-parsed from custody-checked bytes in
    # THIS call, not the mapping the caller is holding.
    return run_observation_set(
        replay_input, run_label=spec.run_label, platform=spec.platform,
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
    # N01 C1 — the four-link records custody witness, computed ONCE up
    # front (and again inside every per-set rebuild). It is a DESCRIPTION
    # in the receipt; nothing reads it back as permission.
    records_chain = verify_records_custody_chain(prepared,
                                                 where="replay evidence")
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
            spec = ReplaySpec.from_observations(
                obs, records_digest=prepared.records_digest)
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
        "records_custody_chain": records_chain,
        "legal_phase_support": list(legal),
        "lifecycle_config_digests": config_digests,
        "n_sets_replayed": len(comparisons),
        "comparisons": comparisons,
    }


def _assert_seal_provenance(prepared: PreparedMCInput) -> CustodyAuthority:
    """B-PROV — the seal boundary re-verifies the prepared input's CUSTODY
    ROOT against the code pins, and returns the authority it re-derived.

    Retaining the provenance (see `PreparedMCInput`) makes the difference
    VISIBLE; this makes it DECISIVE. A prepared input reaching the seal
    must be the product of the production attestation, and "the
    production attestation" is not a string it may assert about itself:

      1. `test_only` — the TEST_ONLY entry's own product has no business
         at a seal boundary, however honest it is;
      2. `source_artifact_id` vs ATTESTATION_PATH — the approved source;
      3. `source_artifact_sha256` vs ATTESTATION_SHA256_PINNED — the
         approved source's approved BYTES, pinned in reviewed code;
      4. trial / commit vs the values PARSED out of those bytes here and
         now — a prepared input bound to another trial cannot borrow this
         attestation's custody root;
      5. the per-file digest table vs the attestation's OWN table — the
         check a copied source string cannot survive, because reproducing
         it requires the sealed bundle's actual bytes;
      6. the BATTERY RECEIPT — that this object is the ten-check
         battery's own product and still carries the content the battery
         certified. (1)-(5) identify the custody authority; only (6)
         answers whether the battery ran at all.

    (2)+(3) are string comparisons against constants; (4)+(5) re-read and
    re-parse the attestation through the SAME constructor the production
    prepare entry uses, so the seal and the prepare agree by construction
    rather than by convention. This is the ONLY repository read on the
    seal path, it happens AFTER the unconditional cold replay, and it
    reads custody metadata only — the computation still consumes nothing
    but the immutable prepared object."""
    if not isinstance(prepared, PreparedMCInput):
        raise MCInputError("prepared_authority_missing",
                           f"{type(prepared).__name__} is not a "
                           "PreparedMCInput")
    if prepared.test_only:
        raise MCInputError(
            "seal_test_only_prepared_input",
            "the prepared input was certified by "
            f"{prepared.source_artifact_id!r} with test_only=True — the "
            "seal accepts ONLY the production attestation's product")
    if prepared.source_artifact_id != ATTESTATION_PATH:
        raise MCInputError(
            "seal_provenance_source_violation",
            f"custody source {prepared.source_artifact_id!r} != approved "
            f"{ATTESTATION_PATH!r}")
    if prepared.source_artifact_sha256 != ATTESTATION_SHA256_PINNED:
        raise MCInputError(
            "seal_provenance_source_digest_violation",
            f"custody source bytes {prepared.source_artifact_sha256[:12]} "
            f"!= code-pinned {ATTESTATION_SHA256_PINNED[:12]}")
    # re-derived HERE, from the pinned document, through the production
    # constructor — never from anything the caller carried in.
    authority = load_custody_authority_from_attestation()
    if prepared.trial_id != authority.trial_id or \
            prepared.authorized_commit != authority.authorized_commit:
        raise MCInputError(
            "seal_trial_commit_attestation_mismatch",
            f"prepared {prepared.trial_id}/"
            f"{prepared.authorized_commit[:12]} vs attestation "
            f"{authority.trial_id}/{authority.authorized_commit[:12]}")
    if dict(prepared.file_sha256) != dict(authority.file_sha256):
        differing = sorted(
            n for n in sorted(BUNDLE_EXACT_SET)
            if prepared.file_sha256.get(n) != authority.file_sha256.get(n))
        raise MCInputError(
            "seal_custody_table_mismatch",
            f"{len(differing)} of {len(BUNDLE_EXACT_SET)} bundle digests "
            f"disagree with the attestation table: {differing[:3]}")
    # (6) THE FACTORY BOUNDARY — and only now. (1)-(5) answer "which
    # authority certified this input"; they cannot answer "did the
    # ten-check battery actually run", because every field they read is
    # a public constructor parameter. Given a bundle and an attestation
    # that agree, a hand-built object or a `dataclasses.replace` of a
    # genuine one satisfies all five and then carries whatever
    # `method_digest` / `seeds` / `k_per_seed` / `day_sequences` /
    # `traded_day_sets` / `calendar` / `authorization_snapshot` its
    # author chose — reaching the feasibility gate as if it were sound.
    #
    # Ordering inside this function is deliberate: the five specific
    # checks stay FIRST so a forged source string, a foreign trial or a
    # substituted digest table each keeps its own precise code, and the
    # receipt check is the catch-all underneath them. It is still well
    # ahead of the reduction, so a battery failure can never be reported
    # as the feasibility gate's DECISION_REQUIRED.
    verify_battery_receipt(prepared)
    return authority


def verdict_and_seal_from_evidence(prepared: PreparedMCInput, *,
                                   base: RunEvidence,
                                   doubled_by_axis: Mapping,
                                   seed_runs: Mapping,
                                   k_witness=None,
                                   grid_convergence=None) -> dict:
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

    B-PROV — and then, before ANY reduction, the prepared input's custody
    root is re-verified against the code pins by
    `_assert_seal_provenance`. Ordering is deliberate: the replay stays
    unconditional and FIRST (N01 PHASE D3 invariant, pinned by
    `test_the_cold_replay_runs_before_any_other_refusal`), and the
    provenance boundary sits ahead of the feasibility gate so a
    provenance failure can never again be reported as "the feasibility
    decision is missing".

    THE FACTORY BOUNDARY — the same call now also verifies the BATTERY
    RECEIPT (`verify_battery_receipt`), which is what makes "the
    ten-check battery produced this object" a checkable fact rather than
    an assumption. A hand-built `PreparedMCInput` or a
    `dataclasses.replace` of a genuine one reaches this point looking
    perfectly provenanced and is refused HERE, under
    `seal_prepared_not_battery_validated` or
    `seal_battery_receipt_mismatch` — still ahead of the feasibility
    gate, so the old "it stopped at feasibility" outcome can no longer
    be mistaken for a refusal.

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
    # B-PROV: the custody root, re-verified against the code pins, AND
    # the factory boundary: the battery receipt, re-verified against the
    # live object. Before the reduction, so neither failure can ever
    # surface as the feasibility gate's DECISION_REQUIRED.
    _assert_seal_provenance(prepared)
    battery_receipt = prepared.battery_receipt
    reduction = _reduce_primary_from_base(base, prepared=prepared)
    # N13: the K witness travels with the evidence it belongs to. The
    # parameter is `k_witness`, not `k_replay`, deliberately:
    # `test_seal_entry_accepts_no_caller_conclusion` bans any seal parameter
    # whose name contains "replay", so that no caller-supplied replay
    # CONCLUSION can ever make the unconditional cold replay skippable.
    # This object is the grid witness rather than a replay receipt, but the
    # guard is a deliberate substring rule and the right move was to rename
    # the parameter, not to carve an exception into the guard.
    # `DOUBLING_AXES` is {B, K} and rule (a) is frozen, so a complete
    # axes set carries a K arm, and N11 admits that arm ONLY against a
    # `KReplayEvidence`. Before this the seal called convergence without
    # one, so no full-axes seal could ever be produced. The witness is
    # factory-only and self-digested, so accepting it here does not
    # reopen the hand-built-evidence hole: a caller cannot construct one,
    # and convergence re-verifies its digest and binds it to this run.
    convergence_report = convergence_from_evidence(
        base, doubled_by_axis, seed_runs, prepared=prepared,
        k_witness=k_witness)
    # THE GRID'S STANDING IS A CROSS-SEED FACT, and it is verified here.
    #
    # `k_witness` binds the K ARM to the base run -- that is its job and it
    # keeps it. But the grid section's status and `deployable_region`'s right
    # to support H1 entry are properties of the region maps ACROSS the three
    # research seeds, and taking them from one seed's witness let the other
    # two seeds' doubled-scale results be computed and then discarded. When a
    # K arm is supplied the cross-seed standing is REQUIRED, so a K-doubled
    # seal cannot be produced from one seed again.
    if k_witness is not None:
        from itsf.mc import grid_replay as _gr
        if grid_convergence is None:
            raise MCInputError(
                "grid_convergence_across_seeds_required",
                "a K arm seals the grid section, and that section's standing "
                "is the AND across every governed seed's witness. Mint it "
                "with grid_replay.aggregate_k_replay_evidence; one seed's "
                "witness is the K-arm binding, not the grid's standing")
        _gr.verify_grid_convergence(grid_convergence)
        if grid_convergence.first_witness_digest(
                k_witness.master_seed) != k_witness.evidence_digest:
            raise MCInputError(
                "grid_convergence_witness_not_in_aggregate",
                f"the K-arm witness for seed {k_witness.master_seed} is not "
                "the FIRST authorized attempt the cross-seed standing "
                "aggregated. The outer K arm is produced at the frozen "
                "scales, so it binds to that attempt; a seed that needed "
                "rule (e)'s retry still ends on a later one, and the "
                "standing carries both")
        if grid_convergence.prepared_digest != base.prepared_digest:
            raise MCInputError("provenance_mismatch",
                               "grid convergence vs base prepared digest")
        # TEST-ONLY GRID EVIDENCE IS NOT PRODUCTION SEAL-ADMISSIBLE.
        #
        # Recording the flag was not enough. A test-only standing reached
        # this boundary against a PRODUCTION prepared input and sealed
        # CONVERGED with `may_support_h1_entry` True -- the flag rode along
        # and admitted nothing, which is a label rather than a boundary. The
        # comparison is between two AUTHORITATIVE TYPED STATES, neither of
        # them a caller argument: `prepared.test_only` is the battery's own
        # product identity, and the standing's flag is capability-minted,
        # carried from the authority through every pass and witness, and
        # re-verified by its own digest a few lines above.
        #
        # It is asserted HERE, at the public seal entry, and before the
        # grid section is composed -- so a test-only CONVERGED standing can
        # never become a production seal candidate, and H1 support can never
        # be granted from it.
        if grid_convergence.test_only and not bool(prepared.test_only):
            raise MCInputError(
                "grid_evidence_test_only_at_production_seal",
                "the grid evidence is test_only and the prepared input is "
                "not: synthetic grid evidence may exist for testing and may "
                "never become production seal-admissible. Nothing here "
                "sanitizes it -- produce the evidence through the governed "
                "production authority, or seal a test_only prepared input")
        if bool(k_witness.test_only) is not bool(grid_convergence.test_only):
            raise MCInputError(
                "grid_convergence_test_only_mismatch",
                f"the K-arm witness is test_only={k_witness.test_only} and "
                f"the standing is test_only={grid_convergence.test_only}")
    elif grid_convergence is not None:
        raise MCInputError(
            "grid_convergence_without_k_arm",
            "a cross-seed grid standing was supplied with no K arm to bind "
            "it to")
    # M7 AND THE MAIN CHANNEL, and the difference between them is the point.
    #
    # A failed MAIN-channel condition -- rules (a)-(d) of MC SS5 -- means the
    # evidence does not support a Checkpoint-0 judgment, so no judgment and no
    # seal candidate is produced. This refusal used to be absent entirely: the
    # four booleans were computed, recorded in the seal, and never consulted,
    # so a run whose quantiles had not converged still returned an admissible
    # GO/STOP category.
    #
    # THE GRID EXCEPTION IS UNCHANGED AND STAYS EXACTLY AS RATIFIED. A
    # non-converged grid does NOT reach this refusal: it seals the grid
    # section NON_CONVERGED and withdraws `deployable_region`'s right to
    # support H1 entry (M7), and the Checkpoint-0 verdict is not withheld.
    # That is why `grid_converged` is no longer multiplied into rule (a) --
    # folded together, the grid's failure would now withhold the judgment,
    # which is precisely what M7 forbids.
    if not convergence_report.converged:
        failed = sorted(name for name in (
            "category_stable_under_doubling", "category_same_across_seeds",
            "quantile_drift_ok", "mcse_ok")
            if not getattr(convergence_report, name))
        raise MCInputError(
            "main_channel_not_converged",
            "the MAIN channel has not converged (%s): MC SS5 rules (a)-(d) "
            "are an admissibility precondition for a Checkpoint-0 judgment, "
            "so no verdict and no seal candidate is produced. This is NOT "
            "the grid exception -- a non-converged GRID seals its own "
            "section NON_CONVERGED and withholds nothing (M7)"
            % ", ".join(failed))
    verdict = apply_verdict(dict(reduction))
    digest_after = prepared_digest(prepared)
    if digest_before != digest_after:
        raise MCInputError("prepared_digest_instability",
                           f"{digest_before[:12]} -> {digest_after[:12]}")
    return {
        # v5: the seal candidate now RECORDS the battery receipt it
        # verified (digests only — no research value enters here), so a
        # reader can see WHICH battery product was sealed rather than
        # taking the seal's word that one existed.
        "schema": "mc_verdict_inputs.v5",
        "trial_id": prepared.trial_id,
        "authorized_commit": prepared.authorized_commit,
        "method_digest": prepared.method_digest,
        "method_version": mc_atoms.METHOD_VERSION,
        "prepared_digest": digest_before,
        "primary_theta_channel": PRIMARY_THETA_CHANNEL,
        # M7: the grid section's own standing, recorded beside the verdict
        # rather than folded into it. A non-converged grid withdraws
        # `deployable_region`'s right to support H1 entry and does NOT
        # withhold Checkpoint-0, so the seal states both facts.
        "convergence": {
            "category_stable_under_doubling":
                convergence_report.category_stable_under_doubling,
            "category_same_across_seeds":
                convergence_report.category_same_across_seeds,
            "quantile_drift_ok": convergence_report.quantile_drift_ok,
            "mcse_ok": convergence_report.mcse_ok,
            # the MAIN channel, which is now a precondition: reaching this
            # line at all means it is True
            "converged": convergence_report.converged,
            # the GRID's own standing, recorded beside it rather than folded
            # into it, so a reader sees two facts instead of one ambiguous one
            "grid_converged": convergence_report.grid_converged},
        "grid_section": ({"status": "NOT_SUPPLIED",
                          "may_support_h1_entry": False}
                         if k_witness is None else
                         {"status": grid_convergence.grid_seal_status,
                          "may_support_h1_entry":
                              grid_convergence.may_support_h1_entry,
                          "k": k_witness.k, "k_doubled": k_witness.k_doubled,
                          "authority_digest": k_witness.authority_digest,
                          "evidence_digest": k_witness.evidence_digest,
                          # EVERY governed seed, named with its own standing,
                          # so "the grid converged" can be checked per seed
                          # rather than taken from one of them
                          "seeds": list(grid_convergence.seeds),
                          "converged_by_seed": {
                              str(seed): bool(value) for seed, value
                              in sorted(
                                  grid_convergence.converged_by_seed.items())},
                          "converged_by_kind": {
                              str(kind): bool(value) for kind, value
                              in sorted(
                                  grid_convergence.converged_by_kind.items())},
                          "doublings_executed":
                              grid_convergence.doublings_executed,
                          "attempts_by_seed": {
                              str(seed): int(value) for seed, value
                              in sorted(
                                  grid_convergence.attempts_by_seed.items())},
                          "final_k_by_seed": {
                              str(seed): int(value) for seed, value
                              in sorted(
                                  grid_convergence.final_k_by_seed.items())},
                          "max_doublings": grid_convergence.max_doublings,
                          "convergence_digest":
                              grid_convergence.convergence_digest,
                          # synthetic evidence says so in the seal it produced
                          "test_only": bool(grid_convergence.test_only)}),
        "bundle_file_sha256": dict(prepared.file_sha256),
        "seeds": list(prepared.seeds),
        "trace_digests": base.trace_digests(),
        "trace_digest_of_digests": base.trace_digest_of_digests(),
        "cold_replay_receipt": replay_receipt,
        "battery_receipt": {
            "schema": battery_receipt.schema,
            "authority_source_artifact_id":
                battery_receipt.authority_source_artifact_id,
            "authority_source_artifact_sha256":
                battery_receipt.authority_source_artifact_sha256,
            "authority_test_only": battery_receipt.authority_test_only,
            "prepared_digest": battery_receipt.prepared_digest,
            "prepared_identity_sha256":
                battery_receipt.prepared_identity_sha256,
            "component_digests": dict(battery_receipt.component_digests)},
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
    # Invariant 5 of dec-registry-migration-2026-08-27 — one construction
    # site. This one also built a RELATIVE path, so it only resolved when
    # the process happened to be running from the repository root.
    from .registry_boundary import read_snapshot
    authorize_real_mc(read_snapshot().text)
    raise AssertionError("unreachable: authorize_real_mc always raises")
