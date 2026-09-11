"""N03 — SUPPLEMENT AUTHORITY / CUSTODY BINDING (lane S1).

WHAT THIS CLOSES. `day_strata_supplement.build_day_strata_supplement_test_only`
takes two arguments that decide what the supplement IS — the sealed day
universe (`expected_day_set`) and the run binding (`binding`) — and it
takes them from whatever the caller hands over. A caller who assembles
a plausible frozenset of dates and a five-key binding dict obtains a
well-formed, sealable supplement that was never tied to the sealed S0
input at all. This module makes the two arguments derivable from ONE
place: a `SupplementAuthority` minted from a `PreparedMCInput` that the
ten-check prepare battery actually produced.

THE FACTORY PATTERN IS BORROWED, NOT REINVENTED. `consumer.BatteryReceipt`
already solved "prove this object came out of the battery": a
module-private capability object that `__post_init__` requires and then
drops, so holding an instance cannot mint a second one and
`dataclasses.replace` — a constructor call — dies at the same gate.
`SupplementAuthority` uses exactly that pattern, and its single minter
demands `consumer.verify_battery_receipt(prepared)` first, so the
supplement path inherits the factory boundary instead of re-opening it.

THE §D.2.2 STRUCTURAL IDENTITY (`ops/DECISION_PACKET_N00_AND_ND1.md`).

    FOR_EACH_ENGINE_SCENARIO:  ref_dates == traded_set
    FOR_EACH_THETA:            (tp_dates UNION fp_dates) == traded_set
                               tp_dates INTERSECT fp_dates == EMPTY
    CROSS_THETA_POPULATION_IDENTITY=REQUIRED
    MISMATCH=SEALED_INTEGRITY_FAILURE

§D.2.4 records the mechanical fact that this identity is ALREADY enforced
by the prepare battery (`consumer._prepare_mc_input_impl`, the eight
codes listed in `IDENTITY_REFUSAL_CODES`), and narrows N03's obligation
accordingly: not "implement the identity" but "bind the supplement path
to the SAME identity under the SAME refusal codes, so a supplement cannot
build its own day universe". `enforce_day_universe_identity` is that
binding — an INDEPENDENT re-derivation from the prepared input, not a
trust of the battery's earlier verdict. A violation refuses BEFORE
anything is built and never "picks another universe and carries on".

VOCABULARY NOTE, deliberately disclosed. `PreparedMCInput.traded_day_sets`
is the per-θ ORACLE-SELECTED (TP) set — see `consumer._paths_for_world` —
NOT §D.2.2's `traded_set`, which names the whole day population. This
module therefore reconstructs, per θ:

    population := set(day_sequences[θ])        # §D.2.2 `traded_set`
    tp         := traded_day_sets[θ]
    fp         := population - tp

and enforces the identity against `ref_dates`, the record key set the
eight MC_HANDOFF_* files agree on. Because `fp` is a COMPLEMENT, a
tp/fp overlap cannot be represented in this projection; the `tp_fp_overlap`
check is kept anyway, explicitly, so that a future change to the
derivation cannot silently drop the requirement.

BLIND BY CONSTRUCTION. Nothing here reads a record's VALUES. The record
mapping is consumed for its KEYS (trade dates) only; the authority
exposes dates, digests, counts and identifiers, and nothing else. TP/FP
membership is consumed by the identity check and DROPPED — the
supplement is blind to the oracle classification as well as to outcomes.

NOTHING HERE AUTHORIZES ANYTHING. Minting an authority is not supplement
authorization: it certifies WHAT a supplement would have to be bound to
if one were ever authorized. `day_strata_supplement.authorize_supplement`
remains a deterministic refusal, and this module emits no registry event,
creates no directory, and reads no repository path.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from dataclasses import fields as _dc_fields
from typing import Mapping

from itsf.mc import atoms as _atoms
from itsf.mc import consumer as _mcc
from itsf.mc import day_strata_supplement as _ds
from itsf.mc import supplement_contract as _sc

# Re-exported so a caller catching supplement-layer refusals does not have
# to know which module defined the type. NEITHER is redefined here.
SupplementError = _ds.SupplementError          # authority-lifecycle refusals
MCInputError = _mcc.MCInputError               # sealed-input integrity

#: The supplement layer's ONE date grammar — aliased from
#: `day_strata_supplement`, never re-spelled, so the authority and the
#: builder cannot drift about what a trade date looks like.
ISO_DATE_RE = _ds._ISO_DATE

SUPPLEMENT_AUTHORITY_SCHEMA = "mc_supplement_authority.v1"
DAY_UNIVERSE_DIGEST_SCHEMA = "mc_supplement_day_universe.v1"
BUNDLE_TABLE_DIGEST_SCHEMA = "mc_supplement_bundle_table.v1"
AUTHORITY_DIGEST_SCHEMA = "mc_supplement_authority_preimage.v1"

#: Defaults, IMPORTED from their owning modules rather than re-spelled:
#: the supplement id the builder already pins, and the frozen MC method
#: version token the atom layer owns.
DEFAULT_SUPPLEMENT_ID = _ds.SUPPLEMENT_ID
SUPPLEMENT_METHOD_VERSION = _atoms.METHOD_VERSION

#: §D.2.4's eight codes. REUSED VERBATIM from the prepare battery — the
#: whole point of N03 is that the supplement path refuses under the SAME
#: vocabulary, so a reader triaging a refusal does not have to learn a
#: second dialect. `tests/test_mc_supplement_authority.py` asserts every
#: one of these literally appears in `consumer._prepare_mc_input_impl`,
#: so a rename there goes RED here instead of forking the vocabulary.
IDENTITY_REFUSAL_CODES = (
    "day_universe_missing",
    "day_sequence_not_ascending",
    "day_sequence_duplicates",
    "tp_fp_overlap",
    "tp_day_without_record",
    "fp_day_without_record",
    "theta_population_drift",
    "record_without_oracle_class",
)

#: Also reused from the prepare battery: the cross-file record-set
#: equality that IS §D.2.2's `FOR_EACH_ENGINE_SCENARIO: ref_dates ==
#: traded_set` half.
RECORD_SET_REFUSAL_CODE = "record_set_drift_across_files"

#: The ONLY identity code this module had to invent, and why no existing
#: code fits. In the prepare battery the population is CONSTRUCTED as
#: `tp + fp`, so "a TP day outside the day universe" is unrepresentable
#: and has no code. In the prepared input's PROJECTION the two arrive as
#: separate fields (`day_sequences` and `traded_day_sets`), so a forged
#: or drifted object CAN claim a traded day the day universe never lists.
#: That is neither `tp_day_without_record` (it may well have a record) nor
#: `tp_fp_overlap` (there is no fp side to overlap with), so it gets its
#: own name rather than being bent into one of the eight.
SUPPLEMENT_SPECIFIC_IDENTITY_CODES = (
    "supplement_traded_day_outside_universe",
)

#: Stated as a constant so a test can assert it, and so no reader has to
#: infer it from prose. Cf. `ops/ND1_PROFILE_RATIFICATION.md` §4.
SUPPLEMENT_AUTHORITY_IS_NOT_AUTHORIZATION = (
    "Minting a SupplementAuthority is NOT supplement authorization. It "
    "binds WHAT a supplement would have to be tied to; permission to run "
    "one requires a future NAMED registry authorization event that binds "
    "the exact commit, the supplement id and the output root. This module "
    "emits no registry event, creates no directory, and grants nothing.")


# ---------------------------------------------------------------------------
# Canonical digests (ONE serialisation authority: the supplement builder's)
# ---------------------------------------------------------------------------

def _digest(schema: str, value) -> str:
    """sha256 over `day_strata_supplement.canonical_json` — the same
    canonical form every supplement digest already uses."""
    return hashlib.sha256(
        _ds.canonical_json({"schema": schema, "value": value})
        .encode("utf-8")).hexdigest()


def day_universe_digest(days) -> str:
    """Digest of a day universe. Derived from the ENFORCED population and
    never supplied by a caller; sorted first, so it is deterministic and
    independent of the order the days arrived in."""
    return _digest(DAY_UNIVERSE_DIGEST_SCHEMA, sorted(str(d) for d in days))


def bundle_table_digest(file_sha256: Mapping) -> str:
    """Digest of the COMPLETE 14-file sealed-bundle digest table."""
    table = {str(k): str(v) for k, v in dict(file_sha256).items()}
    return _digest(BUNDLE_TABLE_DIGEST_SCHEMA,
                   {k: table[k] for k in sorted(table)})


def _source_input_sha256(prepared) -> str:
    """The sealed input's pinned identity bytes — the same preimage the
    cold replay starts from and the battery receipt binds."""
    return hashlib.sha256(
        _mcc.prepared_identity_bytes(prepared)).hexdigest()


# ---------------------------------------------------------------------------
# The §D.2.2 structural identity, re-derived from the prepared input
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DayUniverseIdentity:
    """The STRUCTURAL result of enforcing §D.2.2 — dates, counts and a
    digest. Carries no TP/FP membership and no outcome value."""
    day_universe: tuple            # ascending, unique trade dates
    theta_channels: tuple          # sorted channel names
    n_days: int
    day_universe_digest: str


def enforce_day_universe_identity(prepared) -> DayUniverseIdentity:
    """Re-derive and ENFORCE §D.2.2 from a prepared input.

    Independent of the prepare battery on purpose: the battery's verdict
    is a past event, and N03's obligation is that the SUPPLEMENT path
    cannot proceed on a day universe that fails the identity, whatever
    happened upstream. Refusals reuse the battery's own codes (see
    `IDENTITY_REFUSAL_CODES`) and its precedence — the per-θ record-side
    checks first, then cross-θ drift, then the record-side half — so a
    genuine θ drift surfaces under its own code instead of being reported
    as one θ's unclassified records.

    ORDERING NOTE, deliberate divergence from the battery. The battery
    checks ascending-ness before duplicates, because it sees the raw
    `tp_days` / `fp_days` lists. Here the projection is the MERGED SORTED
    sequence, in which any duplicate is necessarily adjacent and would
    therefore always be reported as `day_sequence_not_ascending`. The two
    checks are swapped so both codes stay reachable and distinct.

    A violation is a SEALED-INPUT INTEGRITY FAILURE and is raised as
    `MCInputError` — the same TYPE the prepare battery raises, so a
    handler that catches sealed-input integrity catches both.
    """
    if not isinstance(prepared, _mcc.PreparedMCInput):
        raise SupplementError(
            "supplement_authority_prepared_input_required",
            f"{type(prepared).__name__} is not a PreparedMCInput")

    # --- §D.2.2 half 1: FOR_EACH_ENGINE_SCENARIO ref_dates == traded_set
    records = prepared.records
    if not isinstance(records, Mapping) or not records:
        raise MCInputError(RECORD_SET_REFUSAL_CODE,
                           "the prepared input carries no records")
    want_keys = {(e, s) for e in _mcc.ENGINES for s in _mcc.SCENARIOS}
    if set(records) != want_keys:
        raise MCInputError(
            RECORD_SET_REFUSAL_CODE,
            f"record key set is not the {len(want_keys)}-file engine x "
            f"scenario cross: "
            f"{sorted(map(str, set(records) ^ want_keys))[:3]}")
    ref_key = (_mcc.ENGINES[0], _mcc.SCENARIOS[0])
    ref_dates = frozenset(str(d) for d in records[ref_key])
    if not ref_dates:
        raise MCInputError(RECORD_SET_REFUSAL_CODE,
                           f"{ref_key[0]}|{ref_key[1]} carries no records")
    for key in sorted(records, key=lambda k: (str(k[0]), str(k[1]))):
        dates = frozenset(str(d) for d in records[key])
        if dates != ref_dates:
            drift = sorted(ref_dates ^ dates)[:3]
            raise MCInputError(
                RECORD_SET_REFUSAL_CODE,
                f"{key[0]}|{key[1]} vs {ref_key[0]}|{ref_key[1]}: {drift}")

    # --- §D.2.2 half 2: the per-θ partition -------------------------------
    seqs = prepared.day_sequences
    tps = prepared.traded_day_sets
    if not isinstance(seqs, Mapping) or not isinstance(tps, Mapping) \
            or not seqs:
        raise MCInputError("day_universe_missing",
                           "day_sequences / traded_day_sets absent")
    if set(seqs) != set(tps):
        raise MCInputError(
            "day_universe_missing",
            f"θ channels disagree between day_sequences and "
            f"traded_day_sets: "
            f"{sorted(map(str, set(seqs) ^ set(tps)))[:3]}")
    channels = tuple(sorted(str(c) for c in seqs))

    populations: dict = {}
    for channel in channels:
        seq = tuple(str(d) for d in seqs[channel])
        if not seq:
            raise MCInputError("day_universe_missing", channel)
        for day in seq:
            if not ISO_DATE_RE.match(day):
                raise MCInputError("day_universe_missing",
                                   f"{channel}: {day!r} is not an ISO date")
        # duplicates BEFORE ascending — see the docstring's ordering note
        if len(set(seq)) != len(seq):
            raise MCInputError("day_sequence_duplicates", channel)
        if any(b <= a for a, b in zip(seq, seq[1:])):
            raise MCInputError("day_sequence_not_ascending", channel)
        population = frozenset(seq)
        tp = frozenset(str(d) for d in tps[channel])
        outside = sorted(tp - population)
        if outside:
            raise MCInputError(
                "supplement_traded_day_outside_universe",
                f"{channel}: {len(outside)} traded day(s) are absent from "
                f"the declared day universe: {outside[:3]}")
        fp = population - tp
        # Structurally empty given `fp` is a complement — kept EXPLICIT so
        # a future change to the derivation cannot drop the requirement.
        overlap = tp & fp
        if overlap:
            raise MCInputError("tp_fp_overlap",
                               f"{channel}: {sorted(overlap)[:3]}")
        missing_tp = sorted(tp - ref_dates)
        if missing_tp:
            raise MCInputError(
                "tp_day_without_record",
                f"{channel}: {len(missing_tp)} of {len(tp)} tp days lack "
                f"a record: {missing_tp[:3]}")
        missing_fp = sorted(fp - ref_dates)
        if missing_fp:
            raise MCInputError(
                "fp_day_without_record",
                f"{channel}: {len(missing_fp)} of {len(fp)} fp days lack "
                f"a record: {missing_fp[:3]}")
        populations[channel] = population

    # --- §D.2.2 half 3: CROSS_THETA_POPULATION_IDENTITY -------------------
    distinct = {p for p in populations.values()}
    if len(distinct) > 1:
        sizes = {ch: len(p) for ch, p in sorted(populations.items())}
        sample = sorted(set().union(*distinct) - set().intersection(*distinct))
        raise MCInputError(
            "theta_population_drift",
            f"θ channels disagree about the day population {sizes}; "
            f"{len(sample)} day(s) appear in some channels only: "
            f"{sample[:3]}")

    # --- §D.2.2 half 4: the other direction of the union ------------------
    for channel in channels:
        unclassified = sorted(ref_dates - populations[channel])
        if unclassified:
            raise MCInputError(
                "record_without_oracle_class",
                f"{channel}: {len(unclassified)} of {len(ref_dates)} "
                f"record days are in neither tp_days nor fp_days: "
                f"{unclassified[:3]}")

    days = tuple(sorted(next(iter(distinct))))
    return DayUniverseIdentity(day_universe=days, theta_channels=channels,
                               n_days=len(days),
                               day_universe_digest=day_universe_digest(days))


# ---------------------------------------------------------------------------
# The authority: factory-only, unforgeable, bound
# ---------------------------------------------------------------------------

class _AuthorityCapability:
    """Module-private construction capability for `SupplementAuthority`.

    ONE instance, created at import time, passed to exactly one call site
    (`_mint_authority`). `__post_init__` drops it the moment it has been
    checked, so a caller holding a genuine authority cannot read the token
    back out and mint another — and `dataclasses.replace`, which is a
    constructor call carrying `capability=None`, dies at the same gate."""
    __slots__ = ()


_AUTHORITY_CAPABILITY = _AuthorityCapability()

#: Every value-bearing field, in the authority's self-digest preimage.
#: `capability` (dropped) and `authority_digest` (the digest itself) are
#: excluded; `_authority_payload` refuses if this list ever drifts from
#: the dataclass, mirroring `consumer.BATTERY_RECEIPT_COMPONENTS`.
AUTHORITY_PAYLOAD_FIELDS = (
    "schema", "supplement_id", "trial_id", "authorized_commit",
    "method_version", "method_digest", "source_artifact_id",
    "source_artifact_sha256", "test_only", "bundle_table_digest",
    "theta_channels", "day_universe", "day_universe_digest", "n_days",
    "source_input_sha256")


def _authority_payload(authority) -> dict:
    declared = {f.name for f in _dc_fields(authority)} - {
        "capability", "authority_digest"}
    if declared != set(AUTHORITY_PAYLOAD_FIELDS):
        raise SupplementError(
            "supplement_authority_payload_field_drift",
            f"{sorted(declared ^ set(AUTHORITY_PAYLOAD_FIELDS))}")
    payload = {}
    for name in AUTHORITY_PAYLOAD_FIELDS:
        value = getattr(authority, name)
        payload[name] = list(value) if isinstance(value, tuple) else value
    return payload


@dataclass(frozen=True, slots=True)
class SupplementAuthority:
    """TYPED CUSTODY BINDING between a battery-validated `PreparedMCInput`
    and a would-be DAY_STRATA supplement.

    It is a CERTIFICATE, not an input and not a permission: nothing reads
    a field of it as authorization. Every field is a structural fact —
    an identifier, a digest, a date or a count.

    Construction is FACTORY-ONLY. `SupplementAuthority(...)` and
    `dataclasses.replace(authority, ...)` both refuse with
    `supplement_authority_capability_required`; the single minter is
    `_mint_authority`, reachable only through
    `derive_supplement_authority` (production) or
    `derive_supplement_authority_for_tests` (synthetic fixtures)."""
    capability: object
    schema: str
    supplement_id: str
    trial_id: str
    authorized_commit: str
    method_version: str
    method_digest: str
    source_artifact_id: str
    source_artifact_sha256: str
    test_only: bool
    bundle_table_digest: str
    theta_channels: tuple
    day_universe: tuple
    day_universe_digest: str
    n_days: int
    source_input_sha256: str
    authority_digest: str

    def __post_init__(self):
        if self.capability is not _AUTHORITY_CAPABILITY:
            raise SupplementError(
                "supplement_authority_capability_required",
                "a supplement authority is MINTED from a battery-"
                "validated prepared input; it cannot be constructed, "
                "copied or `dataclasses.replace`d by a caller")
        # the token never survives on an instance — see _AuthorityCapability
        object.__setattr__(self, "capability", None)
        if self.schema != SUPPLEMENT_AUTHORITY_SCHEMA:
            raise SupplementError("supplement_authority_schema",
                                  f"schema={self.schema!r}")
        if not isinstance(self.supplement_id, str) or \
                not _sc.SUPPLEMENT_ID_PATTERN.match(self.supplement_id):
            raise SupplementError(
                "supplement_authority_supplement_id_pattern",
                f"{self.supplement_id!r} does not match "
                f"{_sc.SUPPLEMENT_ID_PATTERN.pattern}")
        for name in ("trial_id", "method_version", "source_artifact_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise SupplementError("supplement_authority_malformed",
                                      f"{name}={value!r}")
        if not isinstance(self.authorized_commit, str) or \
                not _sc.HEX40_RE.match(self.authorized_commit):
            raise SupplementError("supplement_authority_commit_malformed",
                                  f"{self.authorized_commit!r} is not 40-hex")
        for name in ("method_digest", "source_artifact_sha256",
                     "bundle_table_digest", "day_universe_digest",
                     "source_input_sha256", "authority_digest"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _sc.HEX64_RE.match(value):
                raise SupplementError("supplement_authority_malformed",
                                      f"{name}={value!r} is not 64-hex")
        if type(self.test_only) is not bool:
            raise SupplementError(
                "supplement_authority_malformed",
                f"test_only carries {type(self.test_only).__name__}")
        channels = self.theta_channels
        if not isinstance(channels, tuple) or not channels or \
                any(not isinstance(c, str) or not c for c in channels) or \
                list(channels) != sorted(channels):
            raise SupplementError("supplement_authority_malformed",
                                  f"theta_channels={channels!r}")
        days = self.day_universe
        if not isinstance(days, tuple) or not days:
            raise SupplementError("supplement_authority_malformed",
                                  f"day_universe={type(days).__name__}")
        for day in days:
            if not isinstance(day, str) or not ISO_DATE_RE.match(day):
                raise SupplementError("supplement_authority_malformed",
                                      f"day_universe carries {day!r}")
        if len(set(days)) != len(days):
            raise SupplementError("supplement_authority_malformed",
                                  "day_universe has duplicate days")
        if list(days) != sorted(days):
            raise SupplementError("supplement_authority_malformed",
                                  "day_universe is not ascending")
        if not isinstance(self.n_days, int) or isinstance(self.n_days, bool) \
                or self.n_days != len(days):
            raise SupplementError("supplement_authority_malformed",
                                  f"n_days={self.n_days!r} vs {len(days)}")
        if day_universe_digest(days) != self.day_universe_digest:
            raise SupplementError(
                "supplement_authority_day_universe_digest_mismatch",
                "the declared day_universe_digest is not the digest of "
                "the declared day universe")
        if _digest(AUTHORITY_DIGEST_SCHEMA,
                   _authority_payload(self)) != self.authority_digest:
            raise SupplementError(
                "supplement_authority_self_digest_mismatch",
                "the declared authority_digest does not describe this "
                "authority's own fields")

    # --- the two things `build_day_strata_supplement_test_only` may be fed --------

    @property
    def expected_day_set(self) -> frozenset:
        """The sealed day universe, as the builder's `expected_day_set`."""
        return frozenset(self.day_universe)

    def supplement_binding(self) -> dict:
        """The builder's `binding`, with EXACTLY
        `day_strata_supplement.BINDING_FIELDS` — the field list is read
        from that module, so a change there refuses here rather than
        producing a binding the builder will reject later."""
        binding = {
            "trial_id": self.trial_id,
            "authorized_commit": self.authorized_commit,
            "day_universe_digest": self.day_universe_digest,
            "method_version": self.method_version,
            "source_input_sha256": self.source_input_sha256,
        }
        if set(binding) != set(_ds.BINDING_FIELDS):
            raise SupplementError(
                "supplement_authority_binding_field_drift",
                f"missing={sorted(set(_ds.BINDING_FIELDS) - set(binding))} "
                f"extra={sorted(set(binding) - set(_ds.BINDING_FIELDS))}")
        return binding


