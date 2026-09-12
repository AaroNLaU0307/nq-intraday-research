"""THE production MC entrypoint. Gate-first, and inert without the Owner.

Run it through the trusted launch boundary, never directly:

    scripts\\run_governed.cmd scripts.mc_real_run:main <bundle_root>

WHY THIS FILE EXISTS. `mc_runner.execute_full_mc` is the production
function, but nothing assembled its inputs, so the only callers in the tree
were a probe template and tests. A production function with no production
caller is a function nobody can run and nobody can check.

WHAT IT DOES, IN ORDER, AND THE ORDER IS THE POINT:

  1. resolve the registry snapshot (read-only);
  2. ASK THE GATE FIRST, with the run id, the commit and the sealed
     supplement digest. Without the Owner's authorization this refuses here
     -- before any bundle byte, any attestation byte and any bar is read;
  3. only then re-derive the sealed bundle from DISK
     (`bundle_precheck.precheck_bundle_on_disk`), build the prepared input
     through the production battery, and call `execute_full_mc`.

Step 2 before step 3 is what makes an unauthorized invocation cost nothing:
it reads no protected Development outcome, opens no `.dbn.zst`, consumes no
exposure and writes nothing.

WHAT IT DOES NOT DO. It does not rebuild the retired five-event MC registry
chain and it does not require `SMOKE-001`. Both come from
`ops/DELEGATED_RULINGS_2026-08-24.md`, whose header records
`RECORD_TYPE=DELEGATED_RULING` and `DELEGATED=YES -- this is a delegated
ruling, NOT Aaron's own judgement`; neither appears in the sealed
preregistration, the FROZEN `MC_METHOD_SPEC`, the charter, or any Aaron
OWNER_DECISION row. Under `QUANT_WORKFLOW_VNEXT` §0 that is level-4 project
history. What IS current is vNext §10: a real Monte Carlo run is Owner-only,
and `consumer.authorize_real_mc` is where that is enforced.

BUNDLE ROOT IS A REQUIRED ARGUMENT WITH NO DEFAULT, deliberately. No pinned
governed bundle root exists in code -- `AUTHORIZED_JOB_DIR` pins the vendor
job directory, not the 14-file sealed bundle -- and inventing one would be a
builder choosing a data root. That is Aaron's, exactly as the job directory
was.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

#: The run this entrypoint starts. One id, spelled once.
RUN_ID = "MC-R001"

#: The sealed DAY_STRATA supplement the run consumes, and its digest as the
#: registry recorded it at `SUPPLEMENT_SEALED`. Both are checked; neither is
#: taken on the artifact's word.
SUPPLEMENT_PATH = Path(
    r"C:\Users\Aaron\quant-data\itsf-runs\supplements"
    r"\MC-DS-S004_20260906T135831Z\DAY_STRATA_SUPPLEMENT.json")
SUPPLEMENT_SEALED_SHA256 = (
    "f59a009213f2e3b9ce3b4b4937c1945227c89e724fc6c4fa0c063d0326417e4d")


def _sealed_supplement() -> tuple:
    """`(supplement, sha256)` -- read from disk, digest recomputed.

    The digest is recomputed over the canonical bytes the rest of the system
    uses, so this cannot pass a file whose contents drift from the sealed
    record.
    """
    import hashlib
    import json
    from itsf.mc import day_strata_supplement as ds

    if not SUPPLEMENT_PATH.is_file():
        raise FileNotFoundError(
            "the sealed DAY_STRATA supplement is not at %s" % SUPPLEMENT_PATH)
    supplement = json.loads(SUPPLEMENT_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(
        ds.canonical_supplement_bytes(supplement)).hexdigest()
    if digest != SUPPLEMENT_SEALED_SHA256:
        raise ValueError(
            "the supplement on disk hashes to %s, and the registry sealed "
            "%s" % (digest[:12], SUPPLEMENT_SEALED_SHA256[:12]))
    return supplement, digest


def authorization_preview() -> dict:
    """WHAT THE GATE WOULD BE ASKED. Reads nothing protected, runs nothing.

    Exists so the run identity and its bindings can be inspected before an
    authorization is written, without going near the runner. It reports the
    facts the Owner's authorization has to name; it does not report whether
    an authorization exists, and it cannot start anything.
    """
    from itsf.mc import consumer as mcc

    _supplement, digest = _sealed_supplement()
    return {
        "run_id": RUN_ID,
        "sealed_supplement_sha256": digest,
        "prereg_sha256": mcc._prereg_sha256(),
        "authorization_path": mcc.MC_AUTHORIZATION_PATH,
        "sentence_template": mcc.MC_AUTHORIZATION_SENTENCE,
        "input_bundle_commit":
            "<the commit the prepared input is bound to>",
        "mc_execution_commit": mcc.mc_execution_checkout()[0],
        "governed_paths_modified": list(mcc.mc_execution_checkout()[1]),
        "bundle_summary_digest": "<run bundle_identity(root) to measure it>",
    }


def bundle_identity(bundle_root: str) -> dict:
    """The sealed bundle's governed identity, measured from disk.

    Re-derives the 14-file table through the production precheck -- the same
    call the run makes -- and reports its summary digest. It reports
    identity only: no file content is returned, displayed or interpreted.
    """
    from itsf.mc.bundle_precheck import precheck_bundle_on_disk

    pc = precheck_bundle_on_disk(Path(bundle_root))
    return {
        "bundle_root": str(Path(bundle_root)),
        "n_files": pc.n_files,
        "expected_source": pc.expected_source,
        "bundle_summary_digest": pc.summary_digest,
        "total_bytes": sum(int(e.size) for e in pc.recomputed),
        "names": tuple(sorted(e.name for e in pc.recomputed)),
    }


def main(bundle_root: str = "", output_root: str = "") -> int:
    """The real run. Refuses before reading anything without the Owner."""
    from itsf.mc import consumer as mcc
    from itsf.mc import mc_runner as run
    from itsf.mc.registry_boundary import resolve_registry

    if not bundle_root:
        sys.stderr.write(
            "mc_real_run: REFUSING — no bundle root supplied. There is no "
            "pinned governed bundle root in code and this entrypoint will "
            "not invent one; the sealed 14-file bundle's location is the "
            "Owner's to name, as the vendor job directory was.\n")
        return 2

    # THE TRUSTED-LAUNCH GATE, with the production defaults. Every sanctioned
    # real-run entry binds to it, and binding to it IS binding to the trusted
    # launch: run outside `run_governed.cmd` and this refuses here. It reads
    # two attestation flags and no data.
    from itsf.guards import assert_real_run_allowed
    assert_real_run_allowed()

    supplement, supplement_sha = _sealed_supplement()
    resolution = resolve_registry()

    # ---- THE GATE, BEFORE ANY DATA IS OPENED --------------------------
    #
    # `prepared.authorized_commit` is what the gate binds to, and building a
    # prepared input means reading the bundle. So the commit is taken here
    # from the authorization itself and re-checked against the prepared
    # input below: the gate refuses an unauthorized call at zero cost, and
    # a mismatched one before the run starts.
    mcc.authorize_real_mc(
        resolution.snapshot.text,
        run_id=RUN_ID,
        input_bundle_commit=_declared_commit(mcc),
        sealed_supplement_sha256=supplement_sha)

    # ---- only now is anything read -----------------------------------
    #
    # The bundle is re-derived from DISK and summarised, and the gate is
    # asked AGAIN with that summary. Phase one above cost nothing and
    # refused an unauthorized caller; phase two is what binds the run to
    # THIS bundle, and `bind_owner_authorization` refuses without it.
    from itsf.mc.bundle_precheck import precheck_bundle_on_disk

    precheck = precheck_bundle_on_disk(Path(bundle_root))
    authorization = mcc.authorize_real_mc(
        resolution.snapshot.text,
        run_id=RUN_ID,
        input_bundle_commit=_declared_commit(mcc),
        sealed_supplement_sha256=supplement_sha,
        bundle_summary_digest=precheck.summary_digest)
    commit = str(authorization["input_bundle_commit"])
    bundle = {e.name: (Path(bundle_root) / e.name).read_bytes()
              for e in precheck.recomputed}
    attestation = (REPO / mcc.ATTESTATION_PATH).read_bytes()
    prepared = mcc.prepare_mc_input(
        bundle, authorization_snapshot=resolution.snapshot,
        attestation_bytes=attestation)
    if prepared.authorized_commit != commit:
        sys.stderr.write(
            "mc_real_run: REFUSING — the authorization names commit %s and "
            "the prepared input is bound to %s\n"
            % (commit[:12], str(prepared.authorized_commit)[:12]))
        return 3

    result = run.execute_full_mc(
        prepared, run_id=RUN_ID, output_root=output_root or str(REPO),
        supplement=supplement, sealed_artifact_sha256=supplement_sha,
        bundle_summary_digest=precheck.summary_digest)
    sys.stderr.write("mc_real_run: completed %s\n" % result.run_id)
    return 0


def _declared_commit(mcc) -> str:
    """The commit the authorization on disk names, or "" when there is none.

    Reading it here is not trusting it: the gate re-derives the sentence
    from it, and `main` re-checks it against the prepared input's own
    binding. Without this the gate could not be asked BEFORE the bundle is
    read, and asking it afterwards is what makes an unauthorized call
    expensive.
    """
    import json
    path = REPO / mcc.MC_AUTHORIZATION_PATH
    if not path.is_file():
        return ""
    try:
        return str(json.loads(path.read_text(encoding="utf-8"))
                   .get("input_bundle_commit", "")).strip()
    except Exception:                                       # noqa: BLE001
        return ""


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main(*sys.argv[1:]))
