"""S0 OUTPUT PROOF — the sealed RUN DIRECTORY, as it exists on disk.

WHAT THIS IS
------------
A CHECKER. It answers exactly two questions about ONE run directory, and it
answers both from bytes that are already lying on the disk:

  Q1 (governance) do the five contract-specified `governance` keys inside the
     FINAL `S0_REPORT.json` FILE equal, key-for-key and value-for-value, what
     an INDEPENDENT pre-run/authority context says they must be?

  Q2 (sealed set)  does every entry of that report's
     `mc_handoff_manifest.sealed_files` — `sha256` and `bytes` — equal
     `Path.read_bytes()` of the actual file next to it in the run directory,
     and is the declared file set EXACTLY the set of artifacts present there
     (minus the self-excluded `S0_REPORT.json`, plus the run-infrastructure
     names the caller declares)?

It answers nothing else. It knows nothing about labels, NA, samples, costs,
Oracle, bootstrap, grid, volatility, event mapping or any strategy statistic,
and it deliberately does NOT extend (or read) the leaf/token evidence system.

WHY Q2 EXISTS AT ALL (the M6.1.6 gap this file closes)
-------------------------------------------------------
M6.1.6 wired production through an IN-MEMORY artifact map. The verdict it
produced therefore meant "what the renderer INTENDED to seal is correct" — a
claim about a `dict` that was about to be written, not about the bytes that
landed. That is the same fault line as F-a below: the check and the thing it
claims to check were not the same object.

They were measurably not the same object. `runner.py` writes each artifact
through `Path.write_text` with only an encoding — i.e. TEXT mode with the
platform default newline — while the manifest hashes `body.encode("utf-8")`
(LF). On Windows every artifact containing a newline is CRLF-translated on the
way to disk, so at HEAD `185e47f7` nine of the ten `sealed_files` digests do
NOT match the file they name (the tenth, `HANDOFF_ADMISSION.json`, is
single-line canonical JSON, so translation is a no-op on it). An in-memory
verdict was structurally incapable of seeing that. A disk verdict cannot miss
it: `_verify_sealed_set` re-hashes the file.

PRODUCTION ACCEPTANCE IS THE DISK PATH, AND ONLY THE DISK PATH
---------------------------------------------------------------
`prove_governance` takes `report_path=<run_dir>/S0_REPORT.json` and nothing
else. The in-memory route is not a parameter of it any more: `sealed_artifacts=`
survives ONLY as a poison pill that always raises `ProofRefused`, so the old
production call site fails closed and loudly instead of quietly continuing to
mean the weaker thing.

The in-memory check still has a job — it is a cheap PRE-WRITE screen that stops
a wrong `governance` block from ever reaching a file — so it lives on as
`screen_governance_draft`, and it returns a `DraftScreen`, NOT a
`GovernanceProof`. A `DraftScreen` has no `ok` field, its `ok` property raises,
and `bool()` of it raises: a caller who writes the usual `if not result.ok:`
acceptance gate around it gets an exception, never a pass. The invariant is
structural and is asserted by test: **a `GovernanceProof` object can only come
into existence from bytes read off the disk**, and its `actual_source` is
enforced to be `"file"` in `__post_init__`.

WHAT THIS IS NOT (structural, not merely promised)
--------------------------------------------------
It is NOT a generator. The two public callables return frozen dataclasses whose
every field is a `bool`, `int`, `str` or `tuple[str, ...]` (enforced in
`__post_init__`). No public name is bound to the expected-tree builder, no
returned value is a Mapping, and no problem string carries an expected VALUE or
any digest — so a renderer cannot use this module, or its output, to
build/patch/backfill `governance.*` or a `sealed_files` entry. The module
contains no filesystem write call of any kind; its entire I/O vocabulary is
`Path.read_bytes`, `Path.is_file`, `Path.is_symlink` and `Path.iterdir`, all
read-only, all confined to the run directory (`report_path.parent`) and its
immediate entries — a declared name that is not a plain filename is refused
before it is ever joined onto a path.

THREE MEASURED FAILURES THIS DESIGN REFUSES TO REPEAT
-----------------------------------------------------
F-a  "the check ran before the thing it claimed to check existed".
     The pre-existing evidence pass runs at `scripts/s0_real_run.py:1013-1014`,
     i.e. BEFORE `HANDOFF_ADMISSION.json` (:1019), `S0_REPORT.md` (:1035), the
     manifest injection (:1050-1057) and `S0_REPORT.json` (:1066) exist, so its
     target could not have been the sealed bytes. M6.1.6 improved on that but
     still ran against the in-memory map. THIS module refuses to run unless the
     final `S0_REPORT.json` is a FILE: no file, or an empty file, is a
     `ProofRefused`, never a pass. Called anywhere before the Stage-E write-out
     loop has finished, it refuses by construction.

F-b  "the expected side was a mirror of the target side, and the pass was a
     literal". `evidence.py:4020-4042` regenerates six subtrees with the same
     six functions that produced them and reports a hard-coded `6` as its
     compared-count — a check structurally incapable of failing. Here the
     governance expectation comes from a `SourceContext` (pre-run registry
     snapshot + frozen-hash authority + its independent on-disk observations +
     the approved engineering-seed provenance) that never touches the report,
     and BOTH counters (`comparisons_performed`, `disk_checks_performed`) are
     incremented by the loops themselves, one increment per leaf/file-check
     actually executed. `ok` requires no problems AND both counters equal their
     required values AND both required values are non-zero. A skipped check
     cannot pass.

F-c  "expected domain collapse". `evidence.py:2052-2054` sizes its
     `frozen_hash_paths` axis from "the DECLARED governance.frozen_hashes key
     set", i.e. from the very object it guards — so emptying the guarded field
     took the axis from 7 to 0 and the guard evaporated. Two defences here:
       * governance — the expected key domain is `CONTRACT_GOVERNANCE_KEYS` (a
         literal transcription of the content contract) and
         `sorted(context.frozen_hash_authority)` (the freeze registry);
       * sealed set — `disk_checks_required` IS sized from the manifest, which
         is the guarded object, so it is guarded from the other side: the file
         universe comes from `Path.iterdir()` of the run directory, so emptying
         `sealed_files` does not shrink the domain, it turns every artifact on
         disk into a `disk_extra_file` problem (and an empty `sealed_files` is
         itself `manifest_missing`).

EXPECTED-SIDE SOURCES (all supplied by the caller; none read from the report)
-----------------------------------------------------------------------------
  * `authorization_snapshot` — the EXISTING pre-run trial/run identity snapshot
    produced by `RealChain.authorization_snapshot()`
    (`scripts/s0_real_run.py:2339-2364`), taken at Stage A and re-verified
    immediately before the RUN_STARTED transition. Supplies `trial_id`,
    `authorized_commit`, and — as the EXISTING pre-run registry-sequence
    snapshot — `event_sequence` (`len(parse_registry_events(text))`).
  * `frozen_hash_authority` — `itsf.guards.FROZEN_HASHES`
    (`src/itsf/guards.py:20-39`), the freeze-registry authority mapping.
  * `frozen_hash_observations` — the compute-time byte-level re-hash of those
    same files. Authority and observation are compared against EACH OTHER
    before either is used as an expectation, so a frozen file mutated on disk
    is a problem rather than an invisible pass.
  * `engineering_seed` + `engineering_seed_provenance` — the approved
    provenance stamp (`scripts/s0_real_run.py:37-39`, DR-02 / packet §5; prose
    at `src/itsf/s0/handoff.py:226-228`).
  * `infrastructure_files` (at the call site, not in the context) — the names
    the RUN INFRASTRUCTURE writes into the run directory, which the RENDERER
    did not produce and which therefore must not appear in `sealed_files`
    (today: `manifest.jsonl` from `runner.py`, `REGISTRY_AFTER_RUN_STARTED.json`
    from the atomic run-start, and the failure-path `HALF_TRANSITION.md` /
    `INCIDENT_*.md`). It is REQUIRED — there is no permissive default — and it
    is a property of the runner, never derived from the report.

DELIBERATE FAILURE MODE (not a bug)
------------------------------------
`RealChain.compute()` RE-READS the registry (`scripts/s0_real_run.py:2305`,
`find_authorization_event` / `parse_registry_events`) and stamps THAT into the
governance block, while this module's expectation comes from the PRE-RUN
snapshot. If the registry moved in between — an inserted event, a re-signed
authorization — expected != actual and this proof FAILS. That is the point.

HONEST COVERAGE
---------------
`ok=True` means: every contract-specified governance key was present, correctly
typed and exactly equal to the independent context; and every file the report
declares sealed is byte-identical to its declaration, with no artifact on disk
left undeclared. It does NOT mean:

  * the report is bound to the pre-run registry BYTES — `governance.*` carries
    no `registry_sha256` and no `exact_authorization_text_sha256`, and no
    authorization exists to add them, so those snapshot facts are reported as
    PARTIAL (derived, not hand-listed) instead of silently dropped. The formal
    report schema is NOT extended by this module.
  * that a `sealed_files` DECLARATION is the one the renderer meant to write.
    Q2 proves declaration == disk. A tamperer able to rewrite BOTH an artifact
    and its manifest entry inside `S0_REPORT.json` produces a self-consistent
    pair that Q2 alone cannot separate from an honest one; what catches that is
    Q1 (whose expected side never came from the report) when the tamper touches
    `governance.*`, and the Stage-F append-only chain (`manifest.jsonl`, hashed
    at write time by `runner.py`) when it does not. This module is one axis of
    that pair, not a replacement for it — see
    `test_manifest_self_consistency_is_not_sufficient`. `sealed_files` carries
    no field binding it to anything outside the report and there is no
    authorization to add one, so every proof that ran the sealed-set axis
    DISCLOSES this as
    `governance_proof_partial:sealed_file_declaration_not_bound_to_an_external_authority`
    rather than letting `ok=True` read as the stronger claim.
  * anything about the CONTENT of a non-report artifact. `sealed_files` fixes
    its bytes; what those bytes should have SAID is `report.validate_sealed_files`'
    question, not this module's.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType

__all__ = (
    "FINAL_REPORT_NAME",
    "MANIFEST_SECTION",
    "SEALED_FILES_KEY",
    "SELF_EXCLUDED_KEY",
    "CONTRACT_GOVERNANCE_KEYS",
    "CONTRACT_FROZEN_HASH_COUNT",
    "SEALED_ENTRY_KEYS",
    "REFUSAL_REPORT_MISSING",
    "REFUSAL_MANIFEST_MISSING",
    "REFUSAL_DECLARED_FILE_MISSING",
    "REFUSAL_DISK_EXTRA_FILE",
    "REFUSAL_DECLARED_BYTES_MISMATCH",
    "REFUSAL_DECLARED_SHA256_MISMATCH",
    "REFUSAL_CLASSES",
    "ProofRefused",
    "SourceContext",
    "GovernanceProof",
    "DraftScreen",
    "prove_governance",
    "screen_governance_draft",
    # F-2 key-claims release gate (S0 closeout, Aaron ruling 2026-08-10) —
    # a CHECKER surface like the two above, never a producer.
    "KEY_CLAIM_IDS",
    "ResearchClaimsContext",
    "KeyClaimsReport",
    "verify_key_claims",
)

# The ONE artifact whose bytes may be the actual side. Hard-coded on purpose:
# it is not a parameter, so no caller can point the proof at an evidence mirror
# copy, a pre-injection draft, or any other look-alike and have it treated as
# the authority. The RUN DIRECTORY is likewise not a parameter — it is
# `report_path.parent`, so "verify the report over here against the artifacts
# over there" is not expressible.
FINAL_REPORT_NAME = "S0_REPORT.json"

# Where the sealed-set declaration lives inside that report
# (scripts/s0_real_run.py:1050-1057).
MANIFEST_SECTION = "mc_handoff_manifest"
SEALED_FILES_KEY = "sealed_files"
SELF_EXCLUDED_KEY = "self_excluded"

# Exactly the two facts a sealed-file entry declares about the bytes.
SEALED_ENTRY_KEYS: frozenset[str] = frozenset({"sha256", "bytes"})

# The EXACT governance key set the content contract specifies, transcribed from
# S0_REPORT_CONTENT_CONTRACT.md §A row A12 (line 40):
#   "trial_id、authorized_commit、engineering_seed（出处戳记）、
#    冻结哈希七项复述、registry 事件序号快照"
# i.e. trial_id, authorized_commit, engineering_seed, the seven-item frozen-hash
# restatement (`frozen_hashes`), and the registry event-sequence snapshot
# (`registry_sequence_snapshot`). The same five names are the allowlist at
# src/itsf/s0/report.py:809-812 (`_GOVERNANCE_ALLOWED_KEYS`); the agreement of
# these two independently-maintained sets is asserted by the test suite, NOT
# assumed here — this constant is deliberately not imported from report.py so
# the expected domain does not depend on the module that also validates.
CONTRACT_GOVERNANCE_KEYS: frozenset[str] = frozenset({
    "trial_id", "authorized_commit", "engineering_seed", "frozen_hashes",
    "registry_sequence_snapshot"})

# "冻结哈希七项复述" — the contract fixes the restatement at seven items
# (report.py:2444 checks the same count on the actual side).
CONTRACT_FROZEN_HASH_COUNT = 7

# Which pre-run snapshot facts have a home in the contract key set. Facts NOT
# listed here have no governance field to be proven against; that gap is
# DERIVED into the PARTIAL list rather than hidden (and rather than "fixed" by
# extending the sealed schema, which this module has no authority to do).
_SNAPSHOT_FIELD_TO_GOVERNANCE: Mapping[str, str] = MappingProxyType({
    "trial_id": "trial_id",
    "authorized_commit": "authorized_commit",
    "event_sequence": "registry_sequence_snapshot",
})

_ROOT = "governance"
_P = "governance_proof_"

# The ONE value `GovernanceProof.actual_source` may hold. Enforced, not
# documented: there is no code path that constructs a proof from anything but
# a file, and `__post_init__` rejects any other source string outright.
_DISK_SOURCE = "file"

# The ONE value `DraftScreen.acceptance` may hold — a constant that reads, at
# every call site and in every log, as "this is not the verdict".
_NOT_AN_ACCEPTANCE = "not_an_acceptance:disk_proof_required"

# --- the six named failure classes of the SEALED-SET axis -------------------
# One deterministic, individually-named string per class. The first is the
# text of a `ProofRefused` (no report file => no verdict is possible at all);
# the other five are problem codes on a returned `ok=False` proof, emitted as
# "<CLASS>:<node path>". Node paths only — never a digest, never a byte count,
# never a governance value.
REFUSAL_REPORT_MISSING = f"{_P}report_missing"
REFUSAL_MANIFEST_MISSING = f"{_P}manifest_missing"
REFUSAL_DECLARED_FILE_MISSING = f"{_P}declared_file_missing"
REFUSAL_DISK_EXTRA_FILE = f"{_P}disk_extra_file"
REFUSAL_DECLARED_BYTES_MISMATCH = f"{_P}declared_bytes_mismatch"
REFUSAL_DECLARED_SHA256_MISMATCH = f"{_P}declared_sha256_mismatch"

REFUSAL_CLASSES: tuple[str, ...] = (
    REFUSAL_REPORT_MISSING,
    REFUSAL_MANIFEST_MISSING,
    REFUSAL_DECLARED_FILE_MISSING,
    REFUSAL_DISK_EXTRA_FILE,
    REFUSAL_DECLARED_BYTES_MISMATCH,
    REFUSAL_DECLARED_SHA256_MISMATCH,
)

# Hardening classes beyond the six required ones (a malformed or dangerous
# declaration must not silently become "no check").
_ENTRY_MALFORMED = f"{_P}manifest_entry_malformed"
_ENTRY_UNSAFE_NAME = f"{_P}manifest_entry_unsafe_name"
_SELF_EXCLUSION_VIOLATED = f"{_P}self_exclusion_violated"
_DISK_ENTRY_NOT_REGULAR = f"{_P}disk_entry_not_regular"
_DISK_CHECK_COUNT = f"{_P}disk_check_count"

# Honest-coverage marker for the sealed-set axis. Q2 proves DECLARATION ==
# DISK; it cannot prove the declaration is the one the renderer meant, because
# `sealed_files` has no field tying it to anything outside the report and this
# module has no authority to add one. Emitted whenever that axis actually ran,
# so the claim is never read as stronger than it is; absent when there was no
# sealed-set claim to qualify.
_PARTIAL_DECLARATION_UNBOUND = (
    f"{_P}partial:sealed_file_declaration_not_bound_to_an_external_authority")

_HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")

# Sentinel for "the caller did not pass this at all", so that an EXPLICIT empty
# infrastructure declaration (a run directory holding nothing but artifacts)
# stays expressible while a FORGOTTEN one refuses.
_REQUIRED = object()


class ProofRefused(RuntimeError):
    """The proof could not be ATTEMPTED.

    Distinct from a failing proof. A refusal means the caller asked for a
    verdict that cannot honestly be given — the final `S0_REPORT.json` does not
    exist on disk yet, the artifact offered is not that file, the caller tried
    to route production acceptance through the removed in-memory path, or the
    independent context is structurally unusable so no expectation can be
    stated. Refusals are exceptions precisely so they cannot be mistaken for
    `ok=False` and cannot be silently swallowed into a seal.
    """


def _is_plain_filename(name: object) -> bool:
    """True only for a name that can be joined onto the run directory without
    leaving it: a non-empty string, no separator of either flavour, no drive or
    root, and unchanged by `PurePath.name`. Checked BEFORE any path join, so a
    hostile declaration never reaches the filesystem."""
    if not isinstance(name, str) or not name or name in (".", ".."):
        return False
    if "/" in name or "\\" in name or "\x00" in name:
        return False
    try:
        return Path(name).name == name
    except (ValueError, OSError):        # pragma: no cover - defensive
        return False


# ---------------------------------------------------------------------------
# expected side
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceContext:
    """The INDEPENDENT expected-side inputs. Nothing here comes from the report.

    Every field is validated at construction; a structurally unusable context
    raises `ProofRefused` immediately, at the wiring site, rather than
    degrading into a weaker check later.

    Fields
    ------
    authorization_snapshot
        The pre-run identity/registry-sequence snapshot dict as produced by
        `RealChain.authorization_snapshot()` (`scripts/s0_real_run.py:2339`).
        Must carry `trial_id` (non-empty str), `authorized_commit` (40 lowercase
        hex) and `event_sequence` (int >= 1). Extra facts are welcome and are
        reported as PARTIAL coverage.
    frozen_hash_authority
        `itsf.guards.FROZEN_HASHES` — the freeze-registry `{path: sha256}`.
    frozen_hash_observations
        Independently observed `{path: sha256}` of the same files at compute
        time (`scripts/s0_real_run.py:2332-2334`). Never an evidence mirror.
    engineering_seed
        The approved run-infra provenance stamp value (strict `int`).
    engineering_seed_provenance
        Where that approval lives (e.g. "DR-02 / packet §5"). Required so the
        proof can state WHY the seed is what it is even though the sealed
        schema has nowhere to put it (see PARTIAL).
    """

    authorization_snapshot: Mapping[str, object]
    frozen_hash_authority: Mapping[str, str]
    frozen_hash_observations: Mapping[str, str]
    engineering_seed: int
    engineering_seed_provenance: str

    def __post_init__(self) -> None:
        # M6.1.6 review A3-1: VALIDATE THE OBJECT THAT BECOMES THE
        # EXPECTATION, never a different view of it. The frozen expectation
        # below is built with `dict(snap)`, which goes through
        # `__iter__`/`__getitem__`; validating via `snap.get(...)` would let
        # a Mapping whose `.get()` and `__getitem__` disagree pass the
        # checks and then supply DIFFERENT values as the expectation. This
        # is the "validate X, use Y" class the config gateway spent M6.1.4
        # eliminating; the fix is to materialise first and validate the
        # materialised copy, which is what every read below now uses.
        snap_in = self.authorization_snapshot
        if not isinstance(snap_in, Mapping):
            raise ProofRefused(
                "source_context: authorization_snapshot is not a mapping")
        try:
            snap = dict(snap_in)
        except Exception:
            raise ProofRefused(
                "source_context: authorization_snapshot is not materialisable")
        trial = snap.get("trial_id")
        if not isinstance(trial, str) or not trial:
            raise ProofRefused(
                "source_context: authorization_snapshot.trial_id absent or "
                "not a non-empty string")
        commit = snap.get("authorized_commit")
        if not isinstance(commit, str) or not _HEX40.match(commit):
            raise ProofRefused(
                "source_context: authorization_snapshot.authorized_commit is "
                "not a 40-hex commit (an unauthorized run has nothing to prove)")
        seq = snap.get("event_sequence")
        if type(seq) is not int or seq < 1:
            raise ProofRefused(
                "source_context: authorization_snapshot.event_sequence is not "
                "a positive int")

        authority = self.frozen_hash_authority
        if not isinstance(authority, Mapping) or not authority:
            raise ProofRefused(
                "source_context: frozen_hash_authority is not a non-empty "
                "mapping")
        for path, digest in authority.items():
            if not isinstance(path, str) or not path:
                raise ProofRefused(
                    "source_context: frozen_hash_authority has a non-string "
                    "path key")
            if not isinstance(digest, str) or not _HEX64.match(digest):
                raise ProofRefused(
                    "source_context: frozen_hash_authority holds a non-sha256 "
                    "value")
        observations = self.frozen_hash_observations
        if not isinstance(observations, Mapping) or not observations:
            # Same discipline as evidence.py:1189-1191: an EMPTY observation set
            # is fail-closed, never "nothing to disagree with".
            raise ProofRefused(
                "source_context: frozen_hash_observations is empty — a "
                "re-hash of the frozen files is required, not optional")

        if type(self.engineering_seed) is not int:
            raise ProofRefused(
                "source_context: engineering_seed is not a strict int")
        if (not isinstance(self.engineering_seed_provenance, str)
                or not self.engineering_seed_provenance.strip()):
            raise ProofRefused(
                "source_context: engineering_seed_provenance is required (the "
                "approved provenance stamp for the seed value)")

        # Freeze the mappings behind read-only proxies over private copies: the
        # expectation cannot be swapped out from under the proof after the
        # context has been constructed.
        object.__setattr__(self, "authorization_snapshot",
                           MappingProxyType(dict(snap)))
        object.__setattr__(self, "frozen_hash_authority",
                           MappingProxyType(dict(authority)))
        object.__setattr__(self, "frozen_hash_observations",
                           MappingProxyType(dict(observations)))


def _expected_tree(context: "SourceContext") -> dict:
    """Build the EXPECTED `governance` tree from the context ALONE.

    Deliberately takes no report, no artifact map and no path: the expected key
    domain (and every expected value) is derivable with the sealed file absent
    from the machine. NO coercion happens here — the context's types are the
    expectation, so `20260731.0` in a report is a TYPE failure, not a rounding.

    Private by construction and NOT exported: nothing in `__all__` is bound to
    it, so this module offers no entry point a renderer could call to obtain a
    governance block.
    """
    snap = context.authorization_snapshot
    tree = {
        "trial_id": snap["trial_id"],
        "authorized_commit": snap["authorized_commit"],
        "engineering_seed": context.engineering_seed,
        "registry_sequence_snapshot": snap["event_sequence"],
        "frozen_hashes": {path: context.frozen_hash_authority[path]
                          for path in sorted(context.frozen_hash_authority)},
    }
    if set(tree) != CONTRACT_GOVERNANCE_KEYS:
        # Unreachable while this function and the constant agree; it exists so
        # that editing one without the other refuses rather than drifts.
        raise ProofRefused(
            "expected tree does not match the contract key set "
            "(S0_REPORT_CONTENT_CONTRACT.md §A12)")
    return tree


def _leaf_count(node: object) -> int:
    """Number of scalar leaves in an expected tree — the number of comparisons
    the proof MUST perform before it may report a pass."""
    if isinstance(node, Mapping):
        return sum(_leaf_count(v) for v in node.values())
    return 1


def _context_problems(context: "SourceContext") -> list[str]:
    """Problems in the EXPECTED side itself, found by comparing the freeze
    registry against the independently observed on-disk digests.

    This is what keeps the expected side from being a single unchecked constant:
    the authority and the observation are two derivations of the same fact, and
    a disagreement is surfaced as a problem instead of being resolved silently
    in favour of either one.
    """
    problems: list[str] = []
    authority = context.frozen_hash_authority
    observations = context.frozen_hash_observations
    if len(authority) != CONTRACT_FROZEN_HASH_COUNT:
        problems.append(f"{_P}context_frozen_hash_count")
    for path in sorted(authority):
        node = f"{_ROOT}.frozen_hashes[{path}]"
        if path not in observations:
            problems.append(f"{_P}context_observation_missing:{node}")
            continue
        observed = observations[path]
        if not isinstance(observed, str) or not _HEX64.match(observed):
            problems.append(f"{_P}context_observation_malformed:{node}")
        elif observed != authority[path]:
            problems.append(f"{_P}context_observation_conflict:{node}")
    for path in sorted(observations):
        if path not in authority:
            problems.append(
                f"{_P}context_observation_extra:{_ROOT}.frozen_hashes[{path}]")
    return problems


def _partial_coverage(context: "SourceContext") -> list[str]:
    """DERIVED honest-coverage markers: expected-side facts the contract key set
    has no field for. Nothing here is hand-listed — if `governance.*` ever
    gains an authorized field for one of these, the marker disappears by
    itself. This module never extends the schema to close a gap."""
    partial: list[str] = []
    for fact in sorted(context.authorization_snapshot):
        target = _SNAPSHOT_FIELD_TO_GOVERNANCE.get(fact)
        if target is None or target not in CONTRACT_GOVERNANCE_KEYS:
            partial.append(f"{_P}partial:snapshot_fact_absent_from_schema:{fact}")
    if "engineering_seed_provenance" not in CONTRACT_GOVERNANCE_KEYS:
        partial.append(
            f"{_P}partial:engineering_seed_provenance_absent_from_schema")
    return partial


# ---------------------------------------------------------------------------
# comparison — governance axis
# ---------------------------------------------------------------------------

def _json_type(value: object) -> str:
    """Strict JSON type name. `bool` is NOT `int` (so `true` can never satisfy
    an int expectation), `7.0` is NOT `7`, and `"7"` is neither."""
    if value is None:
        return "null"
    if type(value) is bool:
        return "bool"
    if type(value) is int:
        return "int"
    if type(value) is float:
        return "float"
    if type(value) is str:
        return "str"
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    return type(value).__name__


def _node_path(parent: str, key: str) -> str:
    """`governance.trial_id` at the root; `governance.frozen_hashes[<path>]`
    below it. Bracket form because frozen paths contain both '.' and '/' —
    dotted notation there would be ambiguous, and a problem string that cannot
    be read back to a unique node is not a deterministic problem string."""
    return f"{parent}.{key}" if parent == _ROOT else f"{parent}[{key}]"


def _compare(expected: object, actual: object, path: str,
             problems: list[str], counter: list[int]) -> None:
    """EXACT structural comparison. Every divergence class gets its own
    deterministic code, and `absent` / `explicit null` are never merged:

      key_missing    the expected key is not in the actual object at all
      null_value     the key IS there and holds an explicit JSON null
      type_mismatch  present, non-null, wrong JSON type
      value_mismatch present, right type, different value
      key_unexpected present in the actual object, outside the expected domain

    Problem strings carry NODE PATHS ONLY — never an expected or actual value —
    so the output of a failing proof still cannot be used to reconstruct a
    governance block.
    """
    if actual is None and expected is not None:
        problems.append(f"{_P}null_value:{path}")
        return
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            problems.append(f"{_P}type_mismatch:{path}")
            return
        for key in sorted(expected):
            child = _node_path(path, key)
            if key not in actual:
                problems.append(f"{_P}key_missing:{child}")
            else:
                _compare(expected[key], actual[key], child, problems, counter)
        for key in sorted(actual):
            if key not in expected:
                problems.append(f"{_P}key_unexpected:{_node_path(path, key)}")
        return
    # scalar leaf: this line, and only this line, is what makes a pass real.
    counter[0] += 1
    if _json_type(actual) != _json_type(expected):
        problems.append(f"{_P}type_mismatch:{path}")
        return
    if actual != expected:
        problems.append(f"{_P}value_mismatch:{path}")


def _parse_report(raw: bytes, problems: list[str]) -> "Mapping | None":
    """The actual side, parsed from those bytes and nothing else."""
    try:
        root = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        problems.append(f"{_P}report_unparsable")
        return None
    if not isinstance(root, Mapping):
        problems.append(f"{_P}report_root_not_object")
        return None
    return root


def _governance_axis(context: "SourceContext", root: "Mapping | None",
                     problems: list[str], counter: list[int]) -> int:
    """Run Q1 and return the number of comparisons that were REQUIRED."""
    expected = _expected_tree(context)
    required = _leaf_count(expected)
    problems.extend(_context_problems(context))
    if root is not None:
        if _ROOT not in root:
            problems.append(f"{_P}section_missing")
        else:
            _compare(expected, root[_ROOT], _ROOT, problems, counter)
    if counter[0] != required:
        problems.append(f"{_P}comparison_count")
    return required


# ---------------------------------------------------------------------------
# comparison — sealed-set axis (Q2), against the bytes on disk
# ---------------------------------------------------------------------------

def _sealed_node(name: str) -> str:
    return f"{MANIFEST_SECTION}.{SEALED_FILES_KEY}[{name}]"


def _read_declarations(root: "Mapping | None", problems: list[str]
                       ) -> tuple[dict, set]:
    """Parse and validate `mc_handoff_manifest.sealed_files` WITHOUT touching
    the filesystem.

    Returns `(declared, named)` where `declared` maps a safe filename to its
    `(sha256, bytes)` declaration — only entries that are well-formed enough to
    be checkable — and `named` is every string name the manifest mentioned at
    all (valid or not), so that a name whose declaration was rejected is not
    ALSO reported as an undeclared file on disk.
    """
    declared: dict[str, tuple[str, int]] = {}
    named: set[str] = set()
    if root is None:
        return declared, named

    manifest = root.get(MANIFEST_SECTION)
    if not isinstance(manifest, Mapping):
        problems.append(f"{REFUSAL_MANIFEST_MISSING}:{MANIFEST_SECTION}")
        return declared, named

    # The self-exclusion is part of the declaration, not an afterthought: the
    # report must SAY it excludes itself, and must not then list itself.
    excluded = manifest.get(SELF_EXCLUDED_KEY)
    if (not isinstance(excluded, (list, tuple))
            or list(excluded) != [FINAL_REPORT_NAME]):
        problems.append(f"{_SELF_EXCLUSION_VIOLATED}:"
                        f"{MANIFEST_SECTION}.{SELF_EXCLUDED_KEY}")

    sealed = manifest.get(SEALED_FILES_KEY)
    if not isinstance(sealed, Mapping) or not sealed:
        problems.append(f"{REFUSAL_MANIFEST_MISSING}:"
                        f"{MANIFEST_SECTION}.{SEALED_FILES_KEY}")
        return declared, named

    # Deterministic order over a possibly non-string key set: string keys sort
    # among themselves, anything else is reported POSITIONALLY — a hostile key
    # is never interpolated into a problem string, so a declaration can neither
    # forge a node path nor smuggle a newline into the problem tuple.
    string_keys = sorted(k for k in sealed if isinstance(k, str))
    n_other = sum(1 for k in sealed if not isinstance(k, str))
    for index in range(n_other):
        problems.append(f"{_ENTRY_UNSAFE_NAME}:"
                        f"{MANIFEST_SECTION}.{SEALED_FILES_KEY}"
                        f"[#non_str_{index}]")

    for index, name in enumerate(string_keys):
        named.add(name)
        if not _is_plain_filename(name):
            problems.append(f"{_ENTRY_UNSAFE_NAME}:"
                            f"{MANIFEST_SECTION}.{SEALED_FILES_KEY}"
                            f"[#unsafe_{index}]")
            continue
        if name == FINAL_REPORT_NAME:
            # The report carries the manifest, so it cannot hash itself; the
            # self-exclusion is the existing discipline and adding the report
            # back into the sealed set is refused, never quietly honoured.
            problems.append(f"{_SELF_EXCLUSION_VIOLATED}:{_sealed_node(name)}")
            continue
        entry = sealed[name]
        if not isinstance(entry, Mapping) or set(entry) != SEALED_ENTRY_KEYS:
            problems.append(f"{_ENTRY_MALFORMED}:{_sealed_node(name)}")
            continue
        digest = entry["sha256"]
        size = entry["bytes"]
        if (not isinstance(digest, str) or not _HEX64.match(digest)
                or type(size) is not int or size < 0):
            problems.append(f"{_ENTRY_MALFORMED}:{_sealed_node(name)}")
            continue
        declared[name] = (digest, size)
    return declared, named


def _verify_sealed_set(run_dir: Path, declared: Mapping[str, tuple[str, int]],
                       named: "set[str]", infrastructure: "frozenset[str]",
                       problems: list[str], counter: list[int]
                       ) -> tuple[int, int]:
    """Run Q2 against the bytes in `run_dir`.

    Three checks per declared file — exists, byte length, sha256 — each
    counted only when it is actually executed, so a file that is missing shows
    up BOTH as `declared_file_missing` and as a short check count. Then the
    directory is walked and every entry that is neither declared, nor the
    self-excluded report, nor declared run infrastructure is an extra.

    Returns `(checks_required, entries_seen)`.
    """
    required = 3 * len(declared)
    for name in sorted(declared):
        digest, size = declared[name]
        node = _sealed_node(name)
        target = run_dir / name
        counter[0] += 1                                   # check 1: existence
        if target.is_symlink():
            # A symlink can point anywhere; its bytes are not the run
            # directory's bytes, so it is not an admissible sealed artifact.
            problems.append(f"{_DISK_ENTRY_NOT_REGULAR}:{node}")
            continue
        if not target.is_file():
            problems.append(f"{REFUSAL_DECLARED_FILE_MISSING}:{node}")
            continue
        raw = target.read_bytes()
        counter[0] += 1                                   # check 2: byte count
        if len(raw) != size:
            problems.append(f"{REFUSAL_DECLARED_BYTES_MISMATCH}:{node}")
        counter[0] += 1                                   # check 3: digest
        if hashlib.sha256(raw).hexdigest() != digest:
            problems.append(f"{REFUSAL_DECLARED_SHA256_MISMATCH}:{node}")

    # F-c defence for THIS axis: the universe is the DIRECTORY, not the
    # manifest, so emptying the manifest cannot empty the domain.
    accounted = named | {FINAL_REPORT_NAME} | infrastructure
    entries = sorted(entry.name for entry in run_dir.iterdir())
    for entry_name in entries:
        if entry_name not in accounted:
            problems.append(f"{REFUSAL_DISK_EXTRA_FILE}:run_dir[{entry_name}]")
    if counter[0] != required:
        problems.append(_DISK_CHECK_COUNT)
    return required, len(entries)


# ---------------------------------------------------------------------------
# results
# ---------------------------------------------------------------------------

def _reject_content_shaped(obj) -> None:
    """Structural guarantee, enforced rather than documented: no field of a
    result may ever carry report-shaped content."""
    for f in fields(obj):
        value = getattr(obj, f.name)
        if isinstance(value, tuple):
            if not all(type(item) is str for item in value):
                raise TypeError(
                    f"{type(obj).__name__}.{f.name}: tuple fields hold strings "
                    "only")
        elif type(value) not in (bool, int, str):
            raise TypeError(
                f"{type(obj).__name__}.{f.name}: a result carries only bool/"
                "int/str/tuple-of-str — never content")


@dataclass(frozen=True)
class GovernanceProof:
    """The verdict, and the ONLY object in this module that is one.

    It can be produced by exactly one code path — `prove_governance`, reading a
    real `S0_REPORT.json` file — and `__post_init__` enforces that by rejecting
    any `actual_source` other than `"file"`. So "there is a `GovernanceProof`"
    and "the bytes on disk were examined" are the same statement.

    `ok` is True only when the proof performed EVERY required comparison on
    BOTH axes and found no problem. `partial` is disclosure, not a verdict: it
    lists the expected-side facts the sealed schema has no field for, and it
    never weakens or strengthens `ok`.
    """

    ok: bool
    problems: tuple[str, ...]
    partial: tuple[str, ...]
    comparisons_performed: int
    comparisons_required: int
    disk_checks_performed: int
    disk_checks_required: int
    sealed_files_declared: int
    run_dir_entries_seen: int
    report_sha256: str
    actual_source: str

    def __post_init__(self) -> None:
        _reject_content_shaped(self)
        if self.actual_source != _DISK_SOURCE:
            raise ValueError(
                "GovernanceProof.actual_source must be "
                f"{_DISK_SOURCE!r}: a proof exists only for bytes read off "
                "the disk (the in-memory route yields a DraftScreen, which is "
                "not an acceptance)")


@dataclass(frozen=True)
class DraftScreen:
    """The result of the PRE-WRITE screen. Deliberately NOT a verdict.

    `screen_governance_draft` looks at a `dict` the renderer is about to write.
    That is useful — it stops a wrong governance block from ever becoming a
    file — but it says nothing about what lands on disk, so this type is built
    so that it cannot be used as an acceptance:

      * it has no `ok` FIELD, and its `ok` PROPERTY raises `ProofRefused`;
      * `bool()` of it raises `TypeError`;
      * it is not a `GovernanceProof` and never becomes one.

    A caller who copies the usual `if not result.ok: raise` gate around this
    object gets an exception at the miswiring site, which is the entire point.
    """

    blocking_problems: tuple[str, ...]
    partial: tuple[str, ...]
    comparisons_performed: int
    comparisons_required: int
    draft_sha256: str
    acceptance: str

    def __post_init__(self) -> None:
        _reject_content_shaped(self)
        if self.acceptance != _NOT_AN_ACCEPTANCE:
            raise ValueError("DraftScreen.acceptance is fixed")

    @property
    def ok(self) -> bool:
        raise ProofRefused(
            "DraftScreen has no `ok`: the in-memory screen is NOT a production "
            "acceptance route. Accept only prove_governance(context, "
            f"report_path=<run_dir>/{FINAL_REPORT_NAME}, "
            "infrastructure_files=...), which reads the bytes that actually "
            "landed on disk. To gate on the screen, test "
            "`screen.blocking_problems`.")

    def __bool__(self) -> bool:
        raise TypeError(
            "a DraftScreen is not a verdict and has no truth value; test "
            "`screen.blocking_problems` explicitly")


# ---------------------------------------------------------------------------
# the two public entry points
# ---------------------------------------------------------------------------

def _validated_infrastructure(infrastructure_files) -> "frozenset[str]":
    if infrastructure_files is _REQUIRED:
        raise ProofRefused(
            "prove_governance: infrastructure_files= is REQUIRED — name the "
            "files the RUN INFRASTRUCTURE writes into the run directory (e.g. "
            "manifest.jsonl, REGISTRY_AFTER_RUN_STARTED.json). Pass an empty "
            "tuple to assert the directory holds nothing but artifacts; there "
            "is no permissive default, because a forgotten declaration would "
            "silently turn every extra file into an accepted one.")
    if isinstance(infrastructure_files, (str, bytes)) or not isinstance(
            infrastructure_files, Iterable):
        raise ProofRefused(
            "prove_governance: infrastructure_files must be an iterable of "
            "file NAMES (a bare string would iterate as characters)")
    names = frozenset(infrastructure_files)
    for name in names:
        if not _is_plain_filename(name):
            raise ProofRefused(
                "prove_governance: infrastructure_files holds something that "
                "is not a plain file name inside the run directory")
    if FINAL_REPORT_NAME in names:
        raise ProofRefused(
            f"prove_governance: {FINAL_REPORT_NAME} is the sealed report, not "
            "run infrastructure — it is self-excluded by the manifest and "
            "accounted for on its own")
    return names


def prove_governance(context: "SourceContext", *,
                     report_path: "str | Path | None" = None,
                     infrastructure_files=_REQUIRED,
                     sealed_artifacts=None) -> GovernanceProof:
    """Prove ONE sealed run directory, from the bytes that are on the disk.

    Parameters
    ----------
    context
        The independent expected side (see `SourceContext`).
    report_path
        Path to the FINAL report. Its file NAME must be exactly
        `S0_REPORT.json`, so an evidence mirror copy or a draft can never
        stand in as the authority. Its PARENT is the run directory — the two
        are not separately addressable, so "verify this report against those
        artifacts" is not expressible.
    infrastructure_files
        REQUIRED. The names the run infrastructure (not the renderer) writes
        into the run directory. Everything in the directory that is neither
        declared in the manifest, nor the self-excluded report, nor named here,
        is an extra file and fails the proof.
    sealed_artifacts
        REMOVED. Present only as a poison pill: passing the in-memory artifact
        map raises `ProofRefused`, because an in-memory verdict can only ever
        mean "what the renderer INTENDED to seal", and that is exactly the
        claim M6.1.6 could make while nine of ten digests on disk were wrong.
        Use `screen_governance_draft` for the pre-write screen.

    WHERE TO CALL IT
    ----------------
    AFTER the Stage-E write-out loop in `runner.py` has written every artifact
    into the run directory, and BEFORE the run is declared sealed — i.e. before
    the Stage-F `COMPLETED` registry event. Called any earlier,
    `S0_REPORT.json` is not a file yet and the proof REFUSES (F-a).

    Returns a `GovernanceProof`; raises `ProofRefused` when no honest verdict is
    possible. It never writes, patches or returns any part of the report.
    """
    if sealed_artifacts is not None:
        raise ProofRefused(
            "prove_governance: the in-memory sealed_artifacts= acceptance "
            "route is REMOVED. A verdict on the artifact MAP is a claim about "
            "what the renderer intended to seal, not about the bytes that "
            "landed — at 185e47f7 those disagreed for 9 of 10 sealed files. "
            f"Pass report_path=<run_dir>/{FINAL_REPORT_NAME} instead; for the "
            "pre-write screen use screen_governance_draft().")
    if not isinstance(context, SourceContext):
        raise ProofRefused(
            "prove_governance: context must be a SourceContext built from the "
            "independent pre-run sources")
    infrastructure = _validated_infrastructure(infrastructure_files)
    if report_path is None:
        raise ProofRefused(
            "prove_governance: report_path= is required — the proof is the "
            "DISK path and has no other input mode")

    path = Path(report_path)
    if path.name != FINAL_REPORT_NAME:
        raise ProofRefused(
            f"prove_governance: refusing {path.name!r} as the governance "
            f"authority — only the final {FINAL_REPORT_NAME} is admissible "
            "(no evidence mirror, no draft copy)")
    if not path.is_file():
        raise ProofRefused(
            f"{REFUSAL_REPORT_MISSING}: {FINAL_REPORT_NAME} is not a file in "
            "the run directory — the proof runs AFTER every artifact has been "
            "written, never before")
    raw = path.read_bytes()
    if not raw.strip():
        raise ProofRefused(
            f"{REFUSAL_REPORT_MISSING}: {FINAL_REPORT_NAME} is empty — the "
            "sealed bytes are not final yet")
    run_dir = path.parent

    problems: list[str] = []
    partial = _partial_coverage(context)
    counter = [0]
    disk_counter = [0]

    root = _parse_report(raw, problems)
    required = _governance_axis(context, root, problems, counter)
    declared, named = _read_declarations(root, problems)
    disk_required, seen = _verify_sealed_set(
        run_dir, declared, named, infrastructure, problems, disk_counter)
    if disk_required > 0:
        partial.append(_PARTIAL_DECLARATION_UNBOUND)

    ok = (not problems
          and counter[0] == required and required > 0
          and disk_counter[0] == disk_required and disk_required > 0)
    return GovernanceProof(
        ok=ok,
        problems=tuple(problems),
        partial=tuple(partial),
        comparisons_performed=counter[0],
        comparisons_required=required,
        disk_checks_performed=disk_counter[0],
        disk_checks_required=disk_required,
        sealed_files_declared=len(declared),
        run_dir_entries_seen=seen,
        report_sha256=hashlib.sha256(raw).hexdigest(),
        actual_source=_DISK_SOURCE)


def screen_governance_draft(context: "SourceContext", *,
                            draft_artifacts: "Mapping[str, str] | None" = None
                            ) -> DraftScreen:
    """PRE-WRITE screen of the in-memory artifact map. NOT an acceptance.

    Runs the governance comparison (Q1) against
    `draft_artifacts["S0_REPORT.json"]` so a renderer can refuse to WRITE a
    report whose `governance.*` is already wrong. It cannot run Q2 — the files
    do not exist yet, which is precisely why its result is a `DraftScreen` and
    not a `GovernanceProof`.

    Wire it at the very END of the render flow, after
    `files["S0_REPORT.json"] = rep.to_formal_json(formal)` — i.e. after the
    manifest injection and the second contract validation. Called any earlier
    the key is not there yet and the screen REFUSES (F-a).

    Gate on `screen.blocking_problems`; there is no `ok`.
    """
    if not isinstance(context, SourceContext):
        raise ProofRefused(
            "screen_governance_draft: context must be a SourceContext built "
            "from the independent pre-run sources")
    if not isinstance(draft_artifacts, Mapping):
        raise ProofRefused(
            "screen_governance_draft: draft_artifacts= must be the in-progress "
            "artifact mapping")
    if FINAL_REPORT_NAME not in draft_artifacts:
        raise ProofRefused(
            f"screen_governance_draft: {FINAL_REPORT_NAME} is not in the "
            "artifact map yet — the screen runs AFTER the final report is "
            "built, never before")
    text = draft_artifacts[FINAL_REPORT_NAME]
    if not isinstance(text, str) or not text.strip():
        raise ProofRefused(
            f"screen_governance_draft: {FINAL_REPORT_NAME} in the artifact map "
            "is empty or not text")
    raw = text.encode("utf-8")

    problems: list[str] = []
    counter = [0]
    root = _parse_report(raw, problems)
    _governance_axis(context, root, problems, counter)
    return DraftScreen(
        blocking_problems=tuple(problems),
        partial=tuple(_partial_coverage(context)),
        comparisons_performed=counter[0],
        comparisons_required=_leaf_count(_expected_tree(context)),
        draft_sha256=hashlib.sha256(raw).hexdigest(),
        acceptance=_NOT_AN_ACCEPTANCE)


# ===========================================================================
# F-2 MINIMAL SEAL BOUNDARY — KEY-CLAIMS RELEASE GATE (S0 closeout,
# Aaron ruling 2026-08-10)
# ===========================================================================
# Aaron's mandated boundary, stated verbatim in the closeout master prompt:
# independent-source reconciliation ONLY for the formally PUBLISHED key
# claims — (1) the day universe, (2) label/NA counts, (3) Primary/Oracle
# versus parsed artifact bytes, (4) the cost & engine axes and the sealed
# artifact name set, (5) bootstrap/seeds/estimator, (6) the formal report
# versus the disk manifest. Explicitly NOT a general leaf-proof framework:
# the closed six-claim list below is the whole scope, each claim is its own
# named function, and adding a claim means editing this closed tuple. The
# legacy evidence leaf/token system stays what M6.1.8 §5 says it is —
# a diagnostic, not a release certificate; KC3 CONSUMES its hard verdict
# rather than rebuilding it.
#
# Independence sources (never the payload's own mirror of itself):
#   KC1/KC2 -> the LOCKED preflight assertions bytes (compare-only file);
#   KC3     -> evidence.reconcile_with_evidence's flat verdict, whose D_TP /
#              D_FP / oracle series are REBUILT from parsed MC_HANDOFF bytes;
#   KC4     -> the frozen engine x scenario matrix constants (study/report),
#              which finally binds the sealed NAME SET to an authority
#              OUTSIDE the report (closing _PARTIAL_DECLARATION_UNBOUND for
#              the name-set axis; byte identity stays Q2's job);
#   KC5     -> contracts.RESEARCH_BOOTSTRAP_SEEDS / report.FROZEN_N_BOOT /
#              the Aaron-ruled ResolvedS0Methods instance;
#   KC6     -> the runner's post-write disk verification seam result.

KEY_CLAIM_IDS: tuple[str, ...] = (
    "KC1_day_universe",
    "KC2_label_na_counts",
    "KC3_primary_oracle_vs_bytes",
    "KC4_engine_scenario_axis_and_sealed_names",
    "KC5_bootstrap_seeds_estimator",
    "KC6_report_vs_disk",
)

#: The five funnel levels shared by the locked assertions file and the
#: published `structural.funnel_counts` (same VERBATIM key names; the side
#: diagnostic is compared only when both sides carry it).
_KC_FUNNEL_LEVELS: tuple[str, ...] = (
    "L0_scheduled_trading_days", "L1_observed_rth_days",
    "L2_regular_full_session_candidates", "L3_structurally_eligible_days",
    "L4_final_feature_construction_dates")
_KC_FUNNEL_SIDE = "side_diagnostic_complete_390_bar_rth_days"

#: Sealed names that MAY appear beyond the always-expected set — admitted
#: only when their admission conditions hold (handoff.formal_sealable);
#: their presence is validated as membership of this CLOSED set, never as a
#: free-form allowance.
_KC_OPTIONAL_SEALED: frozenset = frozenset(
    {"DAY_STRATA.json", "GRID_SAMPLES.json", "SEED_MANIFEST.json"})


@dataclass(frozen=True)
class ResearchClaimsContext:
    """Independent inputs for `verify_key_claims`. Built by the ENTRY, never
    by the renderer, and never from the payload under test.

    assertions_bytes: raw bytes of the locked expected_preflight_assertions
        JSON (the Stage-B compare-only file).
    ruled_methods: the Aaron-ruled contracts.ResolvedS0Methods instance.
    evidence_problems: the flat list returned by
        evidence.reconcile_with_evidence(...) for THIS payload+files, or
        None if it was not run (None is an uncovered claim -> FAIL).
    disk_report: {"ok": bool, "detail": <str>} adapted from the runner's
        post_write_verify seam result, or None before the bytes exist
        (pre-write phase only).
    """
    assertions_bytes: object
    ruled_methods: object
    evidence_problems: object
    disk_report: object


@dataclass(frozen=True)
class KeyClaimsReport:
    """Per-claim verdicts. `phase` is 'pre_write' or 'post_write'.

    Like `DraftScreen`, this object refuses `bool()` so it can never be
    mistaken for a boolean gate; consumers must ask the explicit question
    (`sealable_pre_write` / `releasable_post_write`).
    """
    phase: str
    verdicts: Mapping                 # claim_id -> PASS | FAIL | PENDING
    problems: tuple

    def __bool__(self) -> bool:
        raise TypeError("KeyClaimsReport has no boolean value; use "
                        ".sealable_pre_write or .releasable_post_write")

    @property
    def sealable_pre_write(self) -> bool:
        if self.phase != "pre_write":
            return False
        return all(self.verdicts.get(c) == "PASS"
                   for c in KEY_CLAIM_IDS[:-1]) and (
                       self.verdicts.get("KC6_report_vs_disk") == "PENDING")

    @property
    def releasable_post_write(self) -> bool:
        if self.phase != "post_write":
            return False
        return all(self.verdicts.get(c) == "PASS" for c in KEY_CLAIM_IDS)


def _kc_int(v) -> bool:
    return type(v) is int


def _kc1_kc2(formal, ctx, problems, verdicts) -> None:
    """KC1 (funnel vs locked assertions) + KC2 (NA arithmetic bound to the
    independent L3). One parse, two claims, separate verdicts."""
    v1 = v2 = "PASS"
    try:
        raw = ctx.assertions_bytes
        if not isinstance(raw, (bytes, bytearray)):
            raise ValueError("assertions_bytes_not_bytes")
        locked = json.loads(bytes(raw).decode("utf-8"))
        funnel = locked["funnel"]
        if not isinstance(funnel, Mapping):
            raise ValueError("locked_funnel_not_a_mapping")
    except Exception as exc:
        problems.append("key_claims.assertions_unusable:" + type(exc).__name__)
        verdicts["KC1_day_universe"] = "FAIL"
        verdicts["KC2_label_na_counts"] = "FAIL"
        return

    st = formal.get("structural") if isinstance(formal, Mapping) else None
    fc = st.get("funnel_counts") if isinstance(st, Mapping) else None
    if not isinstance(fc, Mapping):
        problems.append("key_claims.KC1.published_funnel_counts_missing")
        v1 = "FAIL"
    else:
        for level in _KC_FUNNEL_LEVELS:
            got, want = fc.get(level), funnel.get(level)
            if not _kc_int(got) or not _kc_int(want):
                problems.append("key_claims.KC1.level_uncovered:" + level)
                v1 = "FAIL"
            elif got != want:
                problems.append("key_claims.KC1.funnel_mismatch:"
                                + level + ":" + repr(got) + "!=" + repr(want))
                v1 = "FAIL"
        got, want = fc.get(_KC_FUNNEL_SIDE), funnel.get(_KC_FUNNEL_SIDE)
        if _kc_int(got) and _kc_int(want) and got != want:
            problems.append("key_claims.KC1.funnel_mismatch:"
                            + _KC_FUNNEL_SIDE + ":" + repr(got)
                            + "!=" + repr(want))
            v1 = "FAIL"

    l3 = funnel.get("L3_structurally_eligible_days")
    if not _kc_int(l3):
        problems.append("key_claims.KC2.locked_l3_unusable")
        v2 = "FAIL"
    else:
        nat = st.get("na_table") if isinstance(st, Mapping) else None
        pop = nat.get("population") if isinstance(nat, Mapping) else None
        if not _kc_int(pop) or pop != l3:
            problems.append("key_claims.KC2.population_not_bound_to_locked_l3:"
                            + repr(pop) + "!=" + repr(l3))
            v2 = "FAIL"
        per_field = (nat.get("per_field")
                     if isinstance(nat, Mapping) else None)
        rows_seen = 0
        if isinstance(per_field, Mapping):
            for table in ("features", "labels"):
                rows = per_field.get(table)
                if not isinstance(rows, Mapping):
                    continue
                for name, row in rows.items():
                    if not isinstance(row, Mapping):
                        continue
                    rows_seen += 1
                    na, ok = row.get("na"), row.get("not_na")
                    if not _kc_int(na) or not _kc_int(ok) or na + ok != l3:
                        problems.append(
                            "key_claims.KC2.row_not_conserved_vs_locked_l3:"
                            + table + "." + str(name))
                        v2 = "FAIL"
                    reasons = row.get("reasons")
                    if isinstance(reasons, Mapping) and reasons:
                        vals = list(reasons.values())
                        if all(_kc_int(x) for x in vals) and sum(vals) != na:
                            problems.append(
                                "key_claims.KC2.reasons_do_not_sum_to_na:"
                                + table + "." + str(name))
                            v2 = "FAIL"
        if rows_seen == 0:
            problems.append("key_claims.KC2.no_na_rows_covered")
            v2 = "FAIL"
        f10 = st.get("f10_counts") if isinstance(st, Mapping) else None
        if isinstance(f10, Mapping) and f10:
            vals = list(f10.values())
            if all(_kc_int(x) for x in vals):
                if sum(vals) != l3:
                    problems.append("key_claims.KC2.f10_partition_sum:"
                                    + repr(sum(vals)) + "!=" + repr(l3))
                    v2 = "FAIL"
            else:
                problems.append("key_claims.KC2.f10_counts_not_ints")
                v2 = "FAIL"
        else:
            problems.append("key_claims.KC2.f10_counts_missing")
            v2 = "FAIL"
    verdicts["KC1_day_universe"] = v1
    verdicts["KC2_label_na_counts"] = v2


def _kc3(ctx, problems, verdicts) -> None:
    ev = ctx.evidence_problems
    if ev is None:
        problems.append("key_claims.KC3.evidence_reconciliation_not_run")
        verdicts["KC3_primary_oracle_vs_bytes"] = "FAIL"
        return
    try:
        entries = [str(x) for x in ev]
    except Exception:
        problems.append("key_claims.KC3.evidence_problems_not_iterable")
        verdicts["KC3_primary_oracle_vs_bytes"] = "FAIL"
        return
    hard = [e for e in entries if not e.startswith("PARTIAL:")]
    if hard:
        problems.append("key_claims.KC3.evidence_hard_problems:"
                        + ";".join(hard[:5]))
        verdicts["KC3_primary_oracle_vs_bytes"] = "FAIL"
    else:
        verdicts["KC3_primary_oracle_vs_bytes"] = "PASS"


def _kc4(formal, problems, verdicts) -> None:
    # The AUTHORITY is the frozen engine/scenario constants — imported at
    # call time so this module can never drift from the single source.
    from itsf.s0.report import _SCENARIOS as _SCN          # frozen S0 §6
    from itsf.s0.study import ENGINES as _ENG              # frozen S0 §7
    expected = set()
    for e in _ENG:
        for s in _SCN:
            expected.add("MC_HANDOFF_" + str(e) + "_" + str(s) + ".jsonl")
    expected |= {"S0_REPORT.md", "HANDOFF_ADMISSION.json"}
    man = (formal.get("mc_handoff_manifest")
           if isinstance(formal, Mapping) else None)
    sealed = man.get("sealed_files") if isinstance(man, Mapping) else None
    if not isinstance(sealed, Mapping) or not sealed:
        problems.append("key_claims.KC4.sealed_files_missing")
        verdicts["KC4_engine_scenario_axis_and_sealed_names"] = "FAIL"
        return
    names = set(sealed)
    v = "PASS"
    missing = expected - names
    if missing:
        problems.append("key_claims.KC4.expected_sealed_names_missing:"
                        + ",".join(sorted(missing)))
        v = "FAIL"
    extra = names - expected - _KC_OPTIONAL_SEALED
    if extra:
        problems.append("key_claims.KC4.sealed_names_outside_frozen_matrix:"
                        + ",".join(sorted(str(x) for x in extra)))
        v = "FAIL"
    if "S0_REPORT.json" in names:
        problems.append("key_claims.KC4.self_excluded_name_in_sealed_set")
        v = "FAIL"
    verdicts["KC4_engine_scenario_axis_and_sealed_names"] = v


def _kc5(formal, ctx, problems, verdicts) -> None:
    from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS as _SEEDS
    from itsf.s0.report import FROZEN_N_BOOT as _NBOOT
    v = "PASS"
    m = ctx.ruled_methods
    ruled_est = getattr(m, "worst_day_estimator", None)
    if not isinstance(ruled_est, str) or not ruled_est:
        problems.append("key_claims.KC5.ruled_estimator_unusable")
        verdicts["KC5_bootstrap_seeds_estimator"] = "FAIL"
        return
    want_seeds = {str(s) for s in _SEEDS}
    bci = (formal.get("bootstrap_ci")
           if isinstance(formal, Mapping) else None)
    state = {"per_seed_found": 0, "v": v}

    def _walk(node, depth=0):
        if depth > 6 or not isinstance(node, Mapping):
            return
        ps = node.get("per_seed")
        if isinstance(ps, Mapping):
            state["per_seed_found"] += 1
            if set(str(k) for k in ps.keys()) != want_seeds:
                problems.append(
                    "key_claims.KC5.per_seed_keys_not_frozen_seed_set")
                state["v"] = "FAIL"
            for sk, cell in ps.items():
                nb = (cell.get("n_boot")
                      if isinstance(cell, Mapping) else None)
                if nb != _NBOOT:
                    problems.append("key_claims.KC5.n_boot_not_frozen:"
                                    + str(sk) + ":" + repr(nb))
                    state["v"] = "FAIL"
            return
        for child in node.values():
            _walk(child, depth + 1)

    _walk(bci if isinstance(bci, Mapping) else {})
    v = state["v"]
    if state["per_seed_found"] == 0:
        problems.append("key_claims.KC5.no_per_seed_blocks_covered")
        v = "FAIL"
    e2 = (formal.get("e2_worst_days")
          if isinstance(formal, Mapping) else None)
    cells = 0
    if isinstance(e2, Mapping):
        for tkey, scns in e2.items():
            if not isinstance(scns, Mapping):
                continue
            for scn, cell in scns.items():
                if not isinstance(cell, Mapping):
                    continue
                cells += 1
                if cell.get("estimator_status") != "resolved":
                    problems.append(
                        "key_claims.KC5.estimator_status_not_resolved:"
                        + str(tkey) + "|" + str(scn))
                    v = "FAIL"
                disclosed = cell.get("percentile_estimator")
                if (not isinstance(disclosed, str)
                        or ruled_est not in disclosed):
                    problems.append(
                        "key_claims.KC5.estimator_disclosure_not_ruled:"
                        + str(tkey) + "|" + str(scn))
                    v = "FAIL"
    if cells == 0:
        problems.append("key_claims.KC5.no_e2_cells_covered")
        v = "FAIL"
    verdicts["KC5_bootstrap_seeds_estimator"] = v


def _kc6(ctx, phase, problems, verdicts) -> None:
    dr = ctx.disk_report
    if phase == "pre_write":
        if dr is None:
            verdicts["KC6_report_vs_disk"] = "PENDING"
        else:
            problems.append(
                "key_claims.KC6.disk_report_supplied_before_write")
            verdicts["KC6_report_vs_disk"] = "FAIL"
        return
    if not isinstance(dr, Mapping) or dr.get("ok") is not True:
        problems.append("key_claims.KC6.disk_verification_not_ok")
        verdicts["KC6_report_vs_disk"] = "FAIL"
    else:
        verdicts["KC6_report_vs_disk"] = "PASS"


def verify_key_claims(formal, ctx, *, phase):
    """Run the CLOSED six-claim battery. Never raises, for any input.

    phase='pre_write'  -> KC1..KC5 must PASS, KC6 must be PENDING
                          (`sealable_pre_write`).
    phase='post_write' -> all six must PASS (`releasable_post_write`).
    An unusable context or an unreadable payload is a FAIL on the affected
    claim, never an exception and never a silent PASS.
    """
    problems = []
    verdicts = {}
    if phase not in ("pre_write", "post_write"):
        return KeyClaimsReport(
            phase=str(phase),
            verdicts=MappingProxyType(
                dict((c, "FAIL") for c in KEY_CLAIM_IDS)),
            problems=("key_claims.phase_invalid:" + repr(phase),))
    for step in (lambda: _kc1_kc2(formal, ctx, problems, verdicts),
                 lambda: _kc3(ctx, problems, verdicts),
                 lambda: _kc4(formal, problems, verdicts),
                 lambda: _kc5(formal, ctx, problems, verdicts),
                 lambda: _kc6(ctx, phase, problems, verdicts)):
        try:
            step()
        except BaseException as exc:      # defensive: a gate must not raise
            problems.append("key_claims.step_raised:" + type(exc).__name__)
    for c in KEY_CLAIM_IDS:
        verdicts.setdefault(c, "FAIL")
    return KeyClaimsReport(phase=phase,
                           verdicts=MappingProxyType(dict(verdicts)),
                           problems=tuple(problems))
