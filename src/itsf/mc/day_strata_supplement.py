"""GRID Option-B blind supplemental DAY_STRATA sealer (R2.3 lane S2).

MC_DR5_BUILD_PACKET §10.3 Option B: an INDEPENDENTLY ACCOUNTED
reconstruction of the per-day year x vol x event stratum table
(EXACT_PER_DAY_DAY_STRATA — the missing GRID-replay authority identified
by the R2 PHASE D audit: `CAN_GRID_SAMPLES_BE_RECONSTRUCTED_FROM_
CURRENT_SEAL=NO`). The original S0-T001 seal is NEVER touched; the
supplement is a NEW artifact, separately sealed + hashed, bound to the
original run by commit + digests + day-pool cross-check.

DEFAULT-REFUSE TOOLING — NO REAL DATA THIS ROUND. This module ships the
machinery only:

  * `run_supplement_production` (the ONLY production entry) calls
    `authorize_supplement` FIRST and therefore refuses deterministically
    BEFORE any data access — no SUPPLEMENT_EXECUTION_AUTHORIZED
    vocabulary exists in the registry grammar today, mirroring
    `consumer.authorize_real_mc`. Aaron's §10.3 ruling has recommended
    Option B (`GRID_RECOMMENDATION=B_BLIND_SUPPLEMENTAL_DAY_STRATA_SEAL`)
    but recommendation is not authorization: execution waits for a future
    NAMED authorization binding the exact candidate commit, the
    supplement id and the output root.
  * `build_day_strata_supplement_test_only` is the PURE hermetic core (no I/O):
    it validates strata rows against the DR-2/DR-6 ruled vocabularies
    and the already-sealed day universe, and refuses ANY row field
    beyond the four structural ones — the BLIND guarantee that no
    P&L / return / oracle / report value can ever ride along
    (§10.3 Option B: "零 outcome 查看可设计为盲式").
  * `seal_supplement_test_only` writes the artifact with the runinfra `.partial`
    staging discipline (stage, byte-verify, atomic `os.replace`), never
    overwrites a differing final file, and treats stale partials as
    refusals unless byte-identical.

Blind discipline: nothing in this module reads market data, sealed S0
content, or any repository artifact other than `ops/TRIAL_REGISTRY.md`
(and that single read happens only on the production entry, whose very
next call is the deterministic refusal).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable, Mapping, NoReturn, Sequence

from . import supplement_contract as _sc

_REPO_ROOT = Path(__file__).resolve().parents[3]

SUPPLEMENT_ID = "MC-DS-S001"
SUPPLEMENT_SCHEMA = "mc_day_strata_supplement.v1"
SUPPLEMENT_FILENAME = "DAY_STRATA_SUPPLEMENT.json"
# staging suffix mirrors runinfra._ARCHIVE_PARTIAL_SUFFIX: a `.partial`
# is either mid-construction or crash debris, never an artifact of record
PARTIAL_SUFFIX = ".partial"

# frozen: DR-2 (Aaron 2026-08-10) volatility_regime ruled vocabulary —
# vol20 terciles T1/T2/T3 plus the vol_na FOURTH STRATUM (a LABEL, never a
# None; <21 qualifying closes keeps the day, see s0.dataset.VOL_NA_LABEL).
VOL_STRATA = ("T1", "T2", "T3", "vol_na")
# frozen: DR-6 / IR-12/18 event vocabulary — exclusive per-day classes;
# multi-category days map to NA_multi_event, NO DAY IS EVER DROPPED
# (see s0.dataset.EVENT_STRATUM_NA_MULTI, s0.context exclusive counts).
EVENT_STRATA = ("CPI", "FOMC", "NFP", "NA_multi_event", "none")

# The EXACT structural row schema. This tuple IS the no-outcome
# guarantee: build/seal refuse any key beyond these four, so an outcome
# field (pnl, return, oracle flag, report note, ...) can never enter the
# supplement even by accident.
ROW_FIELDS = ("trade_date", "year", "vol_stratum", "event_stratum")

# The EXACT binding schema: ties the supplement to the sealed S0-T001
# run (commit + day-universe digest + method + source-input digest).
BINDING_FIELDS = ("trial_id", "authorized_commit", "day_universe_digest",
                  "method_version", "source_input_sha256")

# future registry vocabulary — does NOT exist in the grammar today
SUPPLEMENT_AUTHORIZATION_EVENT = "SUPPLEMENT_EXECUTION_AUTHORIZED"

# Anchored with \\Z, not $ — Python's $ also matches before a
# trailing newline. The N06 repair round swept this class in
# `supplement_contract` and `supplement_runner` and CLAIMED to have swept
# the class; it had not — these three were missed, and a fresh Sol N06
# review found them. The claim was the defect, not just the anchors.
_HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}\Z")


class SupplementError(ValueError):
    """Fail-closed refusal from the supplement battery. `code` is the
    machine-readable refusal reason (mirrors consumer.MCInputError)."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


