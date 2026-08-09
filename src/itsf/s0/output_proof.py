"""S0 OUTPUT PROOF — one vertical slice: final `S0_REPORT.json` -> `governance.*`.

WHAT THIS IS
------------
A CHECKER. It answers exactly one question:

    do the five contract-specified `governance` keys inside the FINAL sealed
    `S0_REPORT.json` bytes equal, key-for-key and value-for-value, what an
    INDEPENDENT pre-run/authority context says they must be?

It answers nothing else. It knows nothing about labels, NA, samples, costs,
Oracle, bootstrap, grid, volatility, event mapping or any strategy statistic,
and it deliberately does NOT extend (or read) the leaf/token evidence system.

WHAT THIS IS NOT (structural, not merely promised)
--------------------------------------------------
It is NOT a generator. There is exactly ONE public callable, `prove_governance`,
and it returns a `GovernanceProof` whose every field is a `bool`, `int`, `str`
or `tuple[str, ...]` (enforced in `GovernanceProof.__post_init__`). No public
name is bound to the expected-tree builder, no returned value is a Mapping, and
no problem string carries an expected VALUE — so a renderer cannot use this
module, or its output, to build/patch/backfill `governance.*`. The module also
contains no filesystem write call of any kind: the only I/O verb it uses is
`Path.read_bytes`.

THREE MEASURED FAILURES THIS DESIGN REFUSES TO REPEAT
-----------------------------------------------------
F-a  "the check ran before the thing it claimed to check existed".
     The pre-existing evidence pass runs at `scripts/s0_real_run.py:1013-1014`,
     i.e. BEFORE `HANDOFF_ADMISSION.json` (:1018), `S0_REPORT.md` (:1034), the
     manifest injection (:1049-1056) and `S0_REPORT.json` (:1065) exist, so its
     target could not have been the sealed bytes. THIS module refuses to run
     unless the final `S0_REPORT.json` is already there: in the render flow it
     must be handed the artifact map AFTER `files["S0_REPORT.json"]` is set, and
     a map without that key is a `ProofRefused`, never a pass. The actual side
     is parsed from those bytes and from nothing else.

F-b  "the expected side was a mirror of the target side, and the pass was a
     literal". `evidence.py:4020-4042` regenerates six subtrees with the same
     six functions that produced them and reports a hard-coded `6` as its
     compared-count — a check structurally incapable of failing. Here the
     expected side comes from a `SourceContext` (pre-run registry snapshot +
     frozen-hash authority + its independent on-disk observations + the approved
     engineering-seed provenance) that never touches the report, and
     `comparisons_performed` is incremented by the comparison loop itself, one
     increment per leaf actually examined. `ok` requires `problems == ()` AND
     `comparisons_performed == comparisons_required`, where the required count
     is derived by walking the expected tree. A skipped comparison cannot pass.

F-c  "expected domain collapse". `evidence.py:2052-2054` sizes its
     `frozen_hash_paths` axis from "the DECLARED governance.frozen_hashes key
     set", i.e. from the very object it guards — so emptying the guarded field
     took the axis from 7 to 0 and the guard evaporated. Here the expected key
     domain is `CONTRACT_GOVERNANCE_KEYS` (a literal transcription of the
     content contract) and `sorted(context.frozen_hash_authority)` (the freeze
     registry). Deleting a path from the report makes the report SHORT of the
     expected domain; it never shrinks the domain.

EXPECTED-SIDE SOURCES (all supplied by the caller; none read from the report)
-----------------------------------------------------------------------------
  * `authorization_snapshot` — the EXISTING pre-run trial/run identity snapshot
    produced by `RealChain.authorization_snapshot()`
    (`scripts/s0_real_run.py:2253-2280`), taken at Stage A and re-verified
    immediately before the RUN_STARTED transition. Supplies `trial_id`,
    `authorized_commit`, and — as the EXISTING pre-run registry-sequence
    snapshot — `event_sequence` (`s0_real_run.py:2272`,
    `len(parse_registry_events(text))`).
  * `frozen_hash_authority` — `itsf.guards.FROZEN_HASHES`
    (`src/itsf/guards.py:20-39`), the freeze-registry authority mapping.
  * `frozen_hash_observations` — the compute-time byte-level re-hash of those
    same files (`scripts/s0_real_run.py:2319-2320`). Authority and observation
    are compared against EACH OTHER before either is used as an expectation, so
    a frozen file mutated on disk is a problem rather than an invisible pass.
  * `engineering_seed` + `engineering_seed_provenance` — the approved
    provenance stamp (`scripts/s0_real_run.py:37-39`, DR-02 / packet §5; prose
    at `src/itsf/s0/handoff.py:226-228`).

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
typed and exactly equal to the independent context. It does NOT mean the sealed
report is bound to the pre-run registry BYTES — `governance.*` carries no
`registry_sha256` and no `exact_authorization_text_sha256`, and no
authorization exists to add them, so those snapshot facts are reported as
PARTIAL (derived, not hand-listed) instead of silently dropped. The formal
report schema is NOT extended by this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType

__all__ = (
    "FINAL_REPORT_NAME",
    "CONTRACT_GOVERNANCE_KEYS",
    "CONTRACT_FROZEN_HASH_COUNT",
    "ProofRefused",
    "SourceContext",
    "GovernanceProof",
    "prove_governance",
)

# The ONE artifact whose bytes may be the actual side. Hard-coded on purpose:
# it is not a parameter, so no caller can point the proof at an evidence mirror
# copy, a pre-injection draft, or any other look-alike and have it treated as
# the authority.
FINAL_REPORT_NAME = "S0_REPORT.json"

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

_HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


class ProofRefused(RuntimeError):
    """The proof could not be ATTEMPTED.

    Distinct from a failing proof. A refusal means the caller asked for a
    verdict that cannot honestly be given — the final `S0_REPORT.json` does not
    exist yet, the artifact offered is not that file, or the independent
    context is structurally unusable so no expectation can be stated. Refusals
    are exceptions precisely so they cannot be mistaken for `ok=False` and
    cannot be silently swallowed into a seal.
    """


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
        `RealChain.authorization_snapshot()` (`scripts/s0_real_run.py:2253`).
        Must carry `trial_id` (non-empty str), `authorized_commit` (40 lowercase
        hex) and `event_sequence` (int >= 1). Extra facts are welcome and are
        reported as PARTIAL coverage.
    frozen_hash_authority
        `itsf.guards.FROZEN_HASHES` — the freeze-registry `{path: sha256}`.
    frozen_hash_observations
        Independently observed `{path: sha256}` of the same files at compute
        time (`scripts/s0_real_run.py:2319-2320`). Never an evidence mirror.
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
# comparison
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


# ---------------------------------------------------------------------------
# result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GovernanceProof:
    """The verdict. Scalars and string tuples only — there is nothing in here a
    renderer could splice into a report as content.

    `ok` is True only when the proof performed EVERY required comparison and
    found no problem. `partial` is disclosure, not a verdict: it lists the
    expected-side facts the sealed schema has no field for, and it never
    weakens or strengthens `ok`.
    """

    ok: bool
    problems: tuple[str, ...]
    partial: tuple[str, ...]
    comparisons_performed: int
    comparisons_required: int
    report_sha256: str
    actual_source: str

    def __post_init__(self) -> None:
        # Structural guarantee, enforced rather than documented: no field of a
        # proof may ever carry report-shaped content.
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, tuple):
                if not all(type(item) is str for item in value):
                    raise TypeError(
                        f"GovernanceProof.{f.name}: tuple fields hold strings "
                        "only")
            elif type(value) not in (bool, int, str):
                raise TypeError(
                    f"GovernanceProof.{f.name}: a proof carries only bool/int/"
                    "str/tuple-of-str — never content")


# ---------------------------------------------------------------------------
# the one public entry point
# ---------------------------------------------------------------------------

def prove_governance(context: "SourceContext", *,
                     sealed_artifacts: Mapping[str, str] | None = None,
                     report_path: "str | Path | None" = None
                     ) -> GovernanceProof:
    """Prove the FINAL `S0_REPORT.json`'s `governance.*` against `context`.

    Exactly one of `sealed_artifacts` / `report_path` must be given:

      sealed_artifacts  the Stage-E artifact map. The proof reads ONLY
                        `sealed_artifacts["S0_REPORT.json"]`. Wire this at the
                        very END of the render flow, after
                        `files["S0_REPORT.json"] = rep.to_formal_json(formal)`
                        — i.e. after the manifest injection and the second
                        contract validation. Called any earlier, the key is not
                        there yet and the proof REFUSES (F-a).
      report_path       a path whose file NAME must be exactly
                        `S0_REPORT.json`, for verifying already-written bytes.
                        Any other name is refused, so an evidence mirror copy
                        can never stand in as the authority.

    Returns a `GovernanceProof`; raises `ProofRefused` when no honest verdict is
    possible. It never writes, patches or returns any part of the report.
    """
    if not isinstance(context, SourceContext):
        raise ProofRefused(
            "prove_governance: context must be a SourceContext built from the "
            "independent pre-run sources")
    if (sealed_artifacts is None) == (report_path is None):
        raise ProofRefused(
            "prove_governance: pass exactly one of sealed_artifacts= or "
            "report_path=")

    if sealed_artifacts is not None:
        if not isinstance(sealed_artifacts, Mapping):
            raise ProofRefused(
                "prove_governance: sealed_artifacts must be the Stage-E "
                "artifact mapping")
        if FINAL_REPORT_NAME not in sealed_artifacts:
            raise ProofRefused(
                f"prove_governance: {FINAL_REPORT_NAME} is not in the artifact "
                "map yet — the proof runs AFTER the final report is built, "
                "never before")
        text = sealed_artifacts[FINAL_REPORT_NAME]
        if not isinstance(text, str) or not text.strip():
            raise ProofRefused(
                f"prove_governance: {FINAL_REPORT_NAME} in the artifact map is "
                "empty or not text")
        raw = text.encode("utf-8")
        actual_source = "sealed_artifact"
    else:
        path = Path(report_path)          # type: ignore[arg-type]
        if path.name != FINAL_REPORT_NAME:
            raise ProofRefused(
                f"prove_governance: refusing {path.name!r} as the governance "
                f"authority — only the final {FINAL_REPORT_NAME} is admissible "
                "(no evidence mirror, no draft copy)")
        if not path.is_file():
            raise ProofRefused(
                f"prove_governance: {FINAL_REPORT_NAME} does not exist yet")
        raw = path.read_bytes()
        if not raw.strip():
            raise ProofRefused(
                f"prove_governance: {FINAL_REPORT_NAME} is empty — the sealed "
                "bytes are not final yet")
        actual_source = "file"

    # ---- expected side: built from the context, with `raw` untouched --------
    expected = _expected_tree(context)
    required = _leaf_count(expected)
    problems: list[str] = _context_problems(context)
    partial = _partial_coverage(context)
    counter = [0]

    # ---- actual side: parsed from those bytes and nothing else -------------
    try:
        root = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        problems.append(f"{_P}report_unparsable")
        root = None
    if root is not None:
        if not isinstance(root, Mapping):
            problems.append(f"{_P}report_root_not_object")
        elif _ROOT not in root:
            problems.append(f"{_P}section_missing")
        else:
            _compare(expected, root[_ROOT], _ROOT, problems, counter)

    performed = counter[0]
    if performed != required:
        problems.append(f"{_P}comparison_count")
    ok = not problems and performed == required and required > 0
    return GovernanceProof(
        ok=ok,
        problems=tuple(problems),
        partial=tuple(partial),
        comparisons_performed=performed,
        comparisons_required=required,
        report_sha256=hashlib.sha256(raw).hexdigest(),
        actual_source=actual_source)