def verify_supplement_binding(binding, prepared, *,
                              identity: DayUniverseIdentity | None = None
                              ) -> dict:
    """EVERY field of a sealed supplement's binding header, checked against
    the prepared input it claims to belong to.

    WHY THIS IS HERE AND NOT AT THE CONSUMER. `verify_supplement_authority`
    already performs exactly this comparison for the authority object, and a
    second consumer writing its own version is how two checks that are meant
    to be the same rule drift apart. The grid-replay authority was doing
    precisely that: it verified rows, day-universe coverage and the
    artifact's own hash, and never asked whether the binding named THIS
    trial, THIS commit or THIS source input -- so a supplement built for a
    different sealed run, whose day universe happened to match and whose
    self-hash had been recomputed, was admitted.

    A RECOMPUTED SELF-HASH PROVES ONLY INTERNAL CONSISTENCY. It says the
    bytes hash to what the artifact claims; it says nothing about whose bytes
    they are. Every check below compares a binding value against a value
    DERIVED from the prepared input, which is the only thing that can.

    `identity` is optional so a caller that has already enforced §D.2.2 does
    not pay for it twice; omitted, it is re-derived here.
    """
    if not isinstance(prepared, _mcc.PreparedMCInput):
        raise SupplementError(
            "supplement_binding_prepared_input_required",
            f"{type(prepared).__name__} is not a PreparedMCInput")
    if not isinstance(binding, Mapping):
        raise SupplementError(
            "supplement_binding_schema",
            f"binding is {type(binding).__name__}, not a mapping")
    missing = set(_ds.BINDING_FIELDS) - set(binding)
    if missing:
        raise SupplementError(
            "supplement_binding_schema",
            f"missing={sorted(missing)} -- the binding must carry every "
            "field the supplement contract defines")
    if identity is None:
        identity = enforce_day_universe_identity(prepared)
    expected = {
        "trial_id": str(prepared.trial_id),
        "authorized_commit": str(prepared.authorized_commit),
        "method_version": SUPPLEMENT_METHOD_VERSION,
        "day_universe_digest": identity.day_universe_digest,
        "source_input_sha256": _source_input_sha256(prepared),
    }
    if set(expected) != set(_ds.BINDING_FIELDS):
        raise SupplementError(
            "supplement_binding_field_drift",
            f"{sorted(set(expected) ^ set(_ds.BINDING_FIELDS))} -- the "
            "contract's field list moved and this check did not")
    for name in _ds.BINDING_FIELDS:
        got, want = binding[name], expected[name]
        if got != want:
            raise SupplementError(
                f"supplement_binding_{name}_mismatch",
                f"the binding declares {str(got)[:64]!r}, this prepared "
                f"input's is {str(want)[:64]!r}")
    return dict(binding)