class SupplementNotAuthorized(RuntimeError):
    """No supplement-execution authorization exists in the registry
    vocabulary (mirrors consumer.MCNotAuthorized)."""


# ---------------------------------------------------------------------------
# Authorization gate (default refuse; no vocabulary exists yet)
# ---------------------------------------------------------------------------

def authorize_supplement(registry_text: str) -> NoReturn:
    """Deterministic refusal today: the registry vocabulary contains no
    SUPPLEMENT_EXECUTION_AUTHORIZED event type, and this gate does NOT
    best-effort parse one into existence (mirror of
    consumer.authorize_real_mc). A lookalike token planted in the
    registry text is NAMED in the refusal and refused all the same —
    only a future reviewed registry-grammar extension counts."""
    lookalike = SUPPLEMENT_AUTHORIZATION_EVENT in (registry_text or "")
    raise SupplementNotAuthorized(
        "DAY_STRATA supplemental reconstruction remains NOT authorized: "
        f"the registry grammar has no {SUPPLEMENT_AUTHORIZATION_EVENT} "
        "vocabulary"
        + ((" (a lookalike "
            f"{SUPPLEMENT_AUTHORIZATION_EVENT} token appears in the "
            "registry text but no parser/grammar accepts it — refusal "
            "stands)") if lookalike else "")
        + "; execution requires a FUTURE named authorization event that "
          "binds the EXACT candidate commit + supplement id "
          f"{SUPPLEMENT_ID} + the output root (§10.3 Option B — Aaron "
          "must gate the structural data access explicitly)")


def run_supplement_production(*_a, **_k) -> NoReturn:
    """PRODUCTION entry for the Option-B supplemental reconstruction.

    Gate-first (mirrors real_input.prepare_real_mc_input discipline):
    reads ops/TRIAL_REGISTRY.md — the ONLY repository read this module
    ever performs — and calls `authorize_supplement` immediately, so the
    deterministic refusal fires BEFORE any Development-data access, any
    output-root creation, or any registry event. Everything after the
    gate is unreachable until the vocabulary exists."""
    # Invariant 5 of dec-registry-migration-2026-08-27 — one construction
    # site, and absence now refuses instead of reading as empty.
    from .registry_boundary import read_snapshot
    authorize_supplement(read_snapshot().text)
    raise AssertionError("unreachable: authorize_supplement always raises")


# ---------------------------------------------------------------------------
# Canonical serialisation (single authority for every digest in here)
# ---------------------------------------------------------------------------

