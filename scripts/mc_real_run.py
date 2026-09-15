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

THE BUNDLE ROOT IS PINNED IN CODE, and this file does not pin it.
`real_input.SEALED_RUN_DIR` has named the Owner-bound sealed run directory
since R2.1. (An earlier version of this docstring said no pinned root
existed; that was wrong, and duplicating what `real_input` already owned is
what broke the second launch.) The argument is still required, with no
default: it makes the caller STATE which root it believes it is running, and
a disagreement with the pinned one refuses.

WHERE THE EVIDENCE GOES. `OUTPUT_PATH` below is the exact final directory,
fixed in code so the executing commit determines it, and the Owner
authorization must name the same path. `execute_full_mc` writes the run's
evidence there through `run_output` -- staged in `<path>.partial`, verified,
promoted by one rename -- BEFORE it returns. Until that existed, a completed
real run returned an in-memory object and the process dropped it.

WHAT THIS CONSOLE SAYS, and what it never says. Operational identities only:
completed, run id, output path, inventory digests, execution commit. The
verdict, the seal candidate and every statistic are in the evidence and not
on the console -- printing them would interpret the research before S4
exists to do it.

ONE ASSEMBLY. The prepared input is built by
`real_input._assemble_from_sealed_run` and by nothing here -- see the
comment at the call site, and
`test_the_assembly_is_real_inputs_and_this_file_does_not_hand_roll_it`.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

#: The run this entrypoint starts. One id, spelled once.
RUN_ID = "MC-R001"

#: THE EXACT FINAL OUTPUT DIRECTORY, decided BEFORE the run and pinned in
#: code so the executing commit fixes it. The Owner authorization must name
#: this same path; the gate compares the two, checks it sits directly under
#: the ruled runs root, and refuses if anything is already there. A run that
#: chose its own destination at write time would be a run whose evidence
#: location nobody agreed to in advance.
#:
#: The stamp is a LABEL, not a clock reading: it is the UTC instant this
#: destination was fixed, and it does not move when the run happens to
#: start.
#:
#: IT IS ALSO THE PHYSICAL ATTEMPT IDENTITY, and the reason it changed.
#: MC-R001 is one SCIENTIFIC TRIAL; this path is one PHYSICAL ATTEMPT at
#: computing it. Attempt 1 (`MC-R001_20260913T063102Z`, fixed
#: 2026-09-13T06:31:02Z) ran 39h52m and was destroyed by a Windows Update
#: restart with nothing persisted and no outcome exposed; Aaron ruled it
#: FAILED_AFTER_SUBSTANTIVE_START and the same trial recomputable. Attempt 2
#: therefore keeps the trial id and takes a new stamp -- which is not merely
#: convention: the gate REFUSES an `output_path` that already exists, so a
#: second attempt cannot be pointed at the first one's identity even by
#: mistake.
RUNS_ROOT = Path(r"C:\Users\Aaron\quant-data\itsf-runs\runs")
OUTPUT_PATH = RUNS_ROOT / "MC-R001_20260915T080712Z"

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
    from itsf.mc import run_output as _ro

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
        "output_path": str(OUTPUT_PATH),
        "output_path_exists": OUTPUT_PATH.exists(),
        "partial_path": str(OUTPUT_PATH) + _ro.PARTIAL_SUFFIX,
        "partial_path_exists": Path(
            str(OUTPUT_PATH) + _ro.PARTIAL_SUFFIX).exists(),
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


def synthetic_result(**over):
    """A `RunnerResult` shaped like a real one and carrying no research.

    `test_only=True` is the load-bearing field: `run_output` REFUSES to
    finalize a test-only result anywhere under the ruled runs root, so this
    object cannot be used to plant something that looks like governed
    evidence. Its numbers are placeholders with no meaning.
    """
    from itsf.mc.mc_runner import RunnerResult
    row = dict(
        run_id="MC-PROBE", authorized_commit="0" * 40,
        output_root="<probe>",
        seal_candidate={"verdict": {"category": "PROBE", "reason": "probe"}},
        verdict="PROBE", grid_seal_status="PROBE",
        may_support_h1_entry=False,
        published_region_by_kind={"probe": {"cell": "probe"}},
        grid_convergence={"schema": "probe"},
        grid_evidence_by_seed={7: {"cell": "probe"}},
        b_scales_by_seed={7: (1, 2)}, arm_labels=("probe",), test_only=True)
    row.update(over)
    return RunnerResult(**row)