def _mint_authority(prepared, *, supplement_id: str,
                    identity: DayUniverseIdentity) -> SupplementAuthority:
    """THE only minter. Reached only from the two derivation entries,
    both of which have already verified the battery receipt and enforced
    the §D.2.2 identity."""
    payload = {
        "schema": SUPPLEMENT_AUTHORITY_SCHEMA,
        "supplement_id": str(supplement_id),
        "trial_id": str(prepared.trial_id),
        "authorized_commit": str(prepared.authorized_commit),
        "method_version": SUPPLEMENT_METHOD_VERSION,
        "method_digest": str(prepared.method_digest),
        "source_artifact_id": str(prepared.source_artifact_id),
        "source_artifact_sha256": str(prepared.source_artifact_sha256),
        "test_only": bool(prepared.test_only),
        "bundle_table_digest": bundle_table_digest(prepared.file_sha256),
        "theta_channels": identity.theta_channels,
        "day_universe": identity.day_universe,
        "day_universe_digest": identity.day_universe_digest,
        "n_days": identity.n_days,
        "source_input_sha256": _source_input_sha256(prepared),
    }
    if set(payload) != set(AUTHORITY_PAYLOAD_FIELDS):
        raise SupplementError(
            "supplement_authority_payload_field_drift",
            f"{sorted(set(payload) ^ set(AUTHORITY_PAYLOAD_FIELDS))}")
    preimage = {k: (list(v) if isinstance(v, tuple) else v)
                for k, v in payload.items()}
    return SupplementAuthority(
        capability=_AUTHORITY_CAPABILITY,
        authority_digest=_digest(AUTHORITY_DIGEST_SCHEMA, preimage),
        **payload)