def canonical_json(obj) -> str:
    """THE canonical JSON form: sorted keys, compact separators, ASCII,
    NaN/Infinity rejected. Every digest this module computes or verifies
    uses exactly this.

    `allow_nan=False` ADDED 2026-08-28 under Aaron's authorization. Without
    it this function emitted `{"x":NaN}` — not valid JSON — while
    `atoms.canonical_json` and `cold_reducer._canonical`, the two functions
    N09 R3 §5 called identical to it, raised. It feeds
    `canonical_rows_digest`, so a digest could have been taken over bytes
    that are not JSON, and a cold reader recomputing with either of the
    other two would have raised rather than disagreed.

    R3 §5 had declared the duplication out of its scope — "R3 不修它" — on
    the stated premise that the three were 同体. They were not, so that
    premise was false and Aaron voided the scope statement rather than the
    finding. Measured before changing anything: zero sealed supplements
    exist (no P4 event, no supplement bytes, no subtree), so no existing
    digest could be invalidated; and no supplement row field is a float, so
    no reachable input changes behaviour."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def canonical_rows_digest(rows: Iterable[Mapping]) -> str:
    """sha256 over the canonical JSON of the row list (rows are assumed
    already validated + sorted — `build_day_strata_supplement_test_only` is the
    one production caller; exposed so tests can recompute honestly)."""
    payload = [dict(r) for r in rows]
    return hashlib.sha256(
        canonical_json(payload).encode("utf-8")).hexdigest()


def canonical_supplement_bytes(supplement: Mapping) -> bytes:
    """The exact bytes `seal_supplement_test_only` intends to write."""
    payload = dict(supplement)
    payload["rows"] = [dict(r) for r in payload["rows"]]
    payload["binding"] = dict(payload["binding"])
    return canonical_json(payload).encode("utf-8")


# ---------------------------------------------------------------------------
# Pure hermetic core (no I/O)
# ---------------------------------------------------------------------------

def _validate_binding(binding: Mapping) -> dict:
    if not isinstance(binding, Mapping):
        raise SupplementError("supplement_binding_schema",
                              f"binding is {type(binding).__name__}, "
                              "not a mapping")
    got = set(binding)
    want = set(BINDING_FIELDS)
    if got != want:
        raise SupplementError(
            "supplement_binding_schema",
            f"missing={sorted(want - got)} extra={sorted(got - want)}")
    for key in ("trial_id", "method_version"):
        val = binding[key]
        if not isinstance(val, str) or not val:
            raise SupplementError("supplement_binding_malformed",
                                  f"{key}: empty or non-string")
    commit = binding["authorized_commit"]
    if not isinstance(commit, str) or not _HEX40.match(commit):
        raise SupplementError("supplement_binding_malformed",
                              "authorized_commit is not 40-hex")
    for key in ("day_universe_digest", "source_input_sha256"):
        val = binding[key]
        if not isinstance(val, str) or not _HEX64.match(val):
            raise SupplementError("supplement_binding_malformed",
                                  f"{key} is not 64-hex")
    return dict(binding)


def _validate_row(row, i: int) -> dict:
    """One row of the structural DAY_STRATA table. Field-set exactness is
    checked FORBIDDEN-FIRST: an extra key is the blind-guarantee
    violation (an outcome field riding along), distinct from a merely
    incomplete row."""
    if not isinstance(row, Mapping):
        raise SupplementError("supplement_row_schema",
                              f"row {i}: {type(row).__name__} is not a "
                              "mapping")
    got = set(row)
    want = set(ROW_FIELDS)
    extra = sorted(got - want)
    if extra:
        raise SupplementError(
            "supplement_forbidden_field",
            f"row {i}: {extra} — DAY_STRATA rows carry the four "
            "structural keys ONLY; outcome/P&L/oracle/report fields can "
            "never ride along (blind guarantee)")
    missing = sorted(want - got)
    if missing:
        raise SupplementError("supplement_row_schema",
                              f"row {i}: missing={missing}")
    date = row["trade_date"]
    if not isinstance(date, str) or not _ISO_DATE.match(date):
        raise SupplementError("supplement_row_schema",
                              f"row {i}: trade_date {date!r} is not ISO "
                              "YYYY-MM-DD")
    year = row["year"]
    if isinstance(year, bool) or not isinstance(year, int) or \
            year != int(date[:4]):
        raise SupplementError("supplement_year_mismatch",
                              f"row {i}: year={year!r} vs trade_date "
                              f"{date}")
    if row["vol_stratum"] not in VOL_STRATA:
        raise SupplementError(
            "supplement_vol_vocabulary",
            f"row {i}: {row['vol_stratum']!r} not in DR-2 ruled set "
            f"{VOL_STRATA}")
    if row["event_stratum"] not in EVENT_STRATA:
        raise SupplementError(
            "supplement_event_vocabulary",
            f"row {i}: {row['event_stratum']!r} not in DR-6/IR-12/18 "
            f"ruled set {EVENT_STRATA}")
    return {"trade_date": date, "year": int(year),
            "vol_stratum": str(row["vol_stratum"]),
            "event_stratum": str(row["event_stratum"])}


def build_day_strata_supplement_test_only(day_rows: Sequence[Mapping], *,
                                          expected_day_set: frozenset,
                                          binding: Mapping,
                                          supplement_id: str = SUPPLEMENT_ID
                                          ) -> dict:
    """TEST_ONLY hermetic supplement builder (no I/O; deterministic).

    RENAMED at the N06 repair. This function takes the two arguments
    that DECIDE what a supplement is from its caller, so anything it
    returns is unbound to the sealed S0 input. The production path is
    `supplement_production.build_supplement_from_authority`, which
    derives both arguments from a `SupplementAuthority` and mints a
    receipt the production seal requires. A payload from HERE carries
    no receipt and cannot reach that seal.

    Validates every row against the DR-2/DR-6 ruled vocabularies and the
    ALREADY-SEALED day universe (`expected_day_set`, a frozenset carried
    over from the S0 authority): the reconstructed table must cover that
    universe EXACTLY — a missing day and an invented day are separate
    refusals, and a day can appear only once. Rows are defensively
    copied (a caller mutating its input after build has zero effect) and
    emitted SORTED by trade_date so the digest is order-independent of
    the input.

    Same input -> same `rows_digest`, byte for byte."""
    bound = _validate_binding(binding)
    if not isinstance(expected_day_set, frozenset):
        raise SupplementError(
            "supplement_day_set_authority",
            f"expected_day_set is {type(expected_day_set).__name__} — "
            "the sealed day universe must arrive as a frozenset")
    rows: dict[str, dict] = {}
    for i, raw in enumerate(day_rows):
        row = _validate_row(raw, i)
        date = row["trade_date"]
        if date in rows:
            raise SupplementError("supplement_duplicate_day", date)
        rows[date] = row
    got_days = frozenset(rows)
    missing = sorted(expected_day_set - got_days)
    if missing:
        raise SupplementError(
            "supplement_day_set_incomplete",
            f"{len(missing)} sealed day(s) absent: {missing[:3]}")
    extra = sorted(got_days - expected_day_set)
    if extra:
        raise SupplementError(
            "supplement_day_set_extra",
            f"{len(extra)} day(s) outside the sealed universe: "
            f"{extra[:3]}")
    ordered = tuple(rows[d] for d in sorted(rows))
    # Before this function took the id it could only ever stamp the module
    # constant. Accepting an arbitrary string would be a widening, not a
    # repair -- a malformed id must not reach a sealed artifact.
    if not _sc.SUPPLEMENT_ID_PATTERN.match(supplement_id or ""):
        raise SupplementError("supplement_id_pattern", repr(supplement_id))
    return {
        "schema": SUPPLEMENT_SCHEMA,
        "supplement_id": supplement_id,
        "binding": bound,
        "rows": ordered,
        "n_rows": len(ordered),
        "rows_digest": canonical_rows_digest(ordered),
    }


# ---------------------------------------------------------------------------
# Sealing (.partial staging; runinfra Codex-final-review-#5 discipline)
# ---------------------------------------------------------------------------

_SUPPLEMENT_FIELDS = ("schema", "supplement_id", "binding", "rows",
                      "n_rows", "rows_digest")


def _validate_supplement_object(
        supplement: Mapping, *,
        expected_supplement_id: str = SUPPLEMENT_ID) -> None:
    """Seal-side re-validation: the object must be a well-formed
    supplement whose declared digest matches its own rows (a declared
    statistic never travels unverified — consumer R2.2 PHASE C
    discipline). Row field-set exactness is re-checked here too, so the
    blind no-outcome guarantee holds at the seal boundary as well."""
    if not isinstance(supplement, Mapping) or \
            set(supplement) != set(_SUPPLEMENT_FIELDS):
        raise SupplementError("supplement_object_schema",
                              "not a mapping with the exact supplement "
                              f"field set {_SUPPLEMENT_FIELDS}")
    if supplement["schema"] != SUPPLEMENT_SCHEMA or \
            supplement["supplement_id"] != expected_supplement_id:
        raise SupplementError(
            "supplement_object_schema",
            f"schema={supplement['schema']!r} "
            f"id={supplement['supplement_id']!r}")
    _validate_binding(supplement["binding"])
    rows = supplement["rows"]
    checked = [_validate_row(r, i) for i, r in enumerate(rows)]
    if supplement["n_rows"] != len(checked):
        raise SupplementError("supplement_object_schema",
                              f"n_rows={supplement['n_rows']!r} vs "
                              f"{len(checked)} rows")
    want = canonical_rows_digest(checked)
    if supplement["rows_digest"] != want:
        raise SupplementError(
            "supplement_digest_mismatch",
            f"declared {str(supplement['rows_digest'])[:12]} != "
            f"recomputed {want[:12]}")


def seal_supplement_test_only(supplement: Mapping, out_dir: Path) -> str:
    """Seal the supplement as ``<out_dir>/DAY_STRATA_SUPPLEMENT.json``
    (canonical JSON, sorted keys, utf-8) and return the sha256 of the
    sealed bytes.

    `.partial` staging (runinfra archive discipline, Codex final review
    #5): bytes land in ``<name>.partial`` first, are RE-READ and
    byte-compared against the intent, and only then promoted with a
    single atomic `os.replace`. A crash therefore never leaves a half-
    written file at the final name. A leftover `.partial` from a crashed
    prior attempt is DETECTED: byte-identical residue is simply promoted
    (the crash happened between verify and replace), anything else
    refuses with ``supplement_partial_residue`` — debris is disclosed,
    never silently clobbered.

    A final file is NEVER overwritten with different bytes
    (``supplement_seal_conflict``); re-sealing identical bytes is an
    idempotent no-op. This is the anti-tamper backstop: a synchronized
    row+digest rewrite produces internally consistent DIFFERENT bytes,
    and those bytes cannot replace an existing seal.

    Archive mirroring is deliberately NOT implemented here: at real
    execution time the sealed directory is mirrored by the existing
    `itsf.s0.runinfra.archive_sealed_run` machinery (L-5 ruling), which
    already owns inventory equality + per-file recheck."""
    # Validated against the payload's OWN id: this entry seals whatever
    # object it was handed, and binding that id to the authority is
    # `production_supplement_id_divergence`'s job upstream. Comparing to
    # the module constant here would re-impose "everything is
    # MC-DS-S001" at the last step.
    _validate_supplement_object(
        supplement,
        expected_supplement_id=str(supplement.get("supplement_id", "")))
    intended = canonical_supplement_bytes(supplement)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    final = out / SUPPLEMENT_FILENAME
    partial = out / (SUPPLEMENT_FILENAME + PARTIAL_SUFFIX)

    if final.exists():
        existing = final.read_bytes()
        if existing == intended:
            # idempotent reseal — byte-identical, nothing to write
            return hashlib.sha256(existing).hexdigest()
        raise SupplementError(
            "supplement_seal_conflict",
            f"{final.name} already sealed with DIFFERENT bytes "
            f"(existing sha {hashlib.sha256(existing).hexdigest()[:12]} "
            f"!= intended {hashlib.sha256(intended).hexdigest()[:12]}) — "
            "a sealed supplement is never overwritten")

    if partial.exists():
        residue = partial.read_bytes()
        if residue != intended:
            raise SupplementError(
                "supplement_partial_residue",
                f"stale {partial.name} from a crashed prior attempt "
                "does not match the intended bytes — refusing to reuse "
                "or silently clobber debris")
        # byte-identical residue: the prior attempt crashed after the
        # verified write — promotion below completes it.
    else:
        partial.write_bytes(intended)

    reread = partial.read_bytes()
    if reread != intended:
        try:
            partial.unlink()
        except OSError:
            pass
        raise SupplementError("supplement_partial_verify",
                              "staged bytes re-read differently than "
                              "written")
    os.replace(partial, final)
    sealed = final.read_bytes()
    if sealed != intended:
        raise SupplementError("supplement_partial_verify",
                              "post-promotion re-read diverged from the "
                              "verified staging bytes")
    return hashlib.sha256(sealed).hexdigest()
