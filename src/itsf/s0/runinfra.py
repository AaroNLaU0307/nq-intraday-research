"""S0 run-governance infrastructure (SA-5, M5-T2).

Implements the run-time governance mechanisms authorized by
S0_REAL_RUN_AUTHORIZATION_PACKET.md sections 6/7/8:
  - a JSONL hash-chain manifest (append-only, tamper-evident),
  - the Stage-C log-leak guard (whitelist schema + vocabulary/float blacklist),
  - the NA-conservation checker,
  - the expected-vs-actual preflight assertion comparator,
  - RUN_FAILURE_REPORT / PRE_RUN_ATTEMPT_FAILURE rendering + writing.

This module implements MECHANISM only. Deciding *when* to call these
functions, and all TRIAL_REGISTRY.md state transitions, belong to the
main-agent runner entrypoint (scripts/s0_real_run.py, M5-T3) — never here.

Architecture (Aaron 2026-07-31 erratum, frozen for this task):
  Pure logic layer (zero I/O, zero global state, fully unit-testable):
      canonicalize_manifest_record, compute_record_hash,
      verify_chain_records, validate_log_event, check_na_conservation,
      translate_na_reason, translate_preflight_assertions,
      compare_preflight_assertions, render_failure_report,
      validate_output_roots
  Narrow I/O adapter layer:
      append_manifest_record(path, record)
      write_failure_report(directory, rendered)
      archive_sealed_run(runs_dir, archive_root)      # L-5 ruling, S3/M6.1.9

  L-5 ruling (Aaron 2026-08-10, S3/M6.1.9): the repo lives inside an
  actively-syncing OneDrive tree, which is incompatible with the M6.1.7
  exact-set disk invariant (a sync dropping such as `desktop.ini` is an
  undeclared file, which is a seal refusal, which burns a trial). The
  ruling moves the governed output roots to dedicated LOCAL, non-synced
  directories (`contracts.RULED_RUNS_ROOT` / `RULED_ARCHIVE_ROOT`).
  `validate_output_roots` is the fail-closed structural gate that enforces
  the new roots are disjoint from the repo tree and from each other, and
  that `RunConfig.runs_dir`/`attempts_dir` resolve under `RunConfig.
  runs_root`; `archive_sealed_run` is the post-seal narrow I/O step that
  copies a completed run directory into the archive root and independently
  re-verifies every file's bytes by SHA-256 on both sides after the copy.
  Neither function creates or touches an attempt/run root directory's
  CONTENTS — `validate_output_roots` performs no I/O beyond path
  resolution, and `archive_sealed_run` only ever READS `runs_dir` (never
  writes into it) while writing exclusively under `archive_root`.

Hard constraints honored throughout this module:
  - zero real-data access; zero network access;
  - never creates an attempt/run root directory (directory lifecycle is the
    main runner's responsibility) — the two I/O functions write only inside
    a directory the caller already created, and raise FileNotFoundError if
    it does not exist;
  - never reads S0_INPUT_PREFLIGHT.json — expected/actual assertion values
    are always supplied by the caller (compare_preflight_assertions is a
    pure two-argument comparator; see its docstring for the exact 2026-07-31
    ruling this encodes);
  - only imports from itsf.contracts (RunStage, TrialState,
    APPROVED_NA_REASONS, RunConfig, RunGateError, NAConservationError,
    AssertionMismatchError, LogLeakError) — no other project module.

Known deviation from the literal task text, flagged for main-agent review
(see the SA-5 return report's `unresolved` field for the full writeup):
the task prose says the Stage-C forbidden-vocabulary table should "live in
contracts.py, referenced [from here]". contracts.py is import-only for this
task (no such constant exists there today, and modifying contracts.py is
out of file-ownership scope for SA-5). The vocabulary is therefore defined
locally below as `_FORBIDDEN_VOCAB`, using exactly the word categories the
task prose enumerates (Oracle/label/E1/E2/annual/frequency/distribution),
plus close synonyms. It is written so a future main-agent edit can hoist it
into contracts.py verbatim without changing this module's public behavior.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from itsf.contracts import (
    APPROVED_NA_REASONS,
    AssertionMismatchError,
    InputDataDefectError,
    LogLeakError,
    NAConservationError,
    RunConfig,
    RunGateError,
    RunStage,
    TrialState,
)

# --- module-local exceptions -------------------------------------------
# Reserved strictly for manifest-schema/canonicalization violations, kept
# distinct from the four contracts.py error types (whose exact semantics
# are documented there and must not be repurposed for a mismatched concern).


class ManifestIntegrityError(ValueError):
    """A manifest record fails schema, path, or hash-chain validation."""


# --- shared constants -----------------------------------------------------

GENESIS_PREVIOUS_HASH = "0" * 64

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

_STAGE_VALUES: tuple[str, ...] = tuple(s.value for s in RunStage)
_STAGE_ORDER: dict[str, int] = {s.value: i for i, s in enumerate(RunStage)}

_FILE_REQUIRED_KEYS = frozenset(
    {"record_type", "stage", "relative_path", "file_sha256", "previous_record_hash"}
)
_SEAL_REQUIRED_KEYS = frozenset(
    {"record_type", "stage", "sealed_record_hash", "previous_record_hash"}
)


# =========================================================================
# 0. Output-root governance (L-5 ruling, 2026-08-10) — pure logic
# =========================================================================
#
# The repo lives inside an actively-syncing OneDrive tree. The M6.1.7
# exact-set disk invariant (a run directory's contents must EQUAL its
# declared set, or the run is refused as sealed) makes any sync-tool
# dropping — `desktop.ini`, a `*.tmp` file, a sync client's own
# subdirectory — an automatic `disk_extra_file` refusal that burns a
# trial. Aaron's ruling is to move the governed output roots OUT of the
# repo tree entirely, to dedicated local, non-synced directories
# (`contracts.RULED_RUNS_ROOT` / `RULED_ARCHIVE_ROOT`), rather than widen
# the exact-set invariant with a whitelist (a whitelist would weaken the
# "declared set == disk contents" invariant the M6.1.7 closeout exists to
# guarantee). `validate_output_roots` is the fail-closed structural gate
# that enforces the new roots are actually disjoint from the repo tree
# and from each other.


def _disjoint(a: Path, b: Path) -> bool:
    """True iff neither RESOLVED path is an ancestor of (or equal to) the
    other. Two equal paths are NOT disjoint (each is trivially a "subpath"
    of the other), so this also catches the `a == b` case without a
    separate comparison."""
    return not (a.is_relative_to(b) or b.is_relative_to(a))


def _strictly_under(child: Path, ancestor: Path) -> bool:
    """True iff RESOLVED `child` is a PROPER descendant of RESOLVED
    `ancestor` — i.e. under it, but not equal to it."""
    return child != ancestor and child.is_relative_to(ancestor)


def _absolute_path_field(cfg_value: object, field_name: str) -> Path:
    """`RunConfig` fields are typed `str` but nothing enforces that at
    runtime (a plain frozen dataclass performs no field validation), so
    every value this gate reads is re-checked here before use: must be a
    non-empty `str`, and must be an absolute path. Raises RunGateError
    (never a bare TypeError/ValueError) on any defect, matching the
    fail-closed contract of the rest of this gate."""
    if not isinstance(cfg_value, str) or not cfg_value:
        raise RunGateError(
            f"validate_output_roots: RunConfig.{field_name} must be a "
            f"non-empty str, got {cfg_value!r}"
        )
    p = Path(cfg_value)
    if not p.is_absolute():
        raise RunGateError(
            f"validate_output_roots: RunConfig.{field_name} must be an "
            f"absolute path, got {cfg_value!r}"
        )
    return p


def validate_output_roots(cfg: RunConfig, repo_root: Path) -> None:
    """Fail-closed (L-5 ruling) gate over the FOUR governed output paths
    on `cfg`: `runs_root`, `archive_root`, `runs_dir`, `attempts_dir`.

    Raises `RunGateError` unless ALL of the following hold (checked in
    this order, so the FIRST violation found is the one reported):

      1. `cfg.runs_root` and `cfg.archive_root` are each a non-empty,
         ABSOLUTE path string;
      2. `repo_root` is an absolute path (a defensive check on the
         caller — the runner derives it from its own on-disk location,
         never from a literal, so this should never fire in practice);
      3. `cfg.runs_root` is fully DISJOINT from `repo_root` — neither is
         an ancestor of, nor equal to, the other. Same for
         `cfg.archive_root`. This is the L-5 ruling's central invariant:
         a governed output root living inside the actively-syncing repo
         tree (or the repo tree living inside one, e.g. a mistakenly
         inverted config) is exactly the defect being closed;
      4. `cfg.runs_root` and `cfg.archive_root` are themselves fully
         DISJOINT from EACH OTHER (equal, or one nested inside the
         other, are both refused);
      5. `cfg.runs_dir` and `cfg.attempts_dir` are each a non-empty,
         absolute path string that resolves STRICTLY under (a proper
         descendant of, never equal to) `cfg.runs_root`.

    Pure path arithmetic: `Path.resolve()` WITHOUT `strict=True`, so this
    works correctly before any directory in the chain has been created
    (the ruled roots are provisioned lazily, on first real use, not by
    this gate) — the gate never touches the filesystem beyond whatever
    symlink-normalisation `resolve()` itself performs, and it never
    creates, deletes or lists a directory.

    This function RAISES on failure (never returns a `(bool, str)`
    tuple) — it is a hard invariant checker in the same family as
    `check_na_conservation`'s underlying arithmetic, not a `GateCheck`
    predicate. A caller that needs the `(ok, detail)` shape (the runner's
    Stage-A gate battery) wraps this call; see `runner.py`.
    """
    if not isinstance(cfg, RunConfig):
        raise RunGateError(
            "validate_output_roots: cfg must be a RunConfig instance, got "
            f"{type(cfg).__name__}"
        )
    if not isinstance(repo_root, Path):
        raise RunGateError(
            "validate_output_roots: repo_root must be a pathlib.Path "
            f"instance, got {type(repo_root).__name__}"
        )
    if not repo_root.is_absolute():
        raise RunGateError(
            f"validate_output_roots: repo_root must be an absolute path, "
            f"got {repo_root}"
        )

    runs_root_p = _absolute_path_field(cfg.runs_root, "runs_root")
    archive_root_p = _absolute_path_field(cfg.archive_root, "archive_root")

    repo_root_r = repo_root.resolve()
    runs_root_r = runs_root_p.resolve()
    archive_root_r = archive_root_p.resolve()

    if not _disjoint(runs_root_r, repo_root_r):
        raise RunGateError(
            f"validate_output_roots: runs_root ({runs_root_r}) and the "
            f"repo tree ({repo_root_r}) must be fully disjoint (L-5 "
            f"ruling) — one contains, or equals, the other"
        )
    if not _disjoint(archive_root_r, repo_root_r):
        raise RunGateError(
            f"validate_output_roots: archive_root ({archive_root_r}) and "
            f"the repo tree ({repo_root_r}) must be fully disjoint (L-5 "
            f"ruling) — one contains, or equals, the other"
        )
    if not _disjoint(runs_root_r, archive_root_r):
        raise RunGateError(
            f"validate_output_roots: runs_root ({runs_root_r}) and "
            f"archive_root ({archive_root_r}) must be fully disjoint — "
            f"one contains, or equals, the other"
        )

    runs_dir_p = _absolute_path_field(cfg.runs_dir, "runs_dir")
    attempts_dir_p = _absolute_path_field(cfg.attempts_dir, "attempts_dir")
    runs_dir_r = runs_dir_p.resolve()
    attempts_dir_r = attempts_dir_p.resolve()

    if not _strictly_under(runs_dir_r, runs_root_r):
        raise RunGateError(
            f"validate_output_roots: runs_dir ({runs_dir_r}) does not "
            f"resolve strictly under runs_root ({runs_root_r})"
        )
    if not _strictly_under(attempts_dir_r, runs_root_r):
        raise RunGateError(
            f"validate_output_roots: attempts_dir ({attempts_dir_r}) does "
            f"not resolve strictly under runs_root ({runs_root_r})"
        )


# =========================================================================
# 1. JSONL hash-chain manifest — pure logic
# =========================================================================


def _validate_relative_path(path: object, manifest_relative_path: str) -> None:
    if not isinstance(path, str) or not path:
        raise ManifestIntegrityError(f"relative_path must be a non-empty string: {path!r}")
    if "\\" in path:
        raise ManifestIntegrityError(
            f"relative_path must use POSIX '/' separators, not backslashes: {path!r}"
        )
    if path.startswith("/"):
        raise ManifestIntegrityError(f"relative_path must not be absolute: {path!r}")
    if re.match(r"^[A-Za-z]:", path):
        raise ManifestIntegrityError(
            f"relative_path must not be a drive-absolute Windows path: {path!r}"
        )
    segments = path.split("/")
    if any(seg in ("", ".", "..") for seg in segments):
        raise ManifestIntegrityError(
            f"relative_path must not contain '.', '..', or empty segments "
            f"(no path traversal): {path!r}"
        )
    if path == manifest_relative_path:
        raise ManifestIntegrityError(
            f"relative_path must not self-reference the manifest file itself "
            f"(manifest_self_excluded): {path!r}"
        )


def canonicalize_manifest_record(
    record: Mapping[str, object],
    *,
    manifest_relative_path: str = "manifest.jsonl",
) -> str:
    """Validate `record` against the frozen per-record schema and return its
    canonical JSON serialization (UTF-8, sort_keys=True, compact separators,
    no `record_hash` field — the hash is computed *over* this canonical form,
    so it can never include itself).

    `record` must contain EXACTLY the keys for its `record_type` (no more,
    no fewer): `file` records carry {record_type, stage, relative_path,
    file_sha256, previous_record_hash}; `stage_seal` records carry
    {record_type, stage, sealed_record_hash, previous_record_hash}.
    Raises ManifestIntegrityError on any schema, path, or hash-format
    violation. Zero I/O; deterministic; safe to call from tests directly.
    """
    if not isinstance(record, Mapping):
        raise ManifestIntegrityError("record must be a mapping")

    record_type = record.get("record_type")
    if record_type not in ("file", "stage_seal"):
        raise ManifestIntegrityError(
            f"record_type must be 'file' or 'stage_seal', got {record_type!r}"
        )

    required = _FILE_REQUIRED_KEYS if record_type == "file" else _SEAL_REQUIRED_KEYS
    keys = set(record.keys())
    if keys != required:
        missing = sorted(required - keys)
        extra = sorted(keys - required)
        raise ManifestIntegrityError(
            f"{record_type} record has the wrong keys; missing={missing} extra={extra}"
        )

    stage = record["stage"]
    if stage not in _STAGE_VALUES:
        raise ManifestIntegrityError(f"unknown stage: {stage!r}")

    prev = record["previous_record_hash"]
    if not isinstance(prev, str) or not _HEX64_RE.match(prev):
        raise ManifestIntegrityError(
            f"previous_record_hash must be 64 lowercase hex chars: {prev!r}"
        )

    if record_type == "file":
        _validate_relative_path(record["relative_path"], manifest_relative_path)
        file_sha256 = record["file_sha256"]
        if not isinstance(file_sha256, str) or not _HEX64_RE.match(file_sha256):
            raise ManifestIntegrityError(
                f"file_sha256 must be 64 lowercase hex chars: {file_sha256!r}"
            )
    else:
        sealed_hash = record["sealed_record_hash"]
        if not isinstance(sealed_hash, str) or not _HEX64_RE.match(sealed_hash):
            raise ManifestIntegrityError(
                f"sealed_record_hash must be 64 lowercase hex chars: {sealed_hash!r}"
            )

    payload = {k: record[k] for k in required}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_record_hash(canonical_json: str) -> str:
    """SHA-256 hex digest of a canonical-JSON string (UTF-8 bytes). Pure."""
    if not isinstance(canonical_json, str):
        raise ManifestIntegrityError("canonical_json must be a str")
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChainVerificationResult:
    """Full-chain audit verdict. `valid` is False if ANY record fails any
    check — order, previous-hash linkage, record_hash recomputation, stage
    progression/seal discipline, or (if `file_hash_provider` was supplied)
    the recorded file_sha256 against the caller-provided actual hash."""

    valid: bool
    n_records: int
    errors: tuple[str, ...]
    sealed_stages: tuple[str, ...]
    last_record_hash: str | None


def verify_chain_records(
    records: Sequence[Mapping[str, object]],
    *,
    manifest_relative_path: str = "manifest.jsonl",
    file_hash_provider: Callable[[str], str] | None = None,
) -> ChainVerificationResult:
    """Replay and verify an already-parsed sequence of manifest records
    (e.g. the caller `json.loads`-ed each JSONL line). Performs NO file
    I/O itself — `file_hash_provider`, if given, is a caller-supplied pure
    lookup (e.g. an in-memory dict-backed function in tests) used only to
    cross-check a `file` record's declared file_sha256; runinfra never
    reads real files to obtain it.

    Checks, in order, per record: genesis / previous-hash chain linkage,
    record_hash recomputation (tamper detection), stage monotonic
    progression, stage_seal cannot reopen a sealed stage, a stage_seal's
    `sealed_record_hash` must equal its own `previous_record_hash` (which,
    by append-only construction, is exactly the last record of that stage),
    and (optionally) the file hash cross-check.

    Seal discipline (SA-6 F-26, packet §6 "每阶段结束写入 stage seal 记录"):
    every stage that appears in the chain must carry BOTH at least one
    non-seal (`file`) record AND exactly one `stage_seal`. An unsealed stage
    (records written, seal never appended — e.g. the process died mid-stage)
    and an empty seal (a `stage_seal` for a stage that contributed no
    records) are both chain-invalid, so a truncated tail can no longer read
    as a complete chain.
    """
    errors: list[str] = []
    sealed_stage_idx: set[int] = set()
    sealed_stage_values: list[str] = []
    file_records_per_stage: dict[str, int] = {}
    stages_seen: list[str] = []
    last_stage_idx = -1
    prev_hash_expected = GENESIS_PREVIOUS_HASH
    last_hash: str | None = None

    for i, raw in enumerate(records):
        if not isinstance(raw, Mapping):
            errors.append(f"[{i}] record is not a mapping: {raw!r}")
            continue

        stored_hash = raw.get("record_hash")
        if not isinstance(stored_hash, str) or not _HEX64_RE.match(stored_hash):
            errors.append(f"[{i}] missing or malformed record_hash")

        payload = {k: v for k, v in raw.items() if k not in ("record_hash", "finalized")}
        try:
            canonical = canonicalize_manifest_record(
                payload, manifest_relative_path=manifest_relative_path
            )
        except ManifestIntegrityError as exc:
            errors.append(f"[{i}] {exc}")
            if isinstance(stored_hash, str):
                prev_hash_expected = stored_hash
                last_hash = stored_hash
            continue

        recomputed = compute_record_hash(canonical)
        if isinstance(stored_hash, str) and stored_hash != recomputed:
            errors.append(
                f"[{i}] record_hash mismatch (tamper detected): "
                f"stored={stored_hash!r} recomputed={recomputed!r}"
            )

        actual_prev = raw.get("previous_record_hash")
        if actual_prev != prev_hash_expected:
            if i == 0:
                errors.append(
                    f"[{i}] genesis previous_record_hash must be 64 zeros, "
                    f"got {actual_prev!r}"
                )
            else:
                errors.append(
                    f"[{i}] previous_record_hash chain break: "
                    f"expected={prev_hash_expected!r} got={actual_prev!r}"
                )

        stage = raw.get("stage")
        stage_idx = _STAGE_ORDER.get(stage) if isinstance(stage, str) else None
        if stage_idx is None:
            errors.append(f"[{i}] unknown stage: {stage!r}")
        else:
            if stage not in stages_seen:
                stages_seen.append(stage)
            if stage_idx < last_stage_idx:
                errors.append(f"[{i}] stage out of order: {stage!r}")
            elif stage_idx in sealed_stage_idx:
                errors.append(
                    f"[{i}] stage {stage!r} already sealed; cannot append further records"
                )
            last_stage_idx = max(last_stage_idx, stage_idx)

        record_type = raw.get("record_type")
        if record_type == "stage_seal":
            if stage_idx is not None and stage_idx not in sealed_stage_idx:
                sealed_stage_idx.add(stage_idx)
                sealed_stage_values.append(stage)
            if isinstance(stage, str) and file_records_per_stage.get(stage, 0) == 0:
                errors.append(
                    f"[{i}] stage_seal for stage {stage!r} seals no records "
                    f"(every sealed stage needs at least one file record)"
                )
            sealed_ref = raw.get("sealed_record_hash")
            if sealed_ref != actual_prev:
                errors.append(
                    f"[{i}] stage_seal.sealed_record_hash ({sealed_ref!r}) must equal "
                    f"this record's previous_record_hash ({actual_prev!r})"
                )
        elif record_type == "file":
            if isinstance(stage, str):
                file_records_per_stage[stage] = file_records_per_stage.get(stage, 0) + 1
            if file_hash_provider is not None:
                rel = raw.get("relative_path")
                try:
                    expected_hash = file_hash_provider(rel)  # type: ignore[arg-type]
                except Exception as exc:  # caller-supplied lookup failure
                    errors.append(f"[{i}] file_hash_provider raised for {rel!r}: {exc}")
                else:
                    if expected_hash != raw.get("file_sha256"):
                        errors.append(
                            f"[{i}] file_sha256 mismatch for {rel!r}: "
                            f"recorded={raw.get('file_sha256')!r} actual={expected_hash!r}"
                        )

        if isinstance(stored_hash, str):
            prev_hash_expected = stored_hash
            last_hash = stored_hash

    for stage in stages_seen:
        if stage not in sealed_stage_values:
            errors.append(
                f"stage {stage!r} has {file_records_per_stage.get(stage, 0)} record(s) "
                f"but no stage_seal (unsealed/truncated chain)"
            )

    return ChainVerificationResult(
        valid=not errors,
        n_records=len(records),
        errors=tuple(errors),
        sealed_stages=tuple(sealed_stage_values),
        last_record_hash=last_hash,
    )


# =========================================================================
# 1b. JSONL hash-chain manifest — narrow I/O adapter
# =========================================================================


def append_manifest_record(path: str | Path, record: Mapping[str, object]) -> dict[str, object]:
    """Append one record to the JSONL manifest at `path`.

    `record` must be the FULL persisted-schema dict (as validated by
    canonicalize_manifest_record) PLUS `record_hash` (pre-computed by the
    caller via canonicalize_manifest_record + compute_record_hash) PLUS an
    explicit `finalized: True` marker — the caller's declaration that the
    underlying file (for `file` records) is closed and immutable. Both
    `record_hash` and `finalized` are stripped from the on-disk line's
    logical content per the frozen schema; `finalized` is never persisted
    (it is a call-time gate, not a chain attribute) and `record_hash` IS
    persisted (explicit, per spec).

    Never creates `path`'s parent directory — raises FileNotFoundError if
    it does not already exist (directory lifecycle belongs to the main
    runner). Re-derives and cross-checks the canonical hash and the chain
    linkage against the manifest's current tail before writing, refusing
    to append anything that would corrupt the chain.
    """
    p = Path(path)
    if not p.parent.is_dir():
        raise FileNotFoundError(
            f"append_manifest_record: parent directory does not exist "
            f"(runinfra never creates attempt/run root directories): {p.parent}"
        )

    rec = dict(record)
    finalized = rec.pop("finalized", None)
    if finalized is not True:
        raise ValueError(
            "append_manifest_record: record must carry finalized=True; unclosed/temp "
            "files must never enter the manifest chain"
        )

    claimed_hash = rec.pop("record_hash", None)
    if not isinstance(claimed_hash, str) or not _HEX64_RE.match(claimed_hash):
        raise ManifestIntegrityError(
            "append_manifest_record: record_hash missing or malformed"
        )

    manifest_relative_path = p.name
    canonical = canonicalize_manifest_record(rec, manifest_relative_path=manifest_relative_path)
    recomputed = compute_record_hash(canonical)
    if recomputed != claimed_hash:
        raise ManifestIntegrityError(
            "append_manifest_record: supplied record_hash does not match the recomputed "
            "hash of the record payload; refusing to append a corrupt/tampered record"
        )

    tail_hash = GENESIS_PREVIOUS_HASH
    if p.exists():
        last_line: str | None = None
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last_line = line
        if last_line is not None:
            # SA-6 F-26: a corrupt / truncated tail must be a hard integrity
            # error. Previously a non-JSON tail raised a bare JSONDecodeError
            # and a tail without `record_hash` silently fell back to the
            # genesis hash — i.e. a damaged manifest could be re-forked from
            # the start without anyone noticing.
            try:
                tail_record = json.loads(last_line)
            except json.JSONDecodeError as exc:
                raise ManifestIntegrityError(
                    f"append_manifest_record: manifest tail line is not valid JSON "
                    f"(corrupt/truncated chain, refusing to append): {exc}"
                ) from exc
            if not isinstance(tail_record, dict):
                raise ManifestIntegrityError(
                    "append_manifest_record: manifest tail line is not a JSON object "
                    "(corrupt chain, refusing to append)"
                )
            tail_claim = tail_record.get("record_hash")
            if not isinstance(tail_claim, str) or not _HEX64_RE.match(tail_claim):
                raise ManifestIntegrityError(
                    "append_manifest_record: manifest tail line carries no valid "
                    "record_hash (corrupt chain, refusing to append)"
                )
            tail_hash = tail_claim

    if rec["previous_record_hash"] != tail_hash:
        raise ManifestIntegrityError(
            f"append_manifest_record: previous_record_hash "
            f"{rec['previous_record_hash']!r} does not match manifest tail "
            f"{tail_hash!r}; out-of-order or forked append"
        )

    persisted = dict(rec)
    persisted["record_hash"] = claimed_hash
    line_json = json.dumps(persisted, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line_json + "\n")

    return persisted


# =========================================================================
# 2. Stage-C log-leak guard — pure logic
# =========================================================================

_LOG_SCHEMA_STAGE_STATUS = "stage_status"
_LOG_SCHEMA_HEARTBEAT = "heartbeat"
_LOG_SCHEMA_FILE_HASH = "file_hash"
_LOG_SCHEMA_COMPLETION = "completion"
LOG_SCHEMAS: tuple[str, ...] = (
    _LOG_SCHEMA_STAGE_STATUS,
    _LOG_SCHEMA_HEARTBEAT,
    _LOG_SCHEMA_FILE_HASH,
    _LOG_SCHEMA_COMPLETION,
)

_STAGE_ALT = "|".join(re.escape(v) for v in _STAGE_VALUES)
_ISO_TS_RE = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})"

_SCHEMA_PATTERNS: dict[str, re.Pattern[str]] = {
    _LOG_SCHEMA_STAGE_STATUS: re.compile(rf"^stage=(?:{_STAGE_ALT}) status=(?:pass|fail|start|end)$"),
    _LOG_SCHEMA_HEARTBEAT: re.compile(rf"^heartbeat stage=(?:{_STAGE_ALT}) ts={_ISO_TS_RE}$"),
    _LOG_SCHEMA_FILE_HASH: re.compile(r"^file=[A-Za-z0-9_./-]+ sha256=[0-9a-f]{64}$"),
    _LOG_SCHEMA_COMPLETION: re.compile(rf"^stage=(?:{_STAGE_ALT}) complete records=\d+$"),
}

# See the module docstring's "known deviation" note: the task prose asks for
# this table to live in contracts.py; it is defined here because contracts.py
# is import-only for SA-5. Categories are exactly those named in the task
# spec (Oracle / label / E1 / E2 / annual / frequency / distribution), plus
# directly adjacent research-output vocabulary that would equally leak
# Stage-C computation results.
_FORBIDDEN_VOCAB: tuple[str, ...] = (
    "oracle", "label", "labels", "e1", "e2", "annual", "annually", "yearly",
    "frequency", "freq", "distribution", "decile", "percentile", "sharpe",
    "drawdown", "verdict", "expected_value", "mfe", "mae", "y_cont", "ycont",
    "pnl", "continuation", "ceiling",
    # SA-6 F-20: the S0 feature/label vocabulary itself leaks *which*
    # research quantity a line is about, even when the number is withheld.
    "theta", "base_rate", "cont", "adr", "adr14", "rvol", "gap", "retrace",
    "warmup", "warm_up", "funnel", "na",
)
_FORBIDDEN_VOCAB_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(w) for w in _FORBIDDEN_VOCAB) + r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)

# Numeric whitelist = counts (pure integers) and hashes (64 lowercase hex,
# already locked to that exact shape by the schema patterns above) and
# ISO-8601 whole-second timestamps (no fractional seconds, so no decimal
# point can appear in a legitimate token). Anything else shaped like a
# decimal float is a leak by definition.
_FLOAT_LEAK_RE = re.compile(r"\d+\.\d+")

# SA-6 F-20: `file=` paths are the one whitelisted place where free-form text
# survives the schema, so a研究 number can be smuggled in with the decimal
# point spelled as an underscore (`base_rate_0_63.log` == 0.63). Reject any
# path token that splits digits across underscores (`_<digits>_<digits>`).
# A single underscore-delimited numeric group stays legal so that legitimate
# UTC run-directory stamps (`S0-T001_20260731T100000Z`) still pass.
_SPLIT_NUMBER_IN_PATH_RE = re.compile(r"_\d+_\d+")


def validate_log_event(message: str, *, schema: str | None = None) -> None:
    """Fail-closed Stage-C log guard. Raises LogLeakError unless `message`:
      1. conforms to one of the whitelisted schemas (stage status / heartbeat
         / file hash / non-research completion count) — or, if `schema` is
         given explicitly, conforms to exactly that one;
      2. contains no forbidden research vocabulary (Oracle/label/E1/E2/
         annual/frequency/distribution and close synonyms), anywhere in the
         message, even inside an otherwise-whitelisted field such as a file
         path;
      3. contains no bare (non-count, non-hash, non-timestamp) floating
         point number anywhere in the message;
      4. (file-hash lines) carries no path token that splits digits across
         underscores — the underscore-as-decimal-point smuggling channel
         (SA-6 F-20).

    Returns None on success (pass). Pure: no I/O, no global state — a real
    logger wrapper calls this before emitting each line and aborts the run
    on LogLeakError ("宁可误杀": prefer a false block over any leak).
    """
    if not isinstance(message, str):
        raise LogLeakError(f"log message must be a str, got {type(message)!r}")

    if schema is not None and schema not in LOG_SCHEMAS:
        raise LogLeakError(f"unknown log schema requested: {schema!r}")

    candidates = (schema,) if schema is not None else LOG_SCHEMAS
    if not any(_SCHEMA_PATTERNS[s].match(message) for s in candidates):
        raise LogLeakError(
            f"Stage-C log guard: message does not conform to any whitelisted "
            f"schema {candidates}: {message!r}"
        )

    if _FORBIDDEN_VOCAB_RE.search(message):
        raise LogLeakError(
            f"Stage-C log guard: forbidden research vocabulary detected: {message!r}"
        )

    if _FLOAT_LEAK_RE.search(message):
        raise LogLeakError(
            f"Stage-C log guard: non-whitelisted floating-point value detected: {message!r}"
        )

    if message.startswith("file=") and _SPLIT_NUMBER_IN_PATH_RE.search(
        message.split(" ", 1)[0]
    ):
        raise LogLeakError(
            f"Stage-C log guard: file path splits digits across underscores "
            f"(underscore-as-decimal-point leak channel): {message!r}"
        )


# =========================================================================
# 3. NA-conservation checker — pure logic
# =========================================================================


@dataclass(frozen=True)
class NAConservationResult:
    """Structured failure object (Aaron's phrasing) rather than an
    exception: the caller (main runner) inspects `ok` and raises
    NAConservationError itself if it decides to STOP. Never mutates or
    drops anything — pure arithmetic over caller-supplied counts; no
    pandas object is touched here, so dropna/fillna simply cannot occur."""

    ok: bool
    per_column_ok: Mapping[str, bool]
    unregistered_reasons: tuple[str, ...]
    miscounted_columns: tuple[str, ...]
    errors: tuple[str, ...]


def check_na_conservation(
    na_reason_counts: Mapping[str, Mapping[str, int]],
    *,
    reported_total_na: Mapping[str, int],
) -> NAConservationResult:
    """Item-wise NA conservation check.

    `na_reason_counts`: {column_or_feature_name: {approved_reason: count}}
    — the itemized breakdown the caller produced for each column/label.
    `reported_total_na`: REQUIRED {column_or_feature_name: total_na_count}
    independently observed (e.g. a raw NaN scan on the actual table); the
    itemized reasons for each column must sum to EXACTLY that total
    (catches both over- and under-counting).

    Hardened per SA-6 F-13: the approved-reason table is ALWAYS
    contracts.APPROVED_NA_REASONS — it is deliberately not a parameter, so
    a caller cannot widen the accepted reason set at the call site; and
    `reported_total_na` is mandatory, so the check can never degrade into a
    reasons-are-spelled-correctly formality with no conservation arithmetic.
    Any reason key outside APPROVED_NA_REASONS is a hard failure regardless
    of the sum check.
    """
    if not isinstance(na_reason_counts, Mapping):
        raise TypeError("na_reason_counts must be a mapping")
    if not isinstance(reported_total_na, Mapping):
        raise TypeError("reported_total_na must be a mapping")

    approved = set(APPROVED_NA_REASONS)
    errors: list[str] = []
    unregistered: list[str] = []
    miscounted: list[str] = []
    per_column_ok: dict[str, bool] = {}

    for column, reasons in na_reason_counts.items():
        col_ok = True
        if not isinstance(reasons, Mapping):
            errors.append(f"{column}: reason-count entry must be a mapping, got {reasons!r}")
            per_column_ok[column] = False
            continue

        running_total = 0
        for reason, count in reasons.items():
            if reason not in approved:
                col_ok = False
                unregistered.append(f"{column}::{reason}")
                errors.append(
                    f"{column}: NA reason {reason!r} is not in APPROVED_NA_REASONS"
                )
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                col_ok = False
                errors.append(
                    f"{column}: reason {reason!r} has a non-negative-integer count: {count!r}"
                )
            else:
                running_total += count

        if column in reported_total_na:
            want = reported_total_na[column]
            if running_total != want:
                col_ok = False
                miscounted.append(column)
                errors.append(
                    f"{column}: itemized NA reasons sum to {running_total} but the "
                    f"independently observed total is {want} (conservation violated)"
                )
        else:
            col_ok = False
            miscounted.append(column)
            errors.append(
                f"{column}: no independently observed NA total was supplied for this "
                f"column (F-13: every itemized column must be conserved against one)"
            )

        per_column_ok[column] = col_ok

    for column in reported_total_na:
        if column not in na_reason_counts:
            per_column_ok[column] = False
            miscounted.append(column)
            errors.append(
                f"{column}: an independently observed NA total was given but no "
                f"itemized reason breakdown exists for it"
            )

    return NAConservationResult(
        ok=not errors,
        per_column_ok=per_column_ok,
        unregistered_reasons=tuple(unregistered),
        miscounted_columns=tuple(miscounted),
        errors=tuple(errors),
    )


# =========================================================================
# 4. expected_preflight_assertions comparator — pure logic
# =========================================================================

# --- 4a. preflight -> contracts translation layer (SA-6 F-14) -------------
#
# S0_INPUT_PREFLIGHT.json and contracts.py do NOT share a vocabulary or a
# shape, so feeding the raw preflight document to compare_preflight_assertions
# produced a guaranteed shape mismatch (i.e. an unusable comparator). This
# layer is a PURE, EXPLICIT, TOTAL renaming/reshaping map. It changes neither
# side's semantics: no value is recomputed, rescaled, merged across different
# quantities, or invented — only key names and nesting change, and the two
# documented structural drops below are applied.
#
# Three transformations, exactly as scoped by the SA-7 fix direction:
#   1. NA-reason vocabulary: preflight wording -> APPROVED_NA_REASONS wording
#      (_PREFLIGHT_NA_REASON_TO_CONTRACTS below; every preflight word must be
#      listed, an unknown word is a hard failure rather than a silent pass);
#   2. funnel: the 10 scalar funnel keys collapse to the 5-number chain
#      L0->L1->L2->L3->L4 — the four `minus_*` DELTA rows (including the
#      `minus_adr14_warmup_days` row) and the `side_diagnostic_*` row are
#      dropped, because a delta is not an independently computed quantity
#      (it is L(n-1) - L(n)) and asserting it would double-count the chain;
#   3. the adr14 ROW is dropped on both sides of the seam: the funnel's
#      `minus_adr14_warmup_days` delta (see 2) and any `adr14` feature row —
#      ADR14 is a normalisation series carried on DayFeatures, not one of the
#      F1..F11 preflight feature rows, so it has no expected counterpart and
#      must not appear in either key set. (The `adr14_warmup` NA REASON is a
#      different thing and is preserved verbatim: it is an approved reason.)
#
# The result is a flat {str: int} mapping ready to be passed straight into
# compare_preflight_assertions as `expected`. This module still never reads
# S0_INPUT_PREFLIGHT.json: the caller parses the file and passes the object.

_PREFLIGHT_NA_REASON_TO_CONTRACTS: Mapping[str, str] = {
    # identical in both vocabularies (listed explicitly: the map is total)
    "adr14_warmup": "adr14_warmup",
    "f4_lookback_warmup": "f4_lookback_warmup",
    "roll_transition_day_na": "roll_transition_day_na",
    "prev_rth_close_anchor_missing": "prev_rth_close_anchor_missing",
    "overnight_window_empty": "overnight_window_empty",
    "anchor_missing": "anchor_missing",
    # differing wording -> contracts.APPROVED_NA_REASONS member
    "zero_denominator_no_direction": "zero_direction_day_l82",
    "multi_event_day_single_category_undetermined": "multi_event_day_f10_na",
    # the four IR-19 prev-RTH-close sub-reasons collapse onto the single
    # approved reason whose contracts docstring already enumerates them
    # ("incl. early-close-bar-absent, vendor-degraded, first sample day")
    "no_prior_rth_session_in_sample": "prev_rth_close_anchor_missing",
    "prev_day_early_close_final_scheduled_bar_absent": "prev_rth_close_anchor_missing",
    "prev_day_vendor_degraded_zero_bar": "prev_rth_close_anchor_missing",
    "prev_day_1559_bar_absent": "prev_rth_close_anchor_missing",
}

_FUNNEL_CHAIN_KEYS: tuple[str, ...] = (
    "L0_scheduled_trading_days",
    "L1_observed_rth_days",
    "L2_regular_full_session_candidates",
    "L3_structurally_eligible_days",
    "L4_final_feature_construction_dates",
)

_F10_FINAL_CATEGORIES: tuple[str, ...] = ("CPI", "NFP", "FOMC", "none", "NA_multi_event")


def translate_na_reason(preflight_reason: str) -> str:
    """Map one preflight NA-reason word onto its APPROVED_NA_REASONS member.

    Pure. Raises ValueError on any unlisted word — an unrecognised reason is
    a translation failure (fail closed), never a pass-through.
    """
    try:
        contracts_reason = _PREFLIGHT_NA_REASON_TO_CONTRACTS[preflight_reason]
    except KeyError:
        raise ValueError(
            f"preflight NA reason {preflight_reason!r} has no entry in the "
            f"preflight->contracts translation table; refusing to guess"
        ) from None
    if contracts_reason not in APPROVED_NA_REASONS:
        raise ValueError(
            f"translation target {contracts_reason!r} is not in APPROVED_NA_REASONS"
        )
    return contracts_reason


def translate_preflight_assertions(preflight: Mapping[str, object]) -> dict[str, int]:
    """Translate a parsed S0_INPUT_PREFLIGHT.json into the flat, contracts-
    vocabulary `expected` mapping consumed by compare_preflight_assertions.

    Pure function: no I/O, no clock, no global state, and no arithmetic
    beyond summing sub-reason counts that translate onto the SAME approved
    reason (the IR-19 prev-RTH-close family). Emitted key families:

        funnel.<L0..L4>                      5 structural counts
        f10.<CPI|NFP|FOMC|none|NA_multi_event>
        feature.<F1..F11>.constructible / .na
        na_reason.<F1..F11>.<approved_reason>
        anchor.<name>.available / .missing
        na_reason.anchor.<name>.<approved_reason>
        label.<Y_cont|Y1..Y5>.available / .unavailable

    Raises ValueError if a required section/key is absent or if any NA reason
    word is untranslatable — a preflight document that cannot be translated
    must stop the run, not silently produce a smaller assertion set.
    """
    if not isinstance(preflight, Mapping):
        raise TypeError("preflight must be a mapping (already-parsed JSON object)")

    out: dict[str, int] = {}

    def _section(name: str) -> Mapping[str, object]:
        sec = preflight.get(name)
        if not isinstance(sec, Mapping):
            raise ValueError(f"preflight document has no {name!r} section")
        return sec

    def _int(value: object, where: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{where}: expected an int count, got {value!r}")
        return value

    funnel = _section("funnel")
    for key in _FUNNEL_CHAIN_KEYS:
        if key not in funnel:
            raise ValueError(f"funnel section is missing {key!r}")
        out[f"funnel.{key}"] = _int(funnel[key], f"funnel.{key}")

    f10 = _section("f10")
    final_counts = f10.get("final_mutually_exclusive_F10_counts_eligible")
    if not isinstance(final_counts, Mapping):
        raise ValueError("f10 section is missing final_mutually_exclusive_F10_counts_eligible")
    for category in _F10_FINAL_CATEGORIES:
        if category not in final_counts:
            raise ValueError(f"f10 final counts missing category {category!r}")
        out[f"f10.{category}"] = _int(final_counts[category], f"f10.{category}")

    features = _section("features")
    for name, row in features.items():
        if name == "adr14":  # see transformation 3 in the section header
            continue
        if not isinstance(row, Mapping):
            raise ValueError(f"feature row {name!r} is not a mapping")
        out[f"feature.{name}.constructible"] = _int(
            row.get("constructible"), f"feature.{name}.constructible")
        out[f"feature.{name}.na"] = _int(row.get("na"), f"feature.{name}.na")
        reasons = row.get("reasons") or {}
        if not isinstance(reasons, Mapping):
            raise ValueError(f"feature row {name!r} has a non-mapping 'reasons'")
        for word, count in reasons.items():
            key = f"na_reason.{name}.{translate_na_reason(word)}"
            out[key] = out.get(key, 0) + _int(count, f"na_reason.{name}.{word}")

    anchors = _section("anchors")
    for name, row in anchors.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"anchor row {name!r} is not a mapping")
        out[f"anchor.{name}.available"] = _int(
            row.get("available"), f"anchor.{name}.available")
        out[f"anchor.{name}.missing"] = _int(row.get("missing"), f"anchor.{name}.missing")
        for word, count in (row.get("missing_reasons") or {}).items():
            key = f"na_reason.anchor.{name}.{translate_na_reason(word)}"
            out[key] = out.get(key, 0) + _int(
                count, f"na_reason.anchor.{name}.{word}")

    labels = _section("labels")
    for name, row in labels.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"label row {name!r} is not a mapping")
        out[f"label.{name}.available"] = _int(
            row.get("available_days"), f"label.{name}.available")
        out[f"label.{name}.unavailable"] = _int(
            row.get("unavailable_days"), f"label.{name}.unavailable")

    return out


@dataclass(frozen=True)
class AssertionItemResult:
    key: str
    expected: object
    actual: object
    status: str  # "match" | "mismatch" | "missing_actual" | "unexpected_actual"


@dataclass(frozen=True)
class AssertionComparisonResult:
    all_pass: bool
    shape_ok: bool
    items: tuple[AssertionItemResult, ...]
    missing_keys: tuple[str, ...]
    extra_keys: tuple[str, ...]
    mismatched_keys: tuple[str, ...]


def _values_match(expected: object, actual: object) -> bool:
    # Guard bool/int aliasing (True == 1) so a bool assertion never silently
    # "passes" against an int actual or vice versa.
    if isinstance(expected, bool) or isinstance(actual, bool):
        return isinstance(expected, bool) and isinstance(actual, bool) and expected == actual
    return expected == actual


def compare_preflight_assertions(
    expected: Mapping[str, object],
    actual: Mapping[str, object],
) -> AssertionComparisonResult:
    """Pure, one-way, item-by-item comparator (Aaron 2026-07-31 ruling).

    `expected` is the runner's `expected_preflight_assertions` set (packet
    §5 numbers — e.g. the funnel 2989->2969->2884->2882->2868, F10 128/134/
    83/2528/9, etc.) and `actual` is what the runner independently computed
    this run, under the frozen rules. BOTH are supplied by the caller
    (main runner) — this module never reads S0_INPUT_PREFLIGHT.json, never
    imports assertion numbers from contracts.py or RunConfig, and contracts.py
    defines no such numbers to import. `expected` is used ONLY for this
    one-way comparison; nothing here feeds it back into any computation
    path or uses it to construct `actual`.

    Reports three states: all-pass (every key matches and the key sets are
    identical), single/partial mismatch (same key set, some value differs),
    and shape mismatch (`expected`/`actual` key sets differ).
    """
    if not isinstance(expected, Mapping) or not isinstance(actual, Mapping):
        raise TypeError("expected and actual must both be mappings")

    expected_keys = set(expected.keys())
    actual_keys = set(actual.keys())
    missing = tuple(sorted(expected_keys - actual_keys))
    extra = tuple(sorted(actual_keys - expected_keys))
    shape_ok = not missing and not extra

    items: list[AssertionItemResult] = []
    mismatched: list[str] = []

    for key in sorted(expected_keys | actual_keys):
        if key in missing:
            items.append(AssertionItemResult(key, expected[key], None, "missing_actual"))
            continue
        if key in extra:
            items.append(AssertionItemResult(key, None, actual[key], "unexpected_actual"))
            continue
        exp_v, act_v = expected[key], actual[key]
        if _values_match(exp_v, act_v):
            items.append(AssertionItemResult(key, exp_v, act_v, "match"))
        else:
            items.append(AssertionItemResult(key, exp_v, act_v, "mismatch"))
            mismatched.append(key)

    return AssertionComparisonResult(
        all_pass=shape_ok and not mismatched,
        shape_ok=shape_ok,
        items=tuple(items),
        missing_keys=missing,
        extra_keys=extra,
        mismatched_keys=tuple(mismatched),
    )


# =========================================================================
# 5. Failure report — pure render + narrow I/O write
# =========================================================================

_VALID_REPORT_TYPES = ("PRE_RUN_ATTEMPT_FAILURE", "RUN_FAILURE_REPORT")
_VALID_EXCEPTION_TYPES = (
    RunGateError.__name__,
    NAConservationError.__name__,
    AssertionMismatchError.__name__,
    LogLeakError.__name__,
    InputDataDefectError.__name__,             # SA-10 N2 (IR-22)
    "Unknown",
)


@dataclass(frozen=True)
class FailureReport:
    report_type: str
    trial_id: str
    stage: str
    trial_state: str
    failure_reason: str
    exception_type: str
    released_information: tuple[str, ...]
    chain_status: Mapping[str, object]
    generated_at_utc: str
    markdown: str
    json_payload: Mapping[str, object]


def render_failure_report(
    *,
    report_type: str,
    run_config: RunConfig,
    stage: RunStage,
    trial_state: TrialState,
    failure_reason: str,
    exception_type: str,
    released_information: Sequence[str],
    chain_status: Mapping[str, object],
    generated_at_utc: str,
) -> FailureReport:
    """Pure renderer for RUN_FAILURE_REPORT (Stage C+) / PRE_RUN_ATTEMPT_
    FAILURE (Stage A/B) content (packet §8). Produces both a markdown
    document and a JSON-serializable mirror; writes nothing to disk (see
    write_failure_report for the I/O half). `generated_at_utc` is supplied
    by the caller (not read from the system clock here) to keep this
    function fully deterministic and unit-testable.

    `exception_type` must name one of the four contracts.py error types
    this infrastructure works with (RunGateError / NAConservationError /
    AssertionMismatchError / LogLeakError) or "Unknown" — enforced here so
    a failure report can never silently reference a governance error type
    that doesn't exist in the frozen contract.
    """
    if report_type not in _VALID_REPORT_TYPES:
        raise ValueError(f"report_type must be one of {_VALID_REPORT_TYPES}, got {report_type!r}")
    if not isinstance(run_config, RunConfig):
        raise TypeError("run_config must be a RunConfig instance")
    if not isinstance(stage, RunStage):
        raise TypeError("stage must be a RunStage member")
    if not isinstance(trial_state, TrialState):
        raise TypeError("trial_state must be a TrialState member")
    if exception_type not in _VALID_EXCEPTION_TYPES:
        raise ValueError(
            f"exception_type must be one of {_VALID_EXCEPTION_TYPES}, got {exception_type!r}"
        )

    released = tuple(released_information)
    chain_status_dict = dict(chain_status)

    json_payload: dict[str, object] = {
        "report_type": report_type,
        "trial_id": run_config.trial_id,
        "authorized_commit": run_config.authorized_commit,
        "stage": stage.value,
        "trial_state": trial_state.value,
        "failure_reason": failure_reason,
        "exception_type": exception_type,
        "released_information": list(released),
        "chain_status": chain_status_dict,
        "generated_at_utc": generated_at_utc,
    }

    lines = [
        f"# {report_type}",
        "",
        f"- trial_id: {run_config.trial_id}",
        f"- authorized_commit: {run_config.authorized_commit}",
        f"- stage_at_failure: {stage.value}",
        f"- trial_state_at_failure: {trial_state.value}",
        f"- generated_at_utc: {generated_at_utc}",
        f"- exception_type: {exception_type}",
        "",
        "## Failure point",
        "",
        failure_reason,
        "",
        "## Released information (exposure so far)",
        "",
    ]
    lines += [f"- {item}" for item in released] if released else ["- (none)"]
    lines += [
        "",
        "## Chain status",
        "",
        "```json",
        json.dumps(chain_status_dict, sort_keys=True, indent=2, ensure_ascii=False),
        "```",
        "",
    ]

    return FailureReport(
        report_type=report_type,
        trial_id=run_config.trial_id,
        stage=stage.value,
        trial_state=trial_state.value,
        failure_reason=failure_reason,
        exception_type=exception_type,
        released_information=released,
        chain_status=chain_status_dict,
        generated_at_utc=generated_at_utc,
        markdown="\n".join(lines),
        json_payload=json_payload,
    )


def write_failure_report(directory: str | Path, rendered: FailureReport) -> dict[str, Path]:
    """Write `rendered`'s markdown + JSON into `directory`.

    `directory` MUST already exist (this function never creates an
    attempt/run root directory — that lifecycle is the main runner's).
    Raises FileNotFoundError otherwise. Returns the two paths written.
    """
    d = Path(directory)
    if not d.is_dir():
        raise FileNotFoundError(
            f"write_failure_report: directory does not exist (runinfra never creates "
            f"attempt/run root directories): {d}"
        )

    md_path = d / f"{rendered.report_type}.md"
    json_path = d / f"{rendered.report_type}.json"
    md_path.write_text(rendered.markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(rendered.json_payload, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}


# =========================================================================
# 6. Post-seal archive step (L-5 ruling, 2026-08-10) — narrow I/O
# =========================================================================


@dataclass(frozen=True)
class ArchiveFileRecheck:
    """One file's post-copy recheck record — the exact evidence a `path,
    bytes, sha256, match` receipt is meant to be. `source_bytes`/
    `dest_bytes`/`*_sha256` are ``None`` only when the file could not be
    read/copied at all (a hard per-file failure, e.g. a permissions error
    mid-copy); a completed copy always carries real numbers on both
    sides, even when they disagree."""

    relative_path: str                 # POSIX-separated, relative to the run dir root
    source_bytes: int | None
    dest_bytes: int | None
    source_sha256: str | None
    dest_sha256: str | None
    match: bool


@dataclass(frozen=True)
class ArchiveInventoryEntry:
    """One entry of a full-tree inventory — the identity an archive copy
    must reproduce EXACTLY (Codex round-2 #3).

    `size`/`sha256` are ``None`` for directories (a directory has no
    content of its own); for files they are the byte length and the
    SHA-256 of the complete content. Equality of these values is the whole
    discipline: a copy is an archive of record only if the mapping
    ``{relative_path: entry}`` built from it EQUALS the mapping built from
    the source before the copy began.
    """

    relative_path: str                 # POSIX-separated, relative to the tree root
    is_dir: bool
    size: int | None
    sha256: str | None


@dataclass(frozen=True)
class ArchiveInventorySummary:
    """Counts of the PRE-COPY SOURCE inventory, plus the verdict of each
    of the three set-level equality proofs `archive_sealed_run` performs.

    A verdict is ``None`` when that proof was never reached because an
    earlier step already failed — deliberately distinct from ``False``,
    which is a proof that RAN and REFUSED.
    """

    n_files: int
    n_dirs: int
    total_bytes: int
    source_stable: bool | None            # post-copy source RE-inventory == pre-copy
    staging_matches_source: bool | None   # `<dest>.partial` tree == source
    dest_matches_source: bool | None      # promoted archive dir == source


@dataclass(frozen=True)
class ArchiveReport:
    """The full result of one `archive_sealed_run` call. `status` is the
    "loud" terminal-state word the runner records on `RunOutcome`:
    ``"archive_ok"`` (ok=True, every file matched) or ``"archive_failed"``
    (ok=False — at least one copy/re-read/mismatch problem; `errors`
    carries a human-readable line per problem and `files` carries the
    full per-file recheck manifest, matched and mismatched entries
    alike).

    Codex round-2 #3 added `inventory`: the counts of the pre-copy source
    inventory plus the three exact-equality verdicts. It is ``None`` only
    when the call failed before the source inventory could be built at all
    (destination refusal, unremovable debris, uncreatable staging dir).
    """

    ok: bool
    status: str                        # "archive_ok" | "archive_failed"
    run_dir_name: str
    source_dir: str
    dest_dir: str
    files: tuple[ArchiveFileRecheck, ...]
    errors: tuple[str, ...]
    inventory: ArchiveInventorySummary | None = None


_ARCHIVE_OK = "archive_ok"
_ARCHIVE_FAILED = "archive_failed"

# Codex final-review #5 (S0 closeout). The archive is built under
# `<dest><_ARCHIVE_PARTIAL_SUFFIX>` and only PROMOTED to `<dest>` once every
# file has been copied AND re-verified. A `*.partial` directory is therefore
# never an archive of record: it is either mid-construction or the debris of
# a crashed attempt, and in both cases it may be deleted. That is what makes
# the retry path safe — the thing a failed attempt leaves behind is not the
# thing the next attempt refuses to overwrite.
_ARCHIVE_PARTIAL_SUFFIX = ".partial"


def _remove_archive_partial(partial: Path) -> str | None:
    """Best-effort removal of an in-progress archive copy.

    Returns `None` when the directory is gone (or was never there), else a
    human-readable error LINE for the report — a removal that itself fails
    is disclosed, never swallowed: leftover debris under `archive_root` is
    the exact condition that blocked the retry this change exists to
    unblock, so its presence must be visible in the report."""
    if not partial.exists():
        return None
    try:
        shutil.rmtree(partial)
    except OSError as exc:
        return (f"in-progress archive copy could NOT be removed "
                f"({type(exc).__name__}: {exc}); it must be deleted by hand "
                f"before the next archive attempt: {partial}")
    return None


_INVENTORY_ROOT_REL = "."


def _is_reparse_or_symlink(path: Path) -> bool:
    """True if `path` is a symlink OR a Windows reparse point / junction.

    Codex round-2 #3. BOTH probes are required and neither subsumes the
    other: a Windows DIRECTORY JUNCTION reports ``Path.is_symlink() ==
    False`` while carrying ``FILE_ATTRIBUTE_REPARSE_POINT`` in
    ``os.lstat(...).st_file_attributes`` (measured on this box: a
    ``mklink /J`` junction has attrs 0x410), and a POSIX symlink has no
    ``st_file_attributes`` at all — hence the getattr default of 0, which
    makes the second probe a no-op off Windows.

    Never follows the entry: `Path.is_symlink` and `os.lstat` both
    describe the link itself. Raises OSError if the entry cannot be
    lstat-ed; every caller treats that as a refusal, not as a pass.
    """
    if path.is_symlink():
        return True
    attrs = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _build_inventory(
        root: Path) -> tuple[dict[str, ArchiveInventoryEntry], list[str]]:
    """Full recursive inventory of `root`, plus the refusal lines it
    produced. ``(inventory, errors)``; a non-empty `errors` means the
    inventory is INCOMPLETE and must not be used as an authority.

    Codex round-2 #3. Two jobs, deliberately in one function so the source
    tree, the staging tree and the promoted archive tree are all measured
    by literally the same code:

      * REFUSAL. Any entry that is a symlink or a Windows reparse point /
        junction — directories included — is an error line, never an
        inventory entry. The walk is explicit (an `iterdir` stack) rather
        than `rglob`, precisely so a junction is refused BEFORE anything
        descends through it; the root itself is probed the same way. Any
        entry that is neither a regular file nor a directory is refused
        for the same reason: an archive is an inventory of real bytes.
      * MEASUREMENT. Each surviving entry becomes an `ArchiveInventoryEntry`
        keyed by its POSIX relative path — directories with `size`/`sha256`
        of None, files with their byte length and the SHA-256 of their
        complete content.
    """
    inventory: dict[str, ArchiveInventoryEntry] = {}
    errors: list[str] = []

    def _refused(entry: Path, rel: str) -> bool:
        try:
            if _is_reparse_or_symlink(entry):
                errors.append(
                    f"{rel}: symlink or reparse point/junction — an archive "
                    f"inventory describes real files only (refusing)")
                return True
        except OSError as exc:
            errors.append(f"{rel}: could not be lstat-ed: "
                          f"{type(exc).__name__}: {exc}")
            return True
        return False

    if _refused(root, _INVENTORY_ROOT_REL):
        return {}, errors

    pending = [root]
    while pending:
        current = pending.pop()
        current_rel = (_INVENTORY_ROOT_REL if current == root
                       else current.relative_to(root).as_posix())
        try:
            entries = sorted(current.iterdir())
        except OSError as exc:
            errors.append(f"{current_rel}: directory could not be "
                          f"enumerated: {type(exc).__name__}: {exc}")
            continue
        for entry in entries:
            rel = entry.relative_to(root).as_posix()
            if _refused(entry, rel):
                continue
            try:
                if entry.is_dir():
                    inventory[rel] = ArchiveInventoryEntry(
                        relative_path=rel, is_dir=True, size=None,
                        sha256=None)
                    pending.append(entry)
                elif entry.is_file():
                    data = entry.read_bytes()
                    inventory[rel] = ArchiveInventoryEntry(
                        relative_path=rel, is_dir=False, size=len(data),
                        sha256=hashlib.sha256(data).hexdigest())
                else:
                    errors.append(
                        f"{rel}: neither a regular file nor a directory "
                        f"(refusing to archive a special filesystem entry)")
            except OSError as exc:
                errors.append(f"{rel}: could not be inventoried: "
                              f"{type(exc).__name__}: {exc}")
    return inventory, errors


def _inventory_diff(source: Mapping[str, ArchiveInventoryEntry],
                    other: Mapping[str, ArchiveInventoryEntry],
                    *, other_label: str) -> list[str]:
    """Every way `other` diverges from the SOURCE inventory, as report
    lines. An empty list means EXACT equality — same relative paths, same
    file/directory types, same sizes, same content hashes. Missing,
    surplus and differing entries are all reported, so neither an extra
    file nor a dropped one nor a changed byte can pass."""
    out: list[str] = []
    for rel in sorted(set(source) - set(other)):
        out.append(f"{rel}: in the source inventory but MISSING from "
                   f"{other_label}")
    for rel in sorted(set(other) - set(source)):
        out.append(f"{rel}: EXTRA entry in {other_label} — absent from the "
                   f"source inventory")
    for rel in sorted(set(source) & set(other)):
        s, o = source[rel], other[rel]
        if s != o:
            out.append(
                f"{rel}: inventory mismatch against {other_label} (source "
                f"is_dir={s.is_dir} size={s.size} sha256={s.sha256}; "
                f"{other_label} is_dir={o.is_dir} size={o.size} "
                f"sha256={o.sha256})")
    return out


def archive_sealed_run(runs_dir: str | Path,
                       archive_root: str | Path) -> ArchiveReport:
    """Copy a SEALED run directory into ``archive_root/<run-dir-name>/``
    and independently RE-READ + re-hash every file on BOTH sides after
    the copy (L-5 ruling, 2026-08-10 — "Archive = after a run completes,
    full per-run directory copy into archive_root with a per-file SHA-256
    recheck").

    MUST be called only AFTER the run has reached `F_SEALED` — this
    function performs no stage/seal check itself (the caller, `runner.py`,
    already established that by construction: it is called from the one
    place in `run()` that follows the F_SEALED registry append) — but it
    is otherwise a NARROW, SELF-CONTAINED I/O step: it takes a directory
    path and a destination root and does exactly one thing.

    NEVER MUTATES `runs_dir` IN ANY WAY. Every filesystem write this
    function performs lands under `archive_root`; `runs_dir` is opened
    exclusively for reading (`Path.is_file` / `Path.read_bytes`). A
    mismatch or a copy failure is reported in the returned `ArchiveReport`
    (`status="archive_failed"`) and NOTHING about the sealed run directory
    is touched, deleted, moved or rewritten — exposure was already burned
    at `RUN_STARTED` and the sealed run directory IS the evidentiary
    record; an archive-side problem must never retroactively un-seal it
    or be allowed to mutate it while trying to fix itself. This function
    never raises for a per-file problem (copy failure, post-copy re-read
    failure, digest mismatch) — every such problem is captured into the
    returned report instead, so the caller always gets a structured
    result to attach to the run's terminal state. It raises only
    `FileNotFoundError` if `runs_dir` itself is not an existing directory
    (a caller error: this function is never the thing that creates a run
    directory) — see `ArchiveReport.status == "archive_failed"` for every
    other failure mode, including the destination-root itself being
    uncreatable.

    Refuses (as an `archive_failed` report, not an exception) if
    ``archive_root/<run-dir-name>/`` already exists — this function
    never overwrites a prior archive copy.

    RECOVERABILITY (Codex final review #5, S0 closeout). Every byte is
    written into ``archive_root/<run-dir-name>.partial/`` and the copy is
    PROMOTED to its final name with a single `os.replace` only after every
    file has been copied AND re-verified. A failure at any point therefore
    leaves NO directory at the final name: the partial is removed
    best-effort (a removal that itself fails is reported), so the very
    next attempt sees a clean destination and can simply retry. Before
    this, a mid-copy failure left a half-copy AT the final name, which the
    `dest.exists()` refusal below then treated as a completed archive —
    the failure was permanent and the only remedy was manual deletion. A
    stale `*.partial` left by a crashed prior attempt is removed at the
    start for the same reason: it is never the archive of record.

    The `dest.exists()` refusal is UNCHANGED and deliberately so — a
    completed archive is never overwritten, only a partial is.

    EXACT-INVENTORY DISCIPLINE (Codex round-2 #3). The per-file recheck
    above proves each COPIED file's bytes; it cannot prove that the set of
    files is right, that the sealed source held still, or that the
    promotion landed what was verified. Five steps close that:

      1. REPARSE/SYMLINK REFUSAL. While inventorying, any entry that is a
         symlink or a Windows reparse point / junction — directories
         included — refuses the whole archive (`_is_reparse_or_symlink`).
         The same check runs over the staging tree, because it is the same
         `_build_inventory` call.
      2. PRE-COPY SOURCE INVENTORY: recursive `(relative_path, is_dir,
         size, sha256-for-files)`. This is the SINGLE AUTHORITY every
         later comparison is made against; the copy loop is driven from it
         (including empty directories, which are materialised explicitly).
      3. POST-COPY SOURCE RE-INVENTORY: after the copy and per-file
         recheck complete, the source is enumerated again and must be
         EXACTLY equal to (2). A sealed run directory that changed while
         it was being archived invalidates the copy.
      4. STAGING INVENTORY: the `.partial` tree must be EXACTLY equal to
         (2). The per-file recheck already covers each file's hash; this
         set-level equality is what catches an extra file, a missing one,
         or a divergent directory shape.
      5. FINAL INVENTORY AFTER PROMOTION: the promoted destination is
         re-enumerated and re-hashed (a third full content pass) against
         (2).

    CLEANUP ASYMMETRY, stated because it is deliberate: a failure at steps
    1-4 (or in the copy) removes the `.partial` best-effort, exactly as
    before. A failure at step 5 does NOT delete anything — `dest` has
    already been promoted, so it is no longer an in-progress copy but
    EVIDENCE of a divergence, and it is retained with an explicit error
    line saying so.
    """
    src = Path(runs_dir)
    if not src.is_dir():
        raise FileNotFoundError(
            "archive_sealed_run: runs_dir does not exist or is not a "
            f"directory (archive_sealed_run never creates a run "
            f"directory): {src}"
        )
    dest_root = Path(archive_root)
    dest = dest_root / src.name
    # every write below lands here; `dest` itself is only ever produced by
    # the atomic promotion at the very end.
    partial = dest_root / f"{src.name}{_ARCHIVE_PARTIAL_SUFFIX}"

    def _report(ok: bool, errs: Sequence[str], *,
                files: Sequence[ArchiveFileRecheck] = (),
                inventory: ArchiveInventorySummary | None = None
                ) -> ArchiveReport:
        """The one construction site for this call's report — every field
        that is constant across all outcomes is written exactly once."""
        return ArchiveReport(
            ok=ok, status=_ARCHIVE_OK if ok else _ARCHIVE_FAILED,
            run_dir_name=src.name, source_dir=str(src), dest_dir=str(dest),
            files=tuple(files), errors=tuple(errs), inventory=inventory)

    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return _report(False, [f"archive_root could not be created: "
                               f"{type(exc).__name__}: {exc}"])

    if dest.exists():
        return _report(False, [f"archive destination already exists "
                               f"(refusing to overwrite a prior archive "
                               f"copy): {dest}"])

    # debris from a crashed prior attempt: safe to delete (a partial is
    # never an archive of record), and NOT safe to write into, because
    # stale files would silently survive under a fresh copy.
    stale = _remove_archive_partial(partial)
    if stale is not None:
        return _report(False, [stale])
    try:
        partial.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        return _report(False, [f"in-progress archive copy could not be "
                               f"created: {type(exc).__name__}: {exc}"])

    errors: list[str] = []
    files: list[ArchiveFileRecheck] = []

    # --- (1)+(2) PRE-COPY SOURCE INVENTORY ------------------------------
    # The symlink/reparse refusal fires here, and what survives is the
    # SINGLE AUTHORITY for every comparison below: the copy loop, the
    # post-copy source re-inventory, the staging equality and the final
    # post-promotion verification are all measured against this one
    # mapping, never against each other.
    source_inventory, inventory_errors = _build_inventory(src)
    n_files = sum(1 for e in source_inventory.values() if not e.is_dir)
    n_dirs = len(source_inventory) - n_files
    total_bytes = sum(e.size or 0 for e in source_inventory.values())

    def _summary(*, source_stable: bool | None = None,
                 staging_matches_source: bool | None = None,
                 dest_matches_source: bool | None = None
                 ) -> ArchiveInventorySummary:
        return ArchiveInventorySummary(
            n_files=n_files, n_dirs=n_dirs, total_bytes=total_bytes,
            source_stable=source_stable,
            staging_matches_source=staging_matches_source,
            dest_matches_source=dest_matches_source)

    def _abandon_partial(errs: list[str]) -> list[str]:
        """Discard the in-progress copy (best effort) and disclose a
        removal that itself failed. Only ever called BEFORE promotion —
        see the cleanup asymmetry in this function's docstring."""
        cleanup = _remove_archive_partial(partial)
        if cleanup is not None:
            errs.append(cleanup)
        return errs

    if inventory_errors:
        return _report(False, _abandon_partial(inventory_errors),
                       inventory=_summary())

    # Directories come from the inventory rather than implicitly from a
    # file's parent mkdir, so an EMPTY source directory is reproduced too;
    # the staging equality below is an exact-set proof and would otherwise
    # refuse an honest run that happens to contain one.
    for rel in sorted(r for r, e in source_inventory.items() if e.is_dir):
        try:
            (partial / rel).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            errors.append(f"{rel}: directory could not be created in the "
                          f"in-progress copy: {type(exc).__name__}: {exc}")

    for rel in sorted(r for r, e in source_inventory.items() if not e.is_dir):
        source_path = src / rel
        dest_path = partial / rel
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(source_path.read_bytes())
        except OSError as exc:
            msg = f"{rel}: copy failed: {type(exc).__name__}: {exc}"
            errors.append(msg)
            files.append(ArchiveFileRecheck(
                relative_path=rel, source_bytes=None, dest_bytes=None,
                source_sha256=None, dest_sha256=None, match=False))
            continue

        # THE RECHECK. Independent re-read of BOTH sides after the copy —
        # never reusing the bytes read during the copy itself — so this
        # is a genuine post-write proof, not a re-statement of the value
        # the copy loop already believed. The destination side is read
        # back OUT OF THE PARTIAL, and it is compared against the SOURCE:
        # the promotion below is a rename of bytes that have already been
        # proven equal to the sealed run's, never a copy that is trusted
        # because it was renamed.
        try:
            source_reread = source_path.read_bytes()
            dest_reread = dest_path.read_bytes()
        except OSError as exc:
            msg = f"{rel}: post-copy re-read failed: {type(exc).__name__}: {exc}"
            errors.append(msg)
            files.append(ArchiveFileRecheck(
                relative_path=rel, source_bytes=None, dest_bytes=None,
                source_sha256=None, dest_sha256=None, match=False))
            continue

        source_sha = hashlib.sha256(source_reread).hexdigest()
        dest_sha = hashlib.sha256(dest_reread).hexdigest()
        match = (source_sha == dest_sha
                 and len(source_reread) == len(dest_reread))
        if not match:
            errors.append(
                f"{rel}: sha256/bytes mismatch after copy "
                f"(source={source_sha}:{len(source_reread)} "
                f"dest={dest_sha}:{len(dest_reread)})")
        files.append(ArchiveFileRecheck(
            relative_path=rel, source_bytes=len(source_reread),
            dest_bytes=len(dest_reread), source_sha256=source_sha,
            dest_sha256=dest_sha, match=match))

    if errors:
        # NOTHING is left at the final name, so the next attempt is a
        # plain retry rather than a manual cleanup.
        return _report(False, _abandon_partial(errors), files=files,
                       inventory=_summary())

    # --- (3) POST-COPY SOURCE RE-INVENTORY ------------------------------
    # The sealed run directory must not have changed WHILE it was being
    # archived. The per-file recheck cannot see this: each file is
    # re-read immediately after its own copy, so a file mutated after its
    # recheck (while a LATER file was still being copied) passes every
    # per-file test and still ends up archived as bytes the sealed run no
    # longer holds.
    source_after, source_after_errors = _build_inventory(src)
    source_diff = _inventory_diff(
        source_inventory, source_after,
        other_label="the post-copy source re-inventory")
    if source_after_errors or source_diff:
        errors.extend(source_after_errors)
        errors.extend(source_diff)
        errors.append(
            "the sealed run directory CHANGED while it was being archived; "
            "the copy proves nothing about it and was discarded")
        return _report(False, _abandon_partial(errors), files=files,
                       inventory=_summary(source_stable=False))

    # --- (4) STAGING INVENTORY ------------------------------------------
    # Exact equality of the `.partial` tree against the source inventory.
    # The per-file recheck already covers each copied file's bytes; this
    # is the SET-level proof — an extra entry, a missing entry or a
    # divergent directory shape has no per-file recheck to fail.
    staging_inventory, staging_errors = _build_inventory(partial)
    staging_diff = _inventory_diff(
        source_inventory, staging_inventory,
        other_label="the staging (.partial) tree")
    if staging_errors or staging_diff:
        errors.extend(staging_errors)
        errors.extend(staging_diff)
        return _report(False, _abandon_partial(errors), files=files,
                       inventory=_summary(source_stable=True,
                                          staging_matches_source=False))

    # THE PROMOTION. One rename, after every file is copied and proven.
    # `dest` was checked non-existent above, so this creates it rather
    # than replacing anything; if it lost that race, the OSError is
    # captured like any other archive-side problem and the partial is
    # cleaned up, leaving whatever is at `dest` untouched.
    try:
        os.replace(partial, dest)
    except OSError as exc:
        errors.append(f"verified archive copy could not be promoted to its "
                      f"final name ({type(exc).__name__}: {exc}): {dest}")
        return _report(False, _abandon_partial(errors), files=files,
                       inventory=_summary(source_stable=True,
                                          staging_matches_source=True))

    # --- (5) FINAL INVENTORY, AFTER PROMOTION ---------------------------
    # A third full content pass, this time over the archive OF RECORD.
    # Everything verified so far was verified at a path that no longer
    # exists; this is the only step that speaks about the directory
    # anybody will actually read.
    final_inventory, final_errors = _build_inventory(dest)
    final_diff = _inventory_diff(
        source_inventory, final_inventory,
        other_label="the promoted archive directory")
    if final_errors or final_diff:
        errors.extend(final_errors)
        errors.extend(final_diff)
        # THE ONE FAILURE PATH THAT DELETES NOTHING. `dest` is no longer
        # an in-progress copy — it has been promoted — so it is EVIDENCE
        # of a divergence and is retained for adjudication, never
        # silently removed or "repaired".
        errors.append(
            f"the promoted archive directory FAILED its final inventory "
            f"verification and is deliberately RETAINED as evidence (not "
            f"deleted, not repaired): {dest}")
        return _report(False, errors, files=files,
                       inventory=_summary(source_stable=True,
                                          staging_matches_source=True,
                                          dest_matches_source=False))

    return _report(True, (), files=files,
                   inventory=_summary(source_stable=True,
                                      staging_matches_source=True,
                                      dest_matches_source=True))
