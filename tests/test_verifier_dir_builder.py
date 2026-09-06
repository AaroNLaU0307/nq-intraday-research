"""T-F03: the verifier directory is two-phase, and the sentinel proves it.

QROS-CF v2 §2.8 (DEC-0006 I5; converged F03). Astra's point was that an
allowlist governs LOCATION, not CONTENT: a producer's sealed output can
carry the outcome, so "allowlisted" is not "safe to read before freeze".
The builder answers that structurally -- the post-freeze comparands do not
exist in the directory until the verifier's own result is frozen and
hashed. This file plants a sentinel in a synthetic "sealed output" and
checks it is absent from the directory through the whole pre-freeze phase.

Everything is synthetic and lives under tmp_path; the toy git repository
exports code the same way the real builder does (`git show`).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SENTINEL = "SENTINEL_OUTCOME_9f3a_DO_NOT_LEAK"


def _builder():
    script = REPO / "scripts" / "build_verifier_dir.py"
    spec = importlib.util.spec_from_file_location("build_verifier_dir", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(repo, *args):
    out = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t",
                          "-c", "user.email=t@t", *args],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


@pytest.fixture
def world(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "replay.py").write_text("def replay():\n    return 1\n",
                                                    encoding="utf-8")
    (repo / "ops").mkdir()
    (repo / "ops" / "SECRET.md").write_text("ops document\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    commit = _git(repo, "rev-parse", "HEAD")
    # a later worktree edit that must NOT be exported (export is at the commit)
    (repo / "src" / "pkg" / "replay.py").write_text("def replay():\n    return 2\n",
                                                    encoding="utf-8")

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "inputs.json").write_text('{"days": [1, 2, 3]}', encoding="utf-8")
    (evidence / "sealed_output.json").write_text(
        json.dumps({"statistic": 0.42, "note": SENTINEL}), encoding="utf-8")
    brief = tmp_path / "BRIEF.md"
    brief.write_text("# brief\nrecompute the statistic from inputs.json\n",
                     encoding="utf-8")
    out_root = tmp_path / "review"
    out_root.mkdir()
    spec = {
        "run_id": "SYN-R001",
        "verifier_label": "claim-blind-verifier",
        "blindness": "CLAIM_BLIND",
        "framework_commit": commit,
        "out_root": str(out_root),
        "brief": str(brief),
        "pre_freeze": {"files": [{"src": str(evidence / "inputs.json"),
                                  "dst": "inputs/inputs.json"}],
                       "code_paths": ["src/pkg/replay.py"]},
        "post_freeze": {"files": [{"src": str(evidence / "sealed_output.json"),
                                   "dst": "producer/sealed_output.json"}]},
    }
    spec_path = tmp_path / "SPEC.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return dict(repo=repo, commit=commit, evidence=evidence, out_root=out_root,
                spec=spec, spec_path=spec_path, tmp=tmp_path)


def _contains_sentinel(root: Path) -> list:
    hits = []
    for p in root.rglob("*"):
        if p.is_file() and SENTINEL.encode() in p.read_bytes():
            hits.append(p.relative_to(root).as_posix())
    return hits


def test_pre_freeze_holds_only_the_allowlist_and_never_the_sentinel(world):
    b = _builder()
    spec = b.load_spec(world["spec_path"])
    target = b.build_pre_freeze(spec, repo=world["repo"], date="2026-09-07")
    assert target.is_dir() and (target / "pre_freeze").is_dir()
    assert not (target / "post_freeze").exists()
    assert _contains_sentinel(target) == [], "the comparand leaked before freeze"
    inv = (target / "ALLOWLIST.sha256").read_text(encoding="utf-8").splitlines()
    listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in inv}
    assert set(listed) == {"pre_freeze/inputs/inputs.json",
                           "pre_freeze/code/src/pkg/replay.py",
                           "pre_freeze/BRIEF.md"}
    for rel, sha in listed.items():
        assert hashlib.sha256((target / rel).read_bytes()).hexdigest() == sha
    # the code is the COMMITTED bytes, not the edited worktree
    exported = (target / "pre_freeze" / "code" / "src" / "pkg" / "replay.py").read_text()
    assert "return 1" in exported and "return 2" not in exported
    assert (target / "README_VERIFIER.md").is_file()
    assert json.loads((target / "SPEC.json").read_text())["run_id"] == "SYN-R001"


def test_post_freeze_is_refused_until_a_matching_marker_exists(world):
    b = _builder()
    spec = b.load_spec(world["spec_path"])
    target = b.build_pre_freeze(spec, repo=world["repo"], date="2026-09-07")
    with pytest.raises(b.SpecRefused) as caught:
        b.build_post_freeze(spec, repo=world["repo"], date="2026-09-07")
    assert "FREEZE_MARKER" in str(caught.value)
    assert _contains_sentinel(target) == []

    result = target / "pre_freeze" / "my_result.json"
    result.write_text('{"statistic": 0.42}', encoding="utf-8")
    marker = target / "pre_freeze" / "FREEZE_MARKER.json"
    marker.write_text(json.dumps({"frozen_result": "my_result.json",
                                  "sha256": "0" * 64}), encoding="utf-8")
    with pytest.raises(b.SpecRefused) as caught:
        b.build_post_freeze(spec, repo=world["repo"], date="2026-09-07")
    assert "not frozen" in str(caught.value)
    assert _contains_sentinel(target) == []

    marker.write_text(json.dumps({
        "frozen_result": "my_result.json",
        "sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
        "frozen_at_utc": "2026-09-07T00:00:00Z"}), encoding="utf-8")
    b.build_post_freeze(spec, repo=world["repo"], date="2026-09-07")
    hits = _contains_sentinel(target)
    assert hits == ["post_freeze/producer/sealed_output.json"], hits
    inv = (target / "POST_FREEZE.sha256").read_text(encoding="utf-8")
    assert "post_freeze/producer/sealed_output.json" in inv

    with pytest.raises(b.SpecRefused):
        b.build_post_freeze(spec, repo=world["repo"], date="2026-09-07")


def test_a_directory_is_built_fresh_never_reused(world):
    b = _builder()
    spec = b.load_spec(world["spec_path"])
    b.build_pre_freeze(spec, repo=world["repo"], date="2026-09-07")
    with pytest.raises(b.SpecRefused) as caught:
        b.build_pre_freeze(spec, repo=world["repo"], date="2026-09-07")
    assert "already exists" in str(caught.value)


@pytest.mark.parametrize("mutate,fragment", [
    (lambda s, w: s["pre_freeze"]["files"].append(
        {"src": str(w["repo"] / "ops" / "SECRET.md"), "dst": "x.md"}), "ops/"),
    (lambda s, w: s["pre_freeze"]["files"].append(
        {"src": r"C:\Users\Aaron\quant-data\itsf-registry\ops\ANY_FILE.md",
         "dst": "reg.md"}), "forbidden"),
    (lambda s, w: s["pre_freeze"]["code_paths"].append("ops/README.md"), "exportable"),
    (lambda s, w: s["post_freeze"]["files"].append(
        {"src": str(w["evidence"] / "inputs.json"), "dst": "dup.json"}), "BOTH"),
    (lambda s, w: s["pre_freeze"]["files"].append(
        {"src": str(w["evidence"] / "inputs.json"), "dst": "../escape.json"}), ".."),
    (lambda s, w: s.__setitem__("blindness", "SOMEWHAT_BLIND"), "blindness"),
    (lambda s, w: s.__setitem__("framework_commit", "abc"), "40-hex"),
])
def test_a_spec_that_could_leak_is_refused_before_anything_is_written(world, mutate, fragment):
    b = _builder()
    spec = json.loads(world["spec_path"].read_text())
    mutate(spec, world)
    world["spec_path"].write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(b.SpecRefused) as caught:
        loaded = b.load_spec(world["spec_path"])
        b.build_pre_freeze(loaded, repo=world["repo"], date="2026-09-07")
    assert fragment in str(caught.value)
    assert list(world["out_root"].iterdir()) == [], "a refused spec wrote nothing"


def test_the_cli_reports_refusals_with_exit_2_and_writes_nothing(world):
    b = _builder()
    spec = json.loads(world["spec_path"].read_text())
    spec["framework_commit"] = "zz"
    world["spec_path"].write_text(json.dumps(spec), encoding="utf-8")
    assert b.main(["--spec", str(world["spec_path"]), "--phase", "pre-freeze"]) == 2
    assert list(world["out_root"].iterdir()) == []


def test_dry_run_prints_the_plan_and_writes_nothing(world, capsys):
    b = _builder()
    spec = b.load_spec(world["spec_path"])
    b.build_pre_freeze(spec, repo=world["repo"], date="2026-09-07", dry_run=True)
    out = capsys.readouterr().out
    assert "inputs.json" in out and "replay.py" in out
    assert list(world["out_root"].iterdir()) == []