def _derive_impl(prepared, *, supplement_id: str,
                 production: bool) -> SupplementAuthority:
    if not isinstance(prepared, _mcc.PreparedMCInput):
        raise SupplementError(
            "supplement_authority_prepared_input_required",
            f"{type(prepared).__name__} is not a PreparedMCInput")
    if not isinstance(supplement_id, str) or \
            not _sc.SUPPLEMENT_ID_PATTERN.match(supplement_id):
        raise SupplementError(
            "supplement_authority_supplement_id_pattern",
            f"{supplement_id!r} does not match "
            f"{_sc.SUPPLEMENT_ID_PATTERN.pattern}")
    # (1) the entry gate — SPECIFIC first, exactly as the seal boundary
    # orders its own checks, so an honest test artifact at the production
    # entry keeps its own precise code instead of a generic one.
    if production:
        if prepared.test_only:
            raise SupplementError(
                "supplement_authority_test_only_in_production",
                "the prepared input was certified by "
                f"{prepared.source_artifact_id!r} with test_only=True — "
                "the production derivation accepts ONLY the production "
                "attestation's product")
        if prepared.source_artifact_id != _mcc.ATTESTATION_PATH:
            raise SupplementError(
                "supplement_authority_source_violation",
                f"custody source {prepared.source_artifact_id!r} != "
                f"approved {_mcc.ATTESTATION_PATH!r}")
        if prepared.source_artifact_sha256 != _mcc.ATTESTATION_SHA256_PINNED:
            raise SupplementError(
                "supplement_authority_source_digest_violation",
                f"custody source bytes "
                f"{str(prepared.source_artifact_sha256)[:12]} != "
                f"code-pinned {_mcc.ATTESTATION_SHA256_PINNED[:12]}")
    elif not prepared.test_only:
        raise SupplementError(
            "supplement_authority_production_object_in_test_entry",
            "a production prepared input has no entry here; use "
            "derive_supplement_authority")
    # (2) THE FACTORY BOUNDARY — is this the ten-check battery's product,
    # and does it still carry what the battery certified? Consumer's own
    # codes propagate unchanged (`seal_prepared_not_battery_validated` /
    # `seal_battery_receipt_mismatch`): there is ONE truth about that
    # question and it belongs to `consumer.verify_battery_receipt`.
    _mcc.verify_battery_receipt(prepared)
    # (3) §D.2.2, re-derived here rather than inherited.
    identity = enforce_day_universe_identity(prepared)
    return _mint_authority(prepared, supplement_id=supplement_id,
                           identity=identity)