def output_contract_probe(dest: str = "") -> int:
    """EXERCISE THE OUTPUT WIRING. Runs no MC, touches no governed path.

    This is the launcher-visible proof that the persistence path works in
    the child process the real run would use: it stages, verifies, promotes
    and then RE-READS a synthetic run output through exactly the functions
    `execute_full_mc` calls. It cannot produce governed evidence -- the
    result is `test_only`, which `run_output` refuses to finalize under the
    ruled runs root -- and it prints identities only, like the real report.

    It exists because the two MC-R001 launch failures were both in glue that
    nothing had ever executed. Glue that is never run is glue that is wrong.
    """
    import tempfile
    from itsf.mc import run_output as _ro

    root = Path(dest) if dest else Path(tempfile.mkdtemp(prefix="mc-probe-"))
    destination = root / "MC-PROBE_00000000T000000Z"
    authorization = {
        "run_id": "MC-PROBE", "input_bundle_commit": "0" * 40,
        "mc_execution_commit": "0" * 40, "bundle_summary_digest": "0" * 64,
        "sealed_supplement_sha256": "0" * 64, "prereg_sha256": "0" * 64,
        "authorized_by": "probe", "output_path": str(destination)}
    persisted = _ro.persist_run_output(
        synthetic_result(), destination=destination,
        authorization=authorization, manifest_sha256="0" * 64)
    reread = _ro.read_persisted_output(destination)
    if reread.summary_digest != persisted.summary_digest:
        sys.stderr.write("mc_real_run: PROBE FAILED — re-read digest differs\n")
        return 1
    _report(persisted.as_mapping(), exec_commit="<probe>")
    sys.stderr.write("mc_real_run:   re-read             %s\n"
                     % reread.summary_digest)
    return 0


def main(bundle_root: str = "") -> int:
    """The real run. Refuses before reading anything without the Owner."""
    from itsf.mc import consumer as mcc
    from itsf.mc import mc_runner as run
    from itsf.mc import real_input as _real_input
    from itsf.mc.registry_boundary import resolve_registry

    # THE BUNDLE ROOT IS PINNED IN CODE as `real_input.SEALED_RUN_DIR`, and
    # has been since R2.1. The argument exists so the caller STATES which
    # root it believes it is running; a disagreement refuses rather than
    # silently preferring one of them.
    if bundle_root and Path(bundle_root) != _real_input.SEALED_RUN_DIR:
        sys.stderr.write(
            "mc_real_run: REFUSING — the supplied bundle root %s is not the "
            "pinned sealed run directory %s"
            % (bundle_root, _real_input.SEALED_RUN_DIR) + chr(10))
        return 4
    if not bundle_root:
        sys.stderr.write(
            "mc_real_run: REFUSING — no bundle root supplied. It is pinned "
            "as real_input.SEALED_RUN_DIR and the argument must state it.\n")
        return 2

    # THE HOST, BEFORE ANYTHING ELSE. MC-R001 spent 39h52m of computation
    # and was then destroyed by a Windows Update planned restart. Nothing
    # had ever looked at whether the machine was already waiting to
    # restart. This refuses when it is -- and it is NOT protection: it
    # cannot stop a restart, it can only decline to start a multi-day run
    # on top of one that is already scheduled. The remaining risk is the
    # Owner's to manage outside this process.
    from itsf import host_preflight as _hp
    try:
        context = _hp.assert_host_fit_for_long_run()
    except _hp.HostNotFitError as exc:
        sys.stderr.write("mc_real_run: REFUSING - %s" % exc + chr(10))
        return 5
    _report_host(context)

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
    #
    # `path=` is passed EXPLICITLY. The gate takes it as a default argument,
    # which binds at definition time, so `MC_AUTHORIZATION_PATH` and the path
    # actually consulted could silently differ -- and `_declared_commit` below
    # reads the module constant. Passing it keeps one authority for where the
    # authorization lives, and makes the two reads provably the same file.
    mcc.authorize_real_mc(
        resolution.snapshot.text,
        run_id=RUN_ID,
        input_bundle_commit=_declared_commit(mcc),
        sealed_supplement_sha256=supplement_sha,
        output_path=str(OUTPUT_PATH),
        path=mcc.MC_AUTHORIZATION_PATH)

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
        bundle_summary_digest=precheck.summary_digest,
        output_path=str(OUTPUT_PATH),
        path=mcc.MC_AUTHORIZATION_PATH)
    commit = str(authorization["input_bundle_commit"])
    # THE ASSEMBLY IS `real_input`'s, NOT THIS FILE'S.
    #
    # `_assemble_from_sealed_run` has been the production prepare caller
    # since R2.1 PHASE F: it reads the attestation, constructs the custody
    # authority INSIDE `prepare_mc_input`, and builds the authorization
    # snapshot as the `{trial_id, authorized_commit}` mapping that function
    # requires. This file hand-rolled that and got it wrong -- it passed the
    # REGISTRY snapshot, an object carrying none of those keys, and
    # `prepare_mc_input` refused `authorization_snapshot_missing` after the
    # bundle had already been read. There is one assembly, and this was
    # never it.
    prepared = _real_input._assemble_from_sealed_run()
    if prepared.authorized_commit != commit:
        sys.stderr.write(
            "mc_real_run: REFUSING — the authorization names commit %s and "
            "the prepared input is bound to %s\n"
            % (commit[:12], str(prepared.authorized_commit)[:12]))
        return 3

    # `execute_full_mc` writes the run's evidence to the bound destination
    # before returning; `persisted_output` is where it went and what it
    # hashes to.
    result = run.execute_full_mc(
        prepared, run_id=RUN_ID, output_root=str(OUTPUT_PATH),
        supplement=supplement, sealed_artifact_sha256=supplement_sha,
        bundle_summary_digest=precheck.summary_digest)
    _report(result.persisted_output, exec_commit=_head_commit(mcc))
    _archive(result.persisted_output)
    return 0


