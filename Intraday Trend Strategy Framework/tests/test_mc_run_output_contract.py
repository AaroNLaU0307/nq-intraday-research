"""THE OUTPUT CONTRACT for a governed real MC run, as behaviour.

Until `run_output` existed, `execute_full_mc` computed a complete run and
returned it as an in-memory object that the process then dropped. Everything
here is about the property that closed: the evidence survives the process,
it is written atomically, a failed attempt can never be mistaken for a
completed run, and the destination is decided before the run rather than by
whatever is running.

NO REAL MC IS EXECUTED. Every `RunnerResult` in this file is synthetic and
carries `test_only=True`; no `.dbn.zst` is opened, no protected Development
outcome is read, no governed run directory is created, and nothing is
written outside `tmp_path`. The one thing the ruled runs root is used for is
a path STRING the gate is asked about -- which is a question, not a write.
"""
import json
from pathlib import Path

import pytest

from itsf import contracts as _contracts
from itsf.mc import consumer as mcc
from itsf.mc import run_output as ro
from itsf.mc.atoms import MCInputError
from itsf.s0.handoff import McConsumerAbsent

RUNS_DIR = Path(_contracts.RULED_RUNS_ROOT) / "runs"

AUTHORIZATION = {
    "run_id": "MC-T000",
    "input_bundle_commit": "a" * 40,
    "mc_execution_commit": "e" * 40,
    "bundle_summary_digest": "1" * 64,
    "sealed_supplement_sha256": "b" * 64,
    "prereg_sha256": "c" * 64,
    "authorized_by": "Aaron",
    "output_path": "<set per test>",
}


def _result(**over):
    """A synthetic `RunnerResult`. `test_only=True` is load-bearing."""
    import scripts.mc_real_run as entry
    return entry.synthetic_result(run_id="MC-T000", **over)


def _authorization(destination):
    row = dict(AUTHORIZATION)
    row["output_path"] = str(destination)
    return row


def _persist(destination, result=None, **kw):
    return ro.persist_run_output(
        result if result is not None else _result(),
        destination=destination,
        authorization=_authorization(destination),
        manifest_sha256=kw.pop("manifest_sha256", "d" * 64), **kw)


# == 1. every required artifact class is persisted =========================

def test_a_completed_run_persists_every_required_artifact_class(tmp_path):
    """PROOF 1. What a run produced has to still exist afterwards.

    The four content artifacts plus the manifest, and the identities the run
    was authorized against recorded beside them -- run identity, execution
    code, input-bundle provenance, Development data, prereg, sealed
    supplement and the exact output root.
    """
    dest = tmp_path / "MC-T000_20260101T000000Z"
    persisted = _persist(dest)

    on_disk = sorted(p.name for p in dest.iterdir())
    assert on_disk == sorted(ro.ARTIFACT_NAMES + (ro.MANIFEST_NAME,)), on_disk
    assert persisted.n_files == len(ro.ARTIFACT_NAMES)

    identity = json.loads((dest / "RUN_IDENTITY.json").read_text("utf-8"))
    for field in ro.AUTHORIZATION_FIELDS:
        assert identity[field] == _authorization(dest)[field], field
    assert identity["development_manifest_sha256"] == "d" * 64
    assert identity["runs_root"] == str(ro.RULED_RUNS_DIR)

    seal = json.loads((dest / "SEAL_CANDIDATE.json").read_text("utf-8"))
    assert seal["seal_candidate"] and seal["verdict"] and \
        seal["grid_seal_status"]
    grid = json.loads((dest / "GRID_STANDING.json").read_text("utf-8"))
    assert grid["grid_convergence"] and grid["published_region_by_kind"]
    seeds = json.loads((dest / "PER_SEED_EVIDENCE.json").read_text("utf-8"))
    assert seeds["grid_evidence_by_seed"] and seeds["b_scales_by_seed"] \
        and seeds["arm_labels"]