def derive_supplement_authority(
        prepared, *, supplement_id: str = DEFAULT_SUPPLEMENT_ID
) -> SupplementAuthority:
    """PRODUCTION derivation entry.

    Refuses a TEST_ONLY prepared input
    (`supplement_authority_test_only_in_production`), a prepared input
    whose custody source is not the approved attestation path, and one
    whose custody source bytes are not the code-pinned digest — the
    string-comparison half of `consumer._assert_seal_provenance`, done
    without any repository read. Then the battery receipt, then §D.2.2.

    Deriving an authority is NOT supplement authorization; see
    `SUPPLEMENT_AUTHORITY_IS_NOT_AUTHORIZATION`."""
    return _derive_impl(prepared, supplement_id=supplement_id,
                        production=True)


def derive_supplement_authority_for_tests(
        prepared, *, supplement_id: str = DEFAULT_SUPPLEMENT_ID
) -> SupplementAuthority:
    """TEST_ONLY derivation entry, for SYNTHETIC fixtures.

    Accepts ONLY a `test_only=True` prepared input — the mirror of
    `consumer.prepare_mc_input_for_tests`, so the two entries partition
    the world instead of overlapping. Everything after the entry gate is
    IDENTICAL to the production path: the same receipt verification, the
    same identity enforcement, the same minter."""
    return _derive_impl(prepared, supplement_id=supplement_id,
                        production=False)