def _report_host(context) -> None:
    """The host facts, on the record before the run starts.

    Operational only. None of it refuses; it exists so that a run which
    later dies to the environment can be read against what the environment
    looked like when it was started.
    """
    w = sys.stderr.write
    span = context.get("active_hours_span_hours")
    w("mc_real_run: host preflight OK - no pending reboot marker" + chr(10))
    w("mc_real_run:   pending_file_renames %s" % context.get(
        "pending_file_rename_operations") + chr(10))
    w("mc_real_run:   active_hours         %s-%s (span %s h)"
      % (context.get("active_hours_start"), context.get("active_hours_end"),
         span) + chr(10))
    w("mc_real_run:   updates_paused_until %s" % context.get(
        "updates_paused_until") + chr(10))
    if span is not None and span < 24:
        w("mc_real_run:   NOTE Active Hours cannot cover a run longer than "
          "its span; a restart outside it is permitted by design"
          + chr(10))


def _report(persisted, *, exec_commit: str) -> None:
    """OPERATIONAL IDENTITIES ONLY, and this is a hard boundary.

    The verdict, the seal candidate, the region maps and every statistic the
    run produced are IN the evidence and NOT on this console. A runner that
    prints its own verdict has interpreted the research before S4 exists to
    do it, and once printed it cannot be un-seen. What belongs here is what
    an operator needs: did it finish, where is the evidence, and what does
    that evidence hash to.
    """
    w = sys.stderr.write
    w("mc_real_run: COMPLETED %s\n"
      % persisted.get("run_id", RUN_ID))
    w("mc_real_run:   mc_execution_commit %s\n" % exec_commit)
    w("mc_real_run:   output_path         %s\n"
      % persisted.get("final_path", "<absent>"))
    w("mc_real_run:   summary_digest      %s\n"
      % persisted.get("summary_digest", "<absent>"))
    w("mc_real_run:   artifacts           %s\n"
      % persisted.get("n_files", 0))
    for entry in persisted.get("files", ()):
        w("mc_real_run:     %-22s %9d  %s\n"
          % (entry["name"], entry["size"], entry["sha256"]))


def _archive(persisted) -> None:
    """Mirror the finalized output with the EXISTING archive machinery.

    `runinfra.archive_sealed_run` already owns this: per-file re-read on
    both sides, `.partial` staging, never overwrites, never mutates the
    source. It is reused unchanged.

    An archive problem is reported and never raised. The run is already
    complete and its evidence already written; letting a copy failure
    propagate would turn a finished governed run into a failed one, which it
    structurally is not -- the same holding `s0/runner._archive_sealed_run`
    records.
    """
    from itsf import contracts as _c
    from itsf.s0 import runinfra
    final = persisted.get("final_path", "")
    if not final:
        return
    try:
        report = runinfra.archive_sealed_run(final, _c.RULED_ARCHIVE_ROOT)
        status, detail = report.status, report.dest_dir
    except Exception as exc:                                # noqa: BLE001
        status, detail = "archive_failed", "%s: %s" % (type(exc).__name__, exc)
    sys.stderr.write("mc_real_run:   archive             %s %s\n"
                     % (status, detail))


def _head_commit(mcc) -> str:
    """The executing commit, re-measured for the report."""
    try:
        return mcc.mc_execution_checkout()[0]
    except Exception:                                       # noqa: BLE001
        return "<unmeasured>"


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
