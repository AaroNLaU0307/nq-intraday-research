"""DURABLE OUTPUT for one governed real MC run.

WHY THIS MODULE EXISTS. `mc_runner` computes a complete run and returns a
`RunnerResult` -- and until this module, nothing wrote it anywhere. The whole
product of the one authorized real run lived in a process that then exited.
That was found before MC-R001 was started, not after.

WHAT IT IS NOT. It is not a new persistence framework. The discipline here is
the one `day_strata_supplement.seal_supplement_test_only` and
`runinfra.archive_sealed_run` already use and Codex final review #5 ratified:
stage into `<name>.partial`, re-read and verify what was staged, and promote
with a single atomic rename. The inventory digest is `bundle_precheck`'s own
formula, called with this artifact class's schema rather than
re-implemented. The archive step is `runinfra.archive_sealed_run`, unchanged.

WHAT IT WRITES, and nothing else: the semantic objects the runner already
produced, plus the identities the run was authorized against. No statistic is
computed here. A number that is not already in the `RunnerResult` or in the
Owner's authorization does not appear in the output.

  RUN_IDENTITY.json      every binding the run was authorized against, plus
                         the Development manifest digest, measured here
  SEAL_CANDIDATE.json    the governed seal candidate, its verdict, the grid
                         seal status and the H1-entry standing
  GRID_STANDING.json     the cross-seed grid convergence and the published
                         region map per kind
  PER_SEED_EVIDENCE.json per-seed grid evidence, the B scales each seed
                         actually ran, and the arm labels
  OUTPUT_MANIFEST.json   name/size/sha256 of the four above, and one summary
                         digest over that table

FAILURE IS NEVER TIDIED AWAY. If anything fails before promotion, the
`.partial` directory is LEFT ON DISK exactly as it was. A failed run must not
look like a run that never happened, and it must not look like a completed
one either -- which is what the staging name is for.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
import os
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from itsf import contracts as _c
from itsf.mc.atoms import MCInputError, canonical_json, jsonable
from itsf.mc.bundle_precheck import BundleEntry, _summary

#: A DIFFERENT schema from the bundle's on-disk summary, deliberately. Both
#: are file-table digests; a run output and an input bundle are not the same
#: artifact class, and two classes sharing one schema string can be confused
#: for each other exactly where it matters.
OUTPUT_SUMMARY_SCHEMA = "mc_run_output_summary.v1"
RUN_OUTPUT_SCHEMA = "mc_run_output.v1"

#: Same suffix as the supplement seal and the archive copy.
PARTIAL_SUFFIX = ".partial"

MANIFEST_NAME = "OUTPUT_MANIFEST.json"
ARTIFACT_NAMES = ("RUN_IDENTITY.json", "SEAL_CANDIDATE.json",
                  "GRID_STANDING.json", "PER_SEED_EVIDENCE.json")

#: The ruled runs root, from `contracts` -- not a second copy of the path.
RULED_RUNS_DIR = Path(_c.RULED_RUNS_ROOT) / "runs"

#: Every identity the Owner's authorization carries. Copied verbatim into
#: `RUN_IDENTITY.json`; none of them is recomputed into a different value
#: here, because the run was authorized against THESE.
AUTHORIZATION_FIELDS = ("run_id", "input_bundle_commit", "mc_execution_commit",
                        "bundle_summary_digest", "sealed_supplement_sha256",
                        "prereg_sha256", "authorized_by", "output_path")


def _payload(value):
    """Deterministic JSON-able form of a runner object.

    `atoms.jsonable` already canonicalises scalars, sequences, sets and
    mappings -- including the non-finite float tokens. It refuses anything
    else, which is correct for its own purpose and wrong here: the runner
    returns frozen dataclasses (`CellStatistics`, `GridPass`,
    `AbsentQuantity`, the grid convergence report). Those are expanded field
    by field, in declaration order, and everything else is handed straight to
    `jsonable` so there is exactly one encoding of a number.
    """
    if _dc.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _payload(getattr(value, f.name))
                for f in _dc.fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _payload(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_payload(v) for v in value]
    return jsonable(value)


def _canonical_bytes(obj) -> bytes:
    """The exact bytes one artifact is written as."""
    return (canonical_json(_payload(obj)) + "\n").encode("utf-8")


def development_manifest_sha256() -> str:
    """The Development data identity, measured from the authorized job dir.

    Read here rather than accepted as an argument: an identity a caller
    supplies is an identity the caller asserted.
    """
    from itsf.mc import production_inputs as _pi
    return hashlib.sha256(
        (_pi.AUTHORIZED_JOB_DIR / "manifest.json").read_bytes()).hexdigest()


@_dc.dataclass(frozen=True)
class PersistedOutput:
    """WHERE the evidence is and WHAT it hashes to. No research content."""
    run_id: str
    final_path: str
    partial_path: str
    files: tuple
    summary_digest: str

    @property
    def n_files(self) -> int:
        return len(self.files)

    def as_mapping(self) -> Mapping:
        return MappingProxyType({
            "schema": RUN_OUTPUT_SCHEMA,
            "run_id": self.run_id,
            "final_path": self.final_path,
            "summary_digest": self.summary_digest,
            "n_files": self.n_files,
            "files": tuple(
                MappingProxyType({"name": e.name, "size": e.size,
                                  "sha256": e.sha256}) for e in self.files),
        })


def _artifacts(result, identities: Mapping) -> dict:
    """The four content artifacts, as objects, before any encoding."""
    return {
        "RUN_IDENTITY.json": {
            "schema": RUN_OUTPUT_SCHEMA,
            **{k: identities[k] for k in AUTHORIZATION_FIELDS},
            "development_manifest_sha256":
                identities["development_manifest_sha256"],
            "runs_root": str(RULED_RUNS_DIR),
            "test_only": bool(result.test_only),
        },
        "SEAL_CANDIDATE.json": {
            "schema": RUN_OUTPUT_SCHEMA,
            "run_id": result.run_id,
            "seal_candidate": result.seal_candidate,
            "verdict": result.verdict,
            "grid_seal_status": result.grid_seal_status,
            "may_support_h1_entry": result.may_support_h1_entry,
        },
        "GRID_STANDING.json": {
            "schema": RUN_OUTPUT_SCHEMA,
            "run_id": result.run_id,
            "grid_convergence": result.grid_convergence,
            "published_region_by_kind": result.published_region_by_kind,
        },
        "PER_SEED_EVIDENCE.json": {
            "schema": RUN_OUTPUT_SCHEMA,
            "run_id": result.run_id,
            "grid_evidence_by_seed": result.grid_evidence_by_seed,
            "b_scales_by_seed": result.b_scales_by_seed,
            "arm_labels": result.arm_labels,
        },
    }


def persist_run_output(result, *, destination, authorization: Mapping,
                       manifest_sha256: str = "") -> PersistedOutput:
    """Write the run's evidence under `destination`, atomically.

    `destination` is the EXACT final directory the Owner authorization bound.
    Bytes land in `<destination>.partial/`, every staged file is re-read and
    re-hashed, the manifest is built from what was actually read back, and
    only then is the directory promoted with one `os.replace`.

    REFUSALS, all before anything is written:

      * the final directory already exists -- a finalized MC run output is
        never reused, extended or overwritten;
      * a `.partial` from an earlier attempt is present -- debris is
        disclosed, never silently clobbered or reused;
      * the result is `test_only` and the destination is under the ruled runs
        root -- a synthetic result may not be finalized where governed run
        evidence lives.

    Nothing is deleted on failure. A crashed attempt leaves its `.partial`
    directory exactly as it was, which is both the evidence that the attempt
    happened and the reason it cannot be mistaken for a completed run.
    """
    final = Path(destination)
    if not final.is_absolute():
        raise MCInputError("mc_output_path_not_absolute",
                           f"{final} is not an absolute path")
    partial = final.with_name(final.name + PARTIAL_SUFFIX)

    if bool(result.test_only) and _under(final, RULED_RUNS_DIR):
        raise MCInputError(
            "mc_output_test_only_in_ruled_root",
            f"{final} is under the ruled runs root and the result is "
            "test_only; a synthetic run may not be finalized where governed "
            "evidence lives")
    if final.exists():
        raise MCInputError(
            "mc_output_already_finalized",
            f"{final} already exists -- a finalized MC run output is never "
            "reused or overwritten")
    if partial.exists():
        raise MCInputError(
            "mc_output_partial_residue",
            f"{partial} is left from an earlier attempt; it is disclosed, "
            "never reused or clobbered -- adjudicate it before running again")

    identities = dict(_identities(authorization))
    identities["development_manifest_sha256"] = (
        manifest_sha256 or development_manifest_sha256())

    # THE ONLY DIRECTORY THIS MODULE CREATES, and deliberately without
    # `parents` or `exist_ok`: it makes the staging directory and nothing
    # else. A missing parent is an explicit failure rather than a runs root
    # this module quietly invented, and an existing staging directory was
    # already refused above.
    partial.mkdir()
    intended = {name: _canonical_bytes(obj)
                for name, obj in _artifacts(result, identities).items()}
    for name in ARTIFACT_NAMES:
        (partial / name).write_bytes(intended[name])

    entries = []
    for name in ARTIFACT_NAMES:
        got = (partial / name).read_bytes()
        if got != intended[name]:
            raise MCInputError(
                "mc_output_staged_verify",
                f"{name} re-read differently than it was written")
        entries.append(BundleEntry(name=name, size=len(got),
                                   sha256=hashlib.sha256(got).hexdigest()))
    entries = tuple(entries)
    summary = _summary(entries, schema=OUTPUT_SUMMARY_SCHEMA)

    manifest_bytes = _canonical_bytes({
        "schema": OUTPUT_SUMMARY_SCHEMA,
        "run_id": str(result.run_id),
        "final_path": str(final),
        "files": [{"name": e.name, "size": e.size, "sha256": e.sha256}
                  for e in entries],
        "summary_digest": summary,
    })
    (partial / MANIFEST_NAME).write_bytes(manifest_bytes)
    if (partial / MANIFEST_NAME).read_bytes() != manifest_bytes:
        raise MCInputError("mc_output_staged_verify",
                           f"{MANIFEST_NAME} re-read differently than written")

    os.replace(partial, final)

    for e in entries:
        got = (final / e.name).read_bytes()
        if hashlib.sha256(got).hexdigest() != e.sha256:
            raise MCInputError(
                "mc_output_promoted_verify",
                f"{e.name} diverged between staging and the promoted "
                "directory; the directory is LEFT IN PLACE as evidence")
    return PersistedOutput(run_id=str(result.run_id), final_path=str(final),
                           partial_path=str(partial), files=entries,
                           summary_digest=summary)


def read_persisted_output(final) -> PersistedOutput:
    """Re-read a finalized output and RECOMPUTE its identities from bytes.

    The manifest's own numbers are not trusted: every file is re-hashed and
    the summary digest recomputed, then compared. This is what makes the
    written identities checkable rather than merely recorded.
    """
    import json
    final = Path(final)
    manifest = json.loads((final / MANIFEST_NAME).read_text(encoding="utf-8"))
    entries = []
    for name in ARTIFACT_NAMES:
        got = (final / name).read_bytes()
        entries.append(BundleEntry(name=name, size=len(got),
                                   sha256=hashlib.sha256(got).hexdigest()))
    entries = tuple(entries)
    summary = _summary(entries, schema=OUTPUT_SUMMARY_SCHEMA)
    declared = {(f["name"], int(f["size"]), f["sha256"])
                for f in manifest.get("files", ())}
    if declared != {(e.name, e.size, e.sha256) for e in entries}:
        raise MCInputError(
            "mc_output_inventory_mismatch",
            f"{final} does not hash to the table its own manifest declares")
    if str(manifest.get("summary_digest", "")) != summary:
        raise MCInputError(
            "mc_output_summary_mismatch",
            f"{final} recomputes to {summary[:12]} and its manifest declares "
            f"{str(manifest.get('summary_digest'))[:12]}")
    return PersistedOutput(run_id=str(manifest.get("run_id", "")),
                           final_path=str(final),
                           partial_path=str(final) + PARTIAL_SUFFIX,
                           files=entries, summary_digest=summary)


def _identities(authorization: Mapping) -> dict:
    missing = [k for k in AUTHORIZATION_FIELDS
               if not str((authorization or {}).get(k, "")).strip()]
    if missing:
        raise MCInputError(
            "mc_output_identities_absent",
            f"the authorization carries no {missing}; the output must record "
            "what the run was authorized against, not a subset of it")
    return {k: str(authorization[k]) for k in AUTHORIZATION_FIELDS}


def _under(child: Path, ancestor: Path) -> bool:
    try:
        Path(child).resolve().relative_to(Path(ancestor).resolve())
    except (ValueError, OSError):
        return False
    return True