# ---------------------------------------------------------------------------
# Re-verification: every bound fact, each under its OWN code
# ---------------------------------------------------------------------------

def verify_supplement_authority(
        authority, prepared, *,
        supplement_id: str = DEFAULT_SUPPLEMENT_ID) -> SupplementAuthority:
    """Prove an authority in hand still describes THIS prepared input.

    Every bound fact is recomputed from the live prepared object and
    compared; the authority is never consulted for a value. Each
    difference has its OWN code — a collapsed "authority mismatch" would
    tell an operator nothing about WHICH binding moved. The self-digest
    check is the catch-all UNDERNEATH the specific ones, so it only ever
    reports a field the specific checks do not cover."""
    if type(authority) is not SupplementAuthority:
        raise SupplementError(
            "supplement_authority_required",
            f"{type(authority).__name__} is not a SupplementAuthority")
    if not isinstance(prepared, _mcc.PreparedMCInput):
        raise SupplementError(
            "supplement_authority_prepared_input_required",
            f"{type(prepared).__name__} is not a PreparedMCInput")
    _mcc.verify_battery_receipt(prepared)
    identity = enforce_day_universe_identity(prepared)

    if authority.supplement_id != supplement_id:
        raise SupplementError(
            "supplement_authority_supplement_id_mismatch",
            f"authority binds {authority.supplement_id!r} != "
            f"{supplement_id!r}")
    if authority.method_version != SUPPLEMENT_METHOD_VERSION:
        raise SupplementError(
            "supplement_authority_method_version_mismatch",
            f"authority binds {authority.method_version!r} != frozen "
            f"{SUPPLEMENT_METHOD_VERSION!r}")
    for code, got, want in (
            ("supplement_authority_trial_mismatch",
             authority.trial_id, prepared.trial_id),
            ("supplement_authority_commit_mismatch",
             authority.authorized_commit, prepared.authorized_commit),
            ("supplement_authority_method_digest_mismatch",
             authority.method_digest, prepared.method_digest),
            ("supplement_authority_source_artifact_id_mismatch",
             authority.source_artifact_id, prepared.source_artifact_id),
            ("supplement_authority_source_artifact_sha256_mismatch",
             authority.source_artifact_sha256,
             prepared.source_artifact_sha256),
            ("supplement_authority_bundle_table_mismatch",
             authority.bundle_table_digest,
             bundle_table_digest(prepared.file_sha256)),
            ("supplement_authority_source_input_mismatch",
             authority.source_input_sha256,
             _source_input_sha256(prepared)),
            ("supplement_authority_day_universe_digest_mismatch",
             authority.day_universe_digest, identity.day_universe_digest),
            ("supplement_authority_day_universe_mismatch",
             tuple(authority.day_universe), identity.day_universe),
            ("supplement_authority_theta_channels_mismatch",
             tuple(authority.theta_channels), identity.theta_channels),
            ("supplement_authority_day_count_mismatch",
             authority.n_days, identity.n_days)):
        if got != want:
            raise SupplementError(
                code, f"authority {str(got)[:64]} != prepared "
                      f"{str(want)[:64]}")
    if authority.test_only is not prepared.test_only:
        raise SupplementError(
            "supplement_authority_test_only_mismatch",
            f"authority test_only={authority.test_only} vs prepared "
            f"{prepared.test_only}")
    # N06 ROUND 4, High. Every comparison below asks the AUTHORITY'S OWN
    # values whether they match. A `str` subclass whose `__eq__` returns
    # True answers yes to all of them, and `__new__` +
    # `object.__setattr__` installs one past `__post_init__`'s
    # cross-field check while the type stays exactly right. Measured: a
    # forged authority carrying a 2099 day universe cleared this verifier
    # and all five B_DERIVE gates, and the seal wrote rows dated 2099
    # under a binding digest describing the real 2026 universe
    # (49352d44... declared vs 435fd9b4... actual).
    #
    # Same rule as `freeze_payload` and the builder, third site: exact
    # built-ins only. THE TYPE CHECK IS THE LOAD-BEARING HALF -- removing
    # it fails the round-4 battery. The digest re-derivation below is
    # NOT load-bearing today and no test catches its removal: a
    # plain-string forged universe is already caught by the specific
    # comparisons above. It is kept as a standing invariant so the
    # property survives a refactor of those comparisons, and is
    # deliberately not claimed as a defence.
    for i, day in enumerate(authority.day_universe):
        if type(day) is not str:
            raise SupplementError(
                "supplement_authority_day_universe_type",
                f"day {i} is {type(day).__name__}, not exactly str — a "
                "subclass can carry hostile comparison behaviour")
    if day_universe_digest(tuple(authority.day_universe)) !=             authority.day_universe_digest:
        raise SupplementError(
            "supplement_authority_day_universe_digest_unbacked",
            "the authority's day_universe_digest does not describe the "
            "day universe it carries")

    if authority.schema != SUPPLEMENT_AUTHORITY_SCHEMA:
        raise SupplementError("supplement_authority_schema",
                              f"schema={authority.schema!r}")
    if _digest(AUTHORITY_DIGEST_SCHEMA,
               _authority_payload(authority)) != authority.authority_digest:
        raise SupplementError(
            "supplement_authority_self_digest_mismatch",
            "the authority's own fields no longer hash to the digest it "
            "was minted with")
    return authority


def supplement_build_inputs(authority, prepared, *,
                            supplement_id: str = DEFAULT_SUPPLEMENT_ID):
    """The ONLY sanctioned way to obtain `build_day_strata_supplement_test_only`'s
    `expected_day_set` and `binding`.

    Re-verifies the authority against the prepared input FIRST — binding
    at mint time is not enough, because the object can be carried across
    a process boundary and the two arguments are exactly what decides
    what the supplement is. Returns `(expected_day_set, binding)`.

    Obtaining these is still NOT authorization to build or seal anything;
    see `SUPPLEMENT_AUTHORITY_IS_NOT_AUTHORIZATION`."""
    verify_supplement_authority(authority, prepared,
                                supplement_id=supplement_id)
    return authority.expected_day_set, authority.supplement_binding()