def test_the_manifest_is_the_inventory_of_what_was_actually_written(tmp_path):
    """The digests come from re-reading the staged bytes, not from the
    objects that were meant to be written."""
    import hashlib
    dest = tmp_path / "MC-T000_20260101T000000Z"
    persisted = _persist(dest)
    manifest = json.loads((dest / ro.MANIFEST_NAME).read_text("utf-8"))
    for entry in manifest["files"]:
        raw = (dest / entry["name"]).read_bytes()
        assert entry["size"] == len(raw)
        assert entry["sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["summary_digest"] == persisted.summary_digest


# == 2/3. a partial is never a completed run ===============================

def test_a_partial_directory_is_not_a_completed_run(tmp_path):
    """PROOF 2. The staging name is the whole point: an interrupted write
    sits at `<dest>.partial` and the final name never appears."""
    dest = tmp_path / "MC-T000_20260101T000000Z"
    partial = dest.with_name(dest.name + ro.PARTIAL_SUFFIX)
    partial.mkdir(parents=True)
    (partial / "RUN_IDENTITY.json").write_text("{}", encoding="utf-8")

    assert not dest.exists(), "a staged attempt must not occupy the final name"
    with pytest.raises(MCInputError) as ei:
        _persist(dest)
    assert ei.value.code == "mc_output_partial_residue"
    assert not dest.exists(), "the refusal must not have created the final run"
    assert partial.exists(), "debris is disclosed, never silently removed"


def test_a_failure_before_finalization_leaves_no_completed_run(
        tmp_path, monkeypatch):
    """PROOF 3. The real failure mode: the write dies part-way through.

    The final directory must not exist, the staged one must, and what was
    written must still be there -- a failed attempt is evidence too, and
    deleting it would hide that the run was tried at all.
    """
    dest = tmp_path / "MC-T000_20260101T000000Z"
    partial = dest.with_name(dest.name + ro.PARTIAL_SUFFIX)
    calls = {"n": 0}
    real = Path.write_bytes

    def explode(self, data):
        calls["n"] += 1
        if calls["n"] > 2:
            raise OSError("disk went away mid-write")
        return real(self, data)

    monkeypatch.setattr(Path, "write_bytes", explode)
    with pytest.raises(OSError):
        _persist(dest)
    monkeypatch.undo()

    assert not dest.exists(), "an interrupted run must never look completed"
    assert partial.is_dir(), "the attempt must remain visible"
    staged = sorted(p.name for p in partial.iterdir())
    assert staged, "what was written before the failure is kept"
    assert ro.MANIFEST_NAME not in staged, (
        "a run that died mid-write has no inventory, which is exactly why "
        "it cannot be read back as a completed one")
    with pytest.raises(Exception):
        ro.read_persisted_output(partial)


def test_a_finalized_run_is_never_reused_or_overwritten(tmp_path):
    """PROOF 5. One run, one output. A second attempt at a finalized
    destination refuses rather than extending or replacing it."""
    dest = tmp_path / "MC-T000_20260101T000000Z"
    first = _persist(dest)
    with pytest.raises(MCInputError) as ei:
        _persist(dest)
    assert ei.value.code == "mc_output_already_finalized"
    assert ro.read_persisted_output(dest).summary_digest == \
        first.summary_digest, "the original evidence is untouched"


# == 4. the destination is the Owner's, not the caller's ===================

def test_a_test_only_result_may_not_be_finalized_in_the_ruled_root():
    """A synthetic result cannot be planted where governed evidence lives.

    This is what makes every other test in this file safe: the objects here
    are `test_only`, and `test_only` cannot reach the ruled runs root even
    if a destination pointed there.
    """
    dest = RUNS_DIR / "MC-T000_19700101T000000Z"
    with pytest.raises(MCInputError) as ei:
        _persist(dest)
    assert ei.value.code == "mc_output_test_only_in_ruled_root"
    assert not dest.exists()


def _gate(authorized, row, **kw):
    rel = _write_authorization(authorized, row)
    return mcc.authorize_real_mc(
        "", run_id=row["run_id"], input_bundle_commit=row[
            "input_bundle_commit"],
        sealed_supplement_sha256=row["sealed_supplement_sha256"],
        execution_checkout=lambda: (row["mc_execution_commit"], ()),
        path=rel, **kw)


def _write_authorization(directory, row):
    repo = Path(mcc.__file__).resolve().parents[3]
    target = directory / "MC_RUN_AUTHORIZATION.json"
    target.write_text(json.dumps(row), encoding="utf-8")
    return str(target.relative_to(repo)).replace("\\", "/")


@pytest.fixture()
def authorized(request):
    repo = Path(mcc.__file__).resolve().parents[3]
    d = repo / ".pytest-mc-output" / request.node.name
    d.mkdir(parents=True, exist_ok=True)
    yield d
    for p in sorted(d.rglob("*"), reverse=True):
        p.unlink() if p.is_file() else p.rmdir()
    d.rmdir()
    try:
        d.parent.rmdir()
    except OSError:
        pass


def test_an_output_path_the_code_does_not_name_refuses(authorized):
    """PROOF 4. The authorization and the executing code must agree on
    exactly one destination."""
    row = _authorization(RUNS_DIR / "MC-T000_19700101T000000Z")
    row["prereg_sha256"] = mcc._prereg_sha256()
    row["sentence"] = mcc.MC_AUTHORIZATION_SENTENCE.format(
        run_id=row["run_id"],
        mc_execution_commit=row["mc_execution_commit"],
        input_bundle_commit=row["input_bundle_commit"])
    with pytest.raises(McConsumerAbsent, match="does not authorize another"):
        _gate(authorized, row,
              output_path=str(RUNS_DIR / "MC-T000_19700101T000001Z"))


def test_an_output_path_outside_the_ruled_runs_root_refuses(authorized,
                                                            tmp_path):
    """PROOF 4. Governed evidence lives in the ruled runs root, and an
    authorization naming anywhere else is refused before the run starts."""
    stray = tmp_path / "MC-T000_19700101T000000Z"
    row = _authorization(stray)
    row["prereg_sha256"] = mcc._prereg_sha256()
    row["sentence"] = mcc.MC_AUTHORIZATION_SENTENCE.format(
        run_id=row["run_id"],
        mc_execution_commit=row["mc_execution_commit"],
        input_bundle_commit=row["input_bundle_commit"])
    with pytest.raises(McConsumerAbsent, match="ruled runs root"):
        _gate(authorized, row, output_path=str(stray))


def test_an_output_path_that_already_exists_refuses(authorized, tmp_path):
    """PROOF 5, at the gate. A destination with something already in it is
    refused before a single byte of the bundle is read -- which is what
    stops a second MC-R001 from being pointed at the first one's output."""
    existing = RUNS_DIR / "S0-T001_20260813T170432Z"
    assert existing.exists(), "the sealed S0 run is the stand-in for an " \
        "already-occupied destination"
    row = _authorization(existing)
    row["prereg_sha256"] = mcc._prereg_sha256()
    row["sentence"] = mcc.MC_AUTHORIZATION_SENTENCE.format(
        run_id=row["run_id"],
        mc_execution_commit=row["mc_execution_commit"],
        input_bundle_commit=row["input_bundle_commit"])
    with pytest.raises(McConsumerAbsent, match="already exists"):
        _gate(authorized, row, output_path=str(existing))


def test_the_runner_refuses_a_destination_the_authorization_did_not_bind():
    """The binding is re-checked where the run is actually configured, so a
    runner cannot be handed a different destination than the gate approved."""
    from itsf.mc import mc_runner as run
    row = _authorization(RUNS_DIR / "MC-R999_19700101T000000Z")
    row["run_id"] = "MC-R999"
    row["authorized_commit"] = row["input_bundle_commit"]
    with pytest.raises(MCInputError) as ei:
        run.bind_owner_authorization(
            row, run_id=row["run_id"],
            input_bundle_commit=row["input_bundle_commit"],
            output_root=str(RUNS_DIR / "MC-R999_19700101T000001Z"),
            bundle_summary_digest=row["bundle_summary_digest"])
    assert ei.value.code == "mc_run_output_path_mismatch"


# == 6. what was written re-reads to the same identities ===================

def test_persisted_artifacts_reread_to_the_identities_they_were_written_with(
        tmp_path):
    """PROOF 6. `read_persisted_output` re-hashes every file and recomputes
    the summary rather than believing the manifest."""
    dest = tmp_path / "MC-T000_20260101T000000Z"
    written = _persist(dest)
    reread = ro.read_persisted_output(dest)
    assert reread.summary_digest == written.summary_digest
    assert [(e.name, e.size, e.sha256) for e in reread.files] == \
           [(e.name, e.size, e.sha256) for e in written.files]


def test_a_tampered_artifact_is_caught_on_reread(tmp_path):
    """The identities are checkable, not merely recorded: a byte changed
    after finalization no longer matches the manifest it was written with."""
    dest = tmp_path / "MC-T000_20260101T000000Z"
    _persist(dest)
    p = dest / "SEAL_CANDIDATE.json"
    p.write_bytes(p.read_bytes().replace(b"PROBE", b"OTHER"))
    with pytest.raises(MCInputError) as ei:
        ro.read_persisted_output(dest)
    assert ei.value.code == "mc_output_inventory_mismatch"


def test_the_same_result_persists_to_the_same_digest(tmp_path):
    """Deterministic bytes: the same run written twice, to two places,
    produces the same inventory digest."""
    a = _persist(tmp_path / "MC-T000_20260101T000000Z")
    b = _persist(tmp_path / "MC-T000_20260102T000000Z")
    identity_only = {e.name: e.sha256 for e in a.files
                     if e.name != "RUN_IDENTITY.json"}
    assert identity_only == {e.name: e.sha256 for e in b.files
                             if e.name != "RUN_IDENTITY.json"}


def test_an_authorization_missing_identities_cannot_be_persisted(tmp_path):
    """The output records what the run was authorized against. A subset is
    refused rather than written as a partial record."""
    dest = tmp_path / "MC-T000_20260101T000000Z"
    row = _authorization(dest)
    row.pop("prereg_sha256")
    with pytest.raises(MCInputError) as ei:
        ro.persist_run_output(_result(), destination=dest, authorization=row,
                              manifest_sha256="d" * 64)
    assert ei.value.code == "mc_output_identities_absent"
    assert not dest.exists()


# == 7. the console never interprets the research ==========================

def test_the_entrypoint_reports_identities_and_never_the_verdict(tmp_path,
                                                                capsys):
    """PROOF 7. The verdict is IN the evidence and NOT on the console.

    `_report` is handed a persisted mapping and must emit the operational
    facts only. The synthetic result's verdict token is deliberately
    distinctive so its absence is provable.
    """
    import scripts.mc_real_run as entry
    dest = tmp_path / "MC-T000_20260101T000000Z"
    persisted = _persist(dest)
    entry._report(persisted.as_mapping(), exec_commit="e" * 40)
    out = capsys.readouterr()
    text = out.out + out.err
    assert "MC-T000" in text and persisted.summary_digest in text
    assert str(dest) in text
    for forbidden in ("PROBE", "verdict", "seal_candidate", "region",
                      "may_support_h1_entry"):
        assert forbidden not in text, forbidden


def test_no_research_content_reaches_the_console_from_main():
    """The source-level property behind the test above: `main` hands the
    console `_report` and nothing else from the result."""
    import ast
    import inspect
    import scripts.mc_real_run as entry
    tree = ast.parse(inspect.getsource(entry.main))
    written = [n for n in ast.walk(tree)
               if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute)
               and n.func.attr == "write"]
    for call in written:
        rendered = ast.dump(call)
        assert "verdict" not in rendered and "seal_candidate" not in rendered


