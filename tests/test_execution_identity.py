"""T-F01: the governed-execution identity, the environment pin, and the
dependency register (QROS-CF v2 §2.2; DEC-0006 I1; DEC-0008 Condition A).

WHAT IS PROVED, and it is behavioural, as Condition A demands: for every
class of production-semantic input, changing it after authorization either
changes the authorized identity or causes a refusal before the first write.

    repository files       identity (toy git repository, per path class)
    tier-C test edits      NOT in the identity (a README-index test edit
                           does not void an authorization), while a tier-A
                           test edit or deletion does
    environment variables  environment pin -> gate refuses; seam refuses
    package drift          environment pin (lockfile) -> gate refuses
    interpreter            environment pin (.python-version)
    calendars              gate1/ is inside the identity (frozen csv files)
    data identity          the AUTHORIZED manifest pin, per-file sha256,
                           and -- new at I1 -- condition.json verified
                           before it is read
    check-then-replace     the first-write seam re-checks HEAD, the
                           governed worktree and the environment

The read-set derivation instruments the production entry points on
synthetic input with `sys.addaudithook` and refuses any repository path
they open that no mechanism in `DEPENDENCY_REGISTER` covers.

NO REAL DATA IS READ. The registry is read (not quarantined); git is asked
for HEAD; the two calendar CSVs are opened -- all of which the existing
precheck tests already do.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from itsf import execution_identity as ei
from itsf.mc import supplement_runner as sr

REPO = Path(__file__).resolve().parents[1]
HEAD40 = "a" * 40
OTHER40 = "b" * 40


# ---------------------------------------------------------------------------
# a toy repository, so each path class can be perturbed in isolation
# ---------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t",
                          "-c", "user.email=t@t", "-c", "core.autocrlf=false",
                          *args], capture_output=True, text=True,
                         encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def toy(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("X = 1\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "run.py").write_text("print(1)\n", encoding="utf-8")
    (repo / "gate1").mkdir()
    (repo / "gate1" / "events.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (repo / "ops").mkdir()
    (repo / "ops" / "x.md").write_text("doc\n", encoding="utf-8")
    (repo / "ops" / "requirements.lock.txt").write_text("numpy==1.0\n",
                                                        encoding="utf-8")
    (repo / ".python-version").write_text("3.13\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "conftest.py").write_text("# conftest\n", encoding="utf-8")
    (repo / "tests" / "tiers.py").write_text(
        'GOVERNANCE_FILES = ("test_index.py",)\n', encoding="utf-8")
    (repo / "tests" / "test_leak.py").write_text("def test_a():\n    pass\n",
                                                 encoding="utf-8")
    (repo / "tests" / "test_index.py").write_text("def test_i():\n    pass\n",
                                                  encoding="utf-8")
    base = _commit(repo, "base")
    return repo, base


def _touch_and_commit(repo: Path, rel: str, text: str = "changed\n") -> str:
    (repo / rel).write_text(text, encoding="utf-8")
    return _commit(repo, f"edit {rel}")


def test_identity_is_blind_to_ops_documents_and_tier_c_test_edits(toy):
    repo, base = toy
    after_doc = _touch_and_commit(repo, "ops/x.md")
    cmp = ei.compare(after_doc, base, repo)
    assert cmp.matches, cmp.detail
    after_tier_c = _touch_and_commit(repo, "tests/test_index.py",
                                     "def test_i():\n    assert True\n")
    cmp = ei.compare(after_tier_c, base, repo)
    assert cmp.matches, cmp.detail


@pytest.mark.parametrize("rel", [
    "src/a.py", "scripts/run.py", "gate1/events.csv",
    "ops/requirements.lock.txt", ".python-version", "tests/conftest.py",
    "tests/test_leak.py",
])
def test_identity_sees_every_governed_path_class(toy, rel):
    repo, base = toy
    after = _touch_and_commit(repo, rel)
    cmp = ei.compare(after, base, repo)
    assert not cmp.matches
    assert cmp.differing == (rel,), cmp.differing


def test_identity_sees_a_change_to_the_tier_map_itself(toy):
    repo, base = toy
    after = _touch_and_commit(repo, "tests/tiers.py",
                              'GOVERNANCE_FILES = ("test_index.py",)  # edited\n')
    cmp = ei.compare(after, base, repo)
    assert not cmp.matches and "tests/tiers.py" in cmp.differing


def test_identity_sees_a_deleted_tier_a_test(toy):
    repo, base = toy
    (repo / "tests" / "test_leak.py").unlink()
    after = _commit(repo, "delete the leakage test")
    cmp = ei.compare(after, base, repo)
    assert not cmp.matches and cmp.differing == ("tests/test_leak.py",)


def test_moving_a_test_into_tier_c_changes_the_identity(toy):
    """Reclassifying a test as governance REMOVES it from the identity, so
    the reclassification itself must be visible: tiers.py is governed."""
    repo, base = toy
    after = _touch_and_commit(
        repo, "tests/tiers.py",
        'GOVERNANCE_FILES = ("test_index.py", "test_leak.py")\n')
    cmp = ei.compare(after, base, repo)
    assert not cmp.matches
    assert "tests/tiers.py" in cmp.differing
    assert "tests/test_leak.py" in cmp.differing      # present at base, absent after


def test_a_commit_without_a_tier_map_governs_every_test_file(toy):
    repo, base = toy
    (repo / "tests" / "tiers.py").unlink()
    after = _commit(repo, "no tier map")
    assert ei.governance_files_at(after, repo) == frozenset()
    paths = ei.identity_at(after, repo).paths
    assert "tests/test_index.py" in paths and "tests/test_leak.py" in paths


def test_compare_fails_closed_on_an_unknown_commit(toy):
    repo, base = toy
    cmp = ei.compare(base, "f" * 40, repo)
    assert not cmp.matches and cmp.error
    assert "could not be measured" in cmp.detail


def test_the_real_repository_identity_covers_src_and_excludes_ops_documents():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    ident = ei.identity_at(head)
    assert len(ident.entries) > 100, "premise: the real governed set is large"
    assert "src/itsf/guards.py" in ident.paths          # committed at every HEAD
    assert "tests/conftest.py" in ident.paths
    assert not any(p.startswith("ops/") and p.endswith(".md") for p in ident.paths)
    assert not any(p.startswith(".git") for p in ident.paths)


# ---------------------------------------------------------------------------
# environment pin
# ---------------------------------------------------------------------------

def _lock(tmp_path, text="pkg-one==1.2.3\nPkg_Two==0.1\n"):
    lock = tmp_path / "requirements.lock.txt"
    lock.write_text(text, encoding="utf-8")
    pyv = tmp_path / ".python-version"
    pyv.write_text("3.13\n", encoding="utf-8")
    return lock, pyv


def _versions(mapping):
    def version_of(name):
        return mapping.get(name, mapping.get(ei._normalise(name)))
    return version_of


def test_a_matching_environment_is_pinned(tmp_path):
    lock, pyv = _lock(tmp_path)
    rep = ei.measure_environment(
        lockfile=lock, python_version_file=pyv, environ={},
        version_of=_versions({"pkg-one": "1.2.3", "pkg-two": "0.1"}),
        running=(3, 13, 5))
    assert rep.pinned and rep.packages_checked == 2, rep.detail


def test_package_drift_is_reported_unpinned(tmp_path):
    lock, pyv = _lock(tmp_path)
    rep = ei.measure_environment(
        lockfile=lock, python_version_file=pyv, environ={},
        version_of=_versions({"pkg-one": "1.2.4", "pkg-two": "0.1"}),
        running=(3, 13, 5))
    assert not rep.pinned and "pkg-one" in rep.detail and "1.2.4" in rep.detail


def test_a_missing_locked_package_is_reported_unpinned(tmp_path):
    lock, pyv = _lock(tmp_path)
    rep = ei.measure_environment(
        lockfile=lock, python_version_file=pyv, environ={},
        version_of=_versions({"pkg-one": "1.2.3"}), running=(3, 13, 5))
    assert not rep.pinned and "Pkg_Two" in rep.detail


def test_an_interpreter_mismatch_is_reported_unpinned(tmp_path):
    lock, pyv = _lock(tmp_path)
    rep = ei.measure_environment(
        lockfile=lock, python_version_file=pyv, environ={},
        version_of=_versions({"pkg-one": "1.2.3", "pkg-two": "0.1"}),
        running=(3, 12, 1))
    assert not rep.pinned and "3.12" in rep.detail


@pytest.mark.parametrize("var", ei.HOSTILE_ENV_VARS)
def test_an_override_variable_is_reported_unpinned(tmp_path, var):
    lock, pyv = _lock(tmp_path)
    rep = ei.measure_environment(
        lockfile=lock, python_version_file=pyv, environ={var: "x"},
        version_of=_versions({"pkg-one": "1.2.3", "pkg-two": "0.1"}),
        running=(3, 13, 5))
    assert not rep.pinned and var in rep.detail


def test_an_empty_lockfile_is_unpinned_not_trivially_pinned(tmp_path):
    lock, pyv = _lock(tmp_path, "# nothing\n")
    rep = ei.measure_environment(lockfile=lock, python_version_file=pyv,
                                 environ={}, version_of=_versions({}),
                                 running=(3, 13, 5))
    assert not rep.pinned and "pins no package" in rep.detail


def test_both_production_context_builders_measure_the_pin_and_identity():
    """The gate refuses None; therefore production must never produce None.
    Both builders read the real registry through the boundary and ask git
    for HEAD -- exactly what the existing precheck tests already do."""
    from itsf.mc import day_strata_context as ctxmod
    from itsf.mc import supplement_precheck as pc

    ctx, _gaps = pc.assemble_precheck_context(utc_stamp="20260907T000000Z")
    assert ctx.environment_pinned is not None
    assert ctx.environment_detail
    built = ctxmod.build_precheck_context(supplement_id=ctx.supplement_id,
                                          utc_stamp="20260907T000000Z")
    assert built.environment_pinned is not None
    assert built.environment_detail
    # identity is None only when there is nothing to compare; when it is
    # measured it is a real comparison object
    for c in (ctx, built):
        assert c.execution_identity is None or hasattr(c.execution_identity,
                                                       "matches")


# ---------------------------------------------------------------------------
# the gate, on hand-built contexts
# ---------------------------------------------------------------------------

class _P2:
    def __init__(self, commit):
        self.actor = "Aaron"
        self.authorized_commit = commit
        self.output_root = r"C:\Users\Aaron\quant-data\itsf-runs"


class _Chain:
    def __init__(self, commit):
        self.live_authorizations = (_P2(commit),)
        self.problem = ""
        self.retired = False


def _ctx(**over):
    base = dict(supplement_id="MC-DS-S001", head_commit=HEAD40,
                registry_text="", runs_root=None, archive_root=None,
                frozen_hashes_ok=True, chain=_Chain(HEAD40),
                environment_pinned=True, environment_detail="pinned")
    base.update(over)
    return sr.GateContext(**base)


GATE = sr.GATES["authorized_commit_matches_head"]


def _refusal(ctx) -> str:
    with pytest.raises(sr.SupplementRunnerError) as ei_:
        GATE(ctx)
    return str(ei_.value)


def test_equal_commits_and_a_pinned_environment_pass():
    GATE(_ctx())


def test_differing_commits_with_no_measured_identity_refuse():
    msg = _refusal(_ctx(chain=_Chain(OTHER40)))
    assert "unmeasured" in msg


def test_differing_commits_with_a_differing_identity_refuse_and_name_the_path():
    cmp = ei.IdentityComparison(False, HEAD40, OTHER40, "h" * 64, "a" * 64,
                                ("src/itsf/s0/labels.py",))
    msg = _refusal(_ctx(chain=_Chain(OTHER40), execution_identity=cmp))
    assert "src/itsf/s0/labels.py" in msg


def test_differing_commits_with_an_equal_identity_pass():
    cmp = ei.IdentityComparison(True, HEAD40, OTHER40, "h" * 64, "h" * 64)
    GATE(_ctx(chain=_Chain(OTHER40), execution_identity=cmp))


def test_an_unmeasured_environment_pin_refuses_even_with_equal_commits():
    msg = _refusal(_ctx(environment_pinned=None, environment_detail=""))
    assert "not measured" in msg


def test_a_false_environment_pin_refuses_with_its_reason():
    msg = _refusal(_ctx(environment_pinned=False,
                        environment_detail="numpy: installed '2.4' != locked '2.5.0'"))
    assert "numpy" in msg


# ---------------------------------------------------------------------------
# the first-write seam
# ---------------------------------------------------------------------------

def _fake_git(head, porcelain, tiers_source='GOVERNANCE_FILES = ("test_ops_index_is_complete.py",)\n'):
    def fake(repo, *args):
        if args[:2] == ("rev-parse", "HEAD"):
            return head + "\n"
        if args[:2] == ("status", "--porcelain"):
            return porcelain
        if args[0] == "show":
            return tiers_source
        raise AssertionError(f"unexpected git call {args}")
    return fake


def test_seam_refuses_when_head_moved(monkeypatch):
    monkeypatch.setattr(ei, "_git", _fake_git(OTHER40, ""))
    with pytest.raises(ei.SeamRefused) as caught:
        ei.seam_recheck(HEAD40, environment=ei.EnvironmentReport(True, "ok"))
    assert caught.value.code == "seam_head_moved"


def test_seam_refuses_a_dirty_governed_path_and_ignores_ops(monkeypatch):
    monkeypatch.setattr(ei, "_git", _fake_git(HEAD40, " M ops/README.md\n"))
    ei.seam_recheck(HEAD40, environment=ei.EnvironmentReport(True, "ok"))
    monkeypatch.setattr(ei, "_git",
                        _fake_git(HEAD40, " M ops/README.md\n M src/itsf/s0/labels.py\n"))
    with pytest.raises(ei.SeamRefused) as caught:
        ei.seam_recheck(HEAD40, environment=ei.EnvironmentReport(True, "ok"))
    assert caught.value.code == "seam_governed_tree_dirty"
    assert "src/itsf/s0/labels.py" in caught.value.detail


def test_seam_ignores_a_dirty_tier_c_test_but_not_a_tier_a_test(monkeypatch):
    monkeypatch.setattr(ei, "_git",
                        _fake_git(HEAD40, " M tests/test_ops_index_is_complete.py\n"))
    ei.seam_recheck(HEAD40, environment=ei.EnvironmentReport(True, "ok"))
    monkeypatch.setattr(ei, "_git", _fake_git(HEAD40, " M tests/test_labels.py\n"))
    with pytest.raises(ei.SeamRefused):
        ei.seam_recheck(HEAD40, environment=ei.EnvironmentReport(True, "ok"))


def test_seam_refuses_an_unpinned_environment(monkeypatch):
    monkeypatch.setattr(ei, "_git", _fake_git(HEAD40, ""))
    with pytest.raises(ei.SeamRefused) as caught:
        ei.seam_recheck(HEAD40, environment=ei.EnvironmentReport(False, "PYTHONPATH set"))
    assert caught.value.code == "seam_environment_unpinned"


def test_the_runner_does_not_append_p3_when_the_seam_refuses(monkeypatch):
    from itsf.mc import registry_boundary as rb

    calls = []
    monkeypatch.setattr(rb, "append_run_started",
                        lambda *a, **k: calls.append((a, k)) or "row")
    monkeypatch.setattr(ei, "seam_recheck",
                        lambda *a, **k: (_ for _ in ()).throw(
                            ei.SeamRefused("seam_head_moved", "moved")))
    with pytest.raises(sr.SupplementRunNotAuthorized) as caught:
        sr._append_run_started_after_seam_recheck("MC-DS-S001", _ctx())
    assert "seam_head_moved" in str(caught.value)
    assert calls == [], "P3 must not be appended after a seam refusal"


def test_the_runner_appends_p3_only_after_the_seam_passes(monkeypatch):
    from itsf.mc import registry_boundary as rb

    calls = []
    monkeypatch.setattr(rb, "append_run_started",
                        lambda sid, **k: calls.append((sid, k)) or "row")
    monkeypatch.setattr(ei, "seam_recheck", lambda *a, **k: None)
    assert sr._append_run_started_after_seam_recheck("MC-DS-S001", _ctx()) == "row"
    assert calls and calls[0][1]["head_commit"] == HEAD40


# ---------------------------------------------------------------------------
# Condition A: the register, and the derived read-set
# ---------------------------------------------------------------------------

def test_the_register_covers_every_dependency_class_with_a_valid_mechanism():
    classes = {d.dependency_class for d in ei.DEPENDENCY_REGISTER}
    assert classes == set(ei.DEPENDENCY_CLASSES), sorted(set(ei.DEPENDENCY_CLASSES) - classes)
    for dep in ei.DEPENDENCY_REGISTER:
        assert dep.mechanism in ei.MECHANISMS
    semantic = [d for d in ei.DEPENDENCY_REGISTER if d.mechanism != "NOT_SEMANTIC"]
    assert len(semantic) >= 20, "premise: the register is not vacuous"


def test_every_plain_repository_path_in_the_register_exists():
    plain = [d.locator for d in ei.DEPENDENCY_REGISTER
             if "*" not in d.locator and ":" not in d.locator
             and " " not in d.locator
             and not d.locator.startswith("AUTHORIZED_JOB_DIR/")]
    assert len(plain) >= 10, "premise"
    missing = [p for p in plain if not (REPO / p).exists()]
    assert missing == [], missing


def test_covering_mechanism_answers_for_each_kind_of_path():
    gov = frozenset({"test_ops_index_is_complete.py"})
    assert ei.covering_mechanism("src/itsf/s0/labels.py", gov) == "GOVERNED_IDENTITY"
    assert ei.covering_mechanism("gate1/f10_event_calendar/f10_events.csv", gov) == "GOVERNED_IDENTITY"
    assert ei.covering_mechanism("tests/test_labels.py", gov) == "GOVERNED_IDENTITY"
    assert ei.covering_mechanism("tests/test_ops_index_is_complete.py", gov) is None
    assert ei.covering_mechanism("ops/SECOND_COPY_ATTESTED.flag", gov) == "EXISTENCE_FLAG_GATE"
    assert ei.covering_mechanism("ops/S0_T001_POST_RUN_ATTESTATION.md", gov) == "CODE_PINNED_HASH"
    assert ei.covering_mechanism("STUDY_0_PREREGISTRATION.md", gov) == "FROZEN_HASH"
    assert ei.covering_mechanism("ops/README.md", gov) is None
    assert ei.covering_mechanism("ops/DECISIONS.md", gov) is None


_OPENED: list = []
_ACTIVE: list = []


def _audit(event, args):
    if _ACTIVE and event == "open":
        target = args[0]
        if isinstance(target, (str, bytes, os.PathLike)):
            _OPENED.append(os.fspath(target))


sys.addaudithook(_audit)


def _repo_relative(paths):
    root = os.path.normcase(str(REPO.resolve()))
    out = set()
    for raw in paths:
        p = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        try:
            full = os.path.normcase(str(Path(p).resolve()))
        except OSError:
            continue
        if not full.startswith(root + os.sep):
            continue
        rel = Path(p).resolve().relative_to(REPO.resolve()).as_posix()
        if "__pycache__" in rel or rel.endswith(".pyc") or rel.startswith(".git/"):
            continue
        out.add(rel)
    return sorted(out)


def test_every_repository_path_production_opens_is_covered_by_a_mechanism(tmp_path):
    """The derived read-set. Instrumented: the precheck assembler (registry
    through the boundary, git, frozen hashes), the two calendar builders,
    and the full synthetic rehearsal. Fixture modules are imported BEFORE
    the window opens so the harness's own reads are not attributed to
    production."""
    sys.path.insert(0, str(REPO / "tests"))
    import test_day_strata_dryrun as fixtures            # noqa: F401
    from itsf.mc import production_inputs as pi
    from itsf.mc import supplement_precheck as pc

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    governance = ei.governance_files_at(head)

    _OPENED.clear()
    _ACTIVE.append(True)
    try:
        pc.assemble_precheck_context(utc_stamp="20260907T000000Z")
        pi.build_event_calendar()
        pi.build_roll_intervals()
        fixtures._rehearse(str(tmp_path / "scratch"))
    finally:
        _ACTIVE.clear()

    opened = _repo_relative(_OPENED)
    assert "gate1/f10_event_calendar/f10_events.csv" in opened, "premise: the hook saw the calendar read"
    assert "gate1/symbology/nq_v0_mapping.csv" in opened, "premise: the hook saw the roll mapping read"
    uncovered = [p for p in opened if ei.covering_mechanism(p, governance) is None]
    assert uncovered == [], (
        "production opened repository paths that no mechanism constrains; "
        "add each to execution_identity.DEPENDENCY_REGISTER with the "
        "mechanism that constrains it, or stop reading it:\n  "
        + "\n  ".join(uncovered))


# ---------------------------------------------------------------------------
# data identity: manifest pin, per-file sha256, condition.json (new at I1)
# ---------------------------------------------------------------------------

def _job_dir(tmp_path, condition_text='[{"date": "2026-08-04", "condition": "degraded"}]'):
    job = tmp_path / "job"
    job.mkdir()
    cond = job / "condition.json"
    cond.write_text(condition_text, encoding="utf-8")
    manifest = {"job_id": "synthetic", "files": [
        {"filename": "condition.json",
         "hash": "sha256:" + hashlib.sha256(cond.read_bytes()).hexdigest()},
    ]}
    (job / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return job


def test_condition_json_is_verified_against_the_manifest_before_it_is_read(tmp_path, monkeypatch):
    from itsf.data.manifests import ManifestError
    from itsf.mc import production_inputs as pi

    job = _job_dir(tmp_path)
    pin = hashlib.sha256((job / "manifest.json").read_bytes()).hexdigest()
    # the authorization is a closed one-path list; the fixture stands in for
    # it so the manifest pin and the per-file check are what is exercised
    monkeypatch.setattr(pi, "AUTHORIZED_JOB_DIR", job)
    monkeypatch.setattr(pi, "AUTHORIZED_MANIFEST_SHA256", pin)
    schedule = pi.build_session_schedule("2026-08-03", "2026-08-07", job_dir=job)
    assert schedule.vendor_degraded_dates == frozenset({"2026-08-04"})

    (job / "condition.json").write_text(
        '[{"date": "2026-08-04", "condition": "available"}]', encoding="utf-8")
    with pytest.raises(ManifestError):
        pi.build_session_schedule("2026-08-03", "2026-08-07", job_dir=job)


def test_a_replaced_manifest_is_refused_by_the_pin(tmp_path, monkeypatch):
    from itsf.mc import production_inputs as pi

    job = _job_dir(tmp_path)
    monkeypatch.setattr(pi, "AUTHORIZED_JOB_DIR", job)
    monkeypatch.setattr(pi, "AUTHORIZED_MANIFEST_SHA256", "0" * 64)
    with pytest.raises(PermissionError) as caught:
        pi.verify_authorized_job_dir(job)
    assert "manifest.json" in str(caught.value)


def test_a_job_dir_other_than_the_authorized_one_is_refused(tmp_path):
    from itsf.mc import production_inputs as pi

    with pytest.raises(PermissionError) as caught:
        pi.verify_authorized_job_dir(_job_dir(tmp_path))
    assert "not the authorized directory" in str(caught.value)


def test_a_tampered_data_file_is_refused_by_its_manifest_entry(tmp_path):
    from itsf.data import manifests

    job = _job_dir(tmp_path)
    manifest = manifests.load_manifest(job)
    manifests.verify_file_against_manifest(job / "condition.json", manifest)
    (job / "condition.json").write_bytes(b"[]")
    with pytest.raises(manifests.ManifestError):
        manifests.verify_file_against_manifest(job / "condition.json", manifest)