# == 8. nothing here runs a real MC ========================================

def test_this_module_executes_no_real_mc():
    """PROOF 8, pinned at the source level: no test here reaches the real
    runner entry, and every result it builds is `test_only`."""
    import ast
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {n.func.attr if isinstance(n.func, ast.Attribute)
              else getattr(n.func, "id", "")
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "execute_full_mc" not in called
    assert "run_epistemic" not in called
    assert _result().test_only is True


# == 9. the wiring the launcher will use ===================================

def test_the_probe_exercises_the_same_persistence_the_run_uses(tmp_path):
    """PROOF 9's in-process half: `output_contract_probe` stages, promotes
    and re-reads through the same `run_output` functions `execute_full_mc`
    calls. The launcher half is the same function run through
    `run_governed.cmd`."""
    import scripts.mc_real_run as entry
    assert entry.output_contract_probe(str(tmp_path)) == 0
    dest = tmp_path / "MC-PROBE_00000000T000000Z"
    assert ro.read_persisted_output(dest).n_files == len(ro.ARTIFACT_NAMES)


def test_the_runner_persists_before_it_returns():
    """The property that makes evidence survive the process: persistence is
    inside `execute_full_mc`, not in whoever called it."""
    import ast
    import inspect
    from itsf.mc import mc_runner as run
    tree = ast.parse(inspect.getsource(run.execute_full_mc))
    called = {n.func.attr if isinstance(n.func, ast.Attribute)
              else getattr(n.func, "id", "")
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "persist_run_output" in called, (
        "a caller that forgets to persist would lose the entire run; the "
        "write belongs to the run, not to the caller")


def test_the_entry_writes_only_to_the_code_pinned_destination():
    """The destination is fixed by the executing commit, and the argument
    the runner is handed is that constant -- not a caller's path."""
    import ast
    import inspect
    import scripts.mc_real_run as entry
    assert entry.OUTPUT_PATH.parent == entry.RUNS_ROOT
    assert entry.OUTPUT_PATH.name.startswith("MC-R001_")
    source = inspect.getsource(entry.main)
    assert "output_root=str(OUTPUT_PATH)" in source
    assert "str(REPO)" not in source, (
        "the repository is not an output root")
    tree = ast.parse(source)
    assert not [a for n in ast.walk(tree) if isinstance(n, ast.Call)
                for a in getattr(n, "keywords", [])
                if a.arg == "output_root"
                and not isinstance(a.value, ast.Call)], \
        "output_root must be the pinned constant, never a caller value"
