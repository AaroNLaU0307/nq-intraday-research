"""The three residuals measured while preparing final-certification transport.

None of these came from a reviewer. They were found by mechanically answering
the four directions Aaron named for the final certification, and three of the
answers were NO. This file is the settling test for the repair.

R1  an allowed executable `.pth` was checked AFTER Python startup. A `.pth`
    `import` line runs during site initialisation, before any project line, so
    checking its bytes later cannot constrain what already executed.
R2  a startup hook could import a governed module, mutate it, delete the child
    entries from `sys.modules`, and leave exactly the permitted bootstrap
    closure -- after which the attestation passed. Reproduced.
R3  `scripts/s0_real_run.py` referenced neither `seam_recheck` nor
    `assert_governed_launch` nor `execution_identity`. The trusted-launch proof
    covered one path (the P3 seam) while eight production entries reached real
    bytes without it.

R1 AND R2 ARE ONE HOLE, AND IT IS TEMPORAL. No strengthening of a later check
reaches either. What closes both is `-S`: under it no `.pth` line executes,
`site` is never imported, and neither automatic startup module is imported, so
there is no hook to hide anything and nothing for a census to be fooled about.

THE MEASUREMENT THAT MADE THAT AVAILABLE CORRECTS AN EARLIER ONE. Round two
recorded that `-S` "cannot be used" because `import pandas` fails under it.
True, and the conclusion was wrong: `-S` alone fails, `-S` plus the site
directories on `sys.path` does not. That is why the boundary is two processes.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import marshal
import os
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf import execution_identity as ei                      # noqa: E402
from itsf import guards                                        # noqa: E402
from itsf.mc import registry_boundary as rb                    # noqa: E402
from itsf.mc import owner_control as oc                        # noqa: E402

LAUNCHER = REPO / "scripts" / "run_governed.py"
C40 = "a" * 40
UTC = "2026-09-07T00:00:00+00:00"


def _run(args, env=None, cwd=None):
    return subprocess.run([sys.executable, *args], capture_output=True,
                          text=True, env=env, cwd=str(cwd or REPO))


# ===========================================================================
# 1 — the actual startup order, measured rather than assumed
# ===========================================================================

def test_the_startup_order_is_what_the_repair_assumes():
    """THE PREMISE OF THE WHOLE REPAIR, so it is measured and not asserted.

    Python executes site initialisation -- and with it every `.pth` `import`
    line and `sitecustomize` -- BEFORE the first line of project code. If that
    were false, an in-process check could constrain a startup surface and none
    of this would be needed.
    """
    d = Path(tempfile.mkdtemp())
    marker = d / "ran.txt"
    (d / "hook_payload.py").write_bytes(
        b"from pathlib import Path\n"
        b"Path(r'%s').write_text('startup', encoding='utf-8')\n"
        % str(marker).encode())
    (d / "probe.pth").write_bytes(b"import hook_payload\n")

    # site.addsitedir is the same code path startup uses for a site directory.
    r = _run(["-c",
              "import site, sys;"
              "sys.path.insert(0, r'%s');"
              "site.addsitedir(r'%s');"
              "print('project code runs here')" % (d, d)])
    assert r.returncode == 0, r.stderr[-800:]
    assert marker.exists(), "the .pth did not execute at all; premise unproven"
    assert marker.read_text(encoding="utf-8") == "startup"
    # and the ordering: the hook's write happened before the project line's
    # output could be produced, which is the only ordering that matters here.
    assert "project code runs here" in r.stdout


def test_under_dash_S_no_startup_surface_executes_at_all():
    """THE EARLIEST ENFORCEMENT POINT, and it is not inside the interpreter.

    `-S` is a launch flag, so the decision is made by whoever spawns the
    process. That is why the control lives in a launcher and not in a module.
    """
    r = _run(["-S", "-B", "-c",
              "import sys;"
              "print('no_site', sys.flags.no_site);"
              "print('site_imported', 'site' in sys.modules);"
              "print('pth_ran', 'pip_system_certs.bootstrap' in sys.modules)"])
    assert r.returncode == 0, r.stderr[-500:]
    out = dict(line.split() for line in r.stdout.strip().splitlines())
    assert out == {"no_site": "1", "site_imported": "False",
                   "pth_ran": "False"}, out


def test_the_pinned_environment_still_imports_under_dash_S():
    """THE MEASUREMENT THAT CORRECTED ROUND TWO. Prevention is only available
    because this holds; if it ever stops holding, the mechanism must change
    rather than the claim."""
    import site
    dirs = [p for p in dict.fromkeys(
        list(site.getsitepackages()) + [site.getusersitepackages()])
        if Path(p).is_dir()]
    mods = ["pandas", "numpy", "scipy", "pyarrow", "databento", "zstandard",
            "exchange_calendars", "pandas_market_calendars"]
    code = ("import sys\n"
            "sys.path[:0] = %r\n"
            "bad = []\n"
            "for m in %r:\n"
            "    try:\n"
            "        __import__(m)\n"
            "    except Exception as e:\n"
            "        bad.append(m)\n"
            "print('FAILED', bad)\n"
            "print('pth_ran', 'pip_system_certs.bootstrap' in sys.modules)\n"
            % (dirs, mods))
    r = _run(["-S", "-B", "-c", code])
    assert r.returncode == 0, r.stderr[-900:]
    assert "FAILED []" in r.stdout, r.stdout
    assert "pth_ran False" in r.stdout


# ===========================================================================
# 2 — R1: the forged cache, and the evidence removal that defeated the census
# ===========================================================================

def test_R1_the_forged_cache_attack_still_defeats_a_CENSUS():
    """Reproduced AGAIN, so the record is honest about what did not change:
    the census is still foolable. That is why it is no longer the proof."""
    d = Path(tempfile.mkdtemp())
    pkg = d / "toy"
    pkg.mkdir()
    (pkg / "__init__.py").write_bytes(b"")
    src = pkg / "semantics.py"
    src.write_bytes(b"def rth_close_minute():\n    return 960\n")
    py_compile.compile(str(src), doraise=True)
    cache = Path(importlib.util.cache_from_source(str(src)))
    cache.write_bytes(cache.read_bytes()[:16] + marshal.dumps(
        compile("def rth_close_minute():\n    return 1\n", str(src), "exec")))

    r = _run(["-c", "import sys; sys.path.insert(0, r'%s');"
                    "import toy.semantics as s; print(s.rth_close_minute())"
                    % d])
    assert r.stdout.strip() == "1", "the forged cache did not execute"
    cache.unlink()                                    # step 4: remove evidence
    after = ei.bytecode_report(dont_write=True, prefix="/private",
                               governed_sources=[src])
    assert after.from_source is True, (
        "the census now catches this; if that is real the mechanism could be "
        "simpler, so it must be re-examined rather than left asserted")


def test_R1_a_process_where_a_startup_hook_could_have_run_is_REFUSED():
    """THE CLOSURE, and it is a precondition rather than a search.

    The forged-cache attack needs a moment at which something can run before
    the governed imports. Under `-S` there is no such moment, and a process
    that did not get `-S` is refused outright -- so the attack's precondition
    and a valid governed launch cannot coexist. Nothing has to be detected.
    """
    class _Flags:
        no_site = 0
        dont_write_bytecode = 1

    empty = Path(tempfile.mkdtemp())
    with pytest.raises(ei.SeamRefused) as caught:
        ei.assert_governed_launch(
            flags=_Flags(), prefix=str(empty),
            modules={n: object() for n in ei.BOOTSTRAP_IMPORT_CLOSURE})
    assert caught.value.args[0].startswith("launch_site_processing_enabled")


def test_R1_the_no_site_flag_cannot_be_forged_in_process():
    """The fact is only worth anything because it is read-only."""
    with pytest.raises((AttributeError, TypeError)):
        sys.flags.no_site = 1


# ===========================================================================
# 3 — R2: the hidden governed import, and why it is now unreachable
# ===========================================================================

def test_R2_the_hidden_import_attack_reproduces_against_a_sys_modules_census():
    """THE TRANSPORT-DISCOVERED ATTACK, reproduced exactly.

    A hook imports a governed module, mutates it, then deletes the child
    entries. What remains is precisely the permitted bootstrap closure, so a
    census of `sys.modules` reports nothing wrong -- while the mutation is
    still in effect on the module object any later import will hand back.
    """
    code = (
        "import sys\n"
        "sys.path.insert(0, r'%s')\n"
        "import itsf.mc.owner_control as oc\n"
        "oc.OWNER_ACTOR = 'attacker'\n"          # a visible semantic mutation
        "for m in [m for m in sys.modules if m.startswith('itsf.mc')]:\n"
        "    del sys.modules[m]\n"
        "left = sorted(m for m in sys.modules if m.startswith('itsf'))\n"
        "print('LEFT', left)\n"
        % (REPO / "src"))
    r = _run(["-c", code])
    assert r.returncode == 0, r.stderr[-600:]
    left = json.loads(r.stdout.split("LEFT", 1)[1].strip().replace("'", '"'))
    assert set(left) <= set(ei.BOOTSTRAP_IMPORT_CLOSURE), (
        "the cleanup no longer hides the import; re-examine the mechanism")


def test_R2_the_attack_cannot_be_converted_into_a_valid_governed_launch():
    """THE CLOSURE, and deliberately NOT another `sys.modules` check.

    The hook needs site initialisation to run. Under `-S` it does not, and a
    process without `-S` cannot attest at all -- proven by the R1 case above,
    which is the same single fact. So the census that this attack defeats is
    no longer what the launch rests on.
    """
    src = (REPO / "src" / "itsf" / "execution_identity.py").read_text(
        encoding="utf-8")
    body = src[src.index("def assert_governed_launch"):]
    body = body[:body.index("\ndef ")]
    tree = ast.parse(ast.unparse(ast.parse(body)))
    code_only = ast.unparse(tree)
    assert "no_site" in code_only, (
        "the -S requirement is not in the attestation's CODE; a docstring "
        "claiming it would be exactly the defect this project keeps finding")
    # and the ordering: the -S refusal must come before the sys.modules census,
    # or a hook-bearing process would be judged on the census it can defeat.
    assert code_only.index("no_site") < code_only.index("premature")


# ===========================================================================
# 4 — F02: which startup surfaces exist, and how their identity is bound
# ===========================================================================

def test_F02_the_two_kinds_of_pth_line_are_named_not_implied():
    assert (ei.classify_startup_artifact("import x\n")
            == ei.EXECUTABLE_STARTUP_SURFACE)
    assert (ei.classify_startup_artifact("/some/dir\n")
            == ei.NON_EXECUTABLE_PATH_DECLARATION)
    assert (ei.classify_startup_artifact("# comment\n/dir\n")
            == ei.NON_EXECUTABLE_PATH_DECLARATION)


def test_F02_every_executable_surface_on_this_machine_is_bound_by_bytes():
    """The pin is a mapping name -> sha256, and it matches reality. A wrong
    digest would refuse every governed launch, so it fails here instead."""
    live = ei.startup_report()
    assert live.pinned is True, live.detail
    assert set(live.executable_pth) <= set(ei.EXPECTED_EXECUTABLE_PTH)
    for name, want in ei.EXPECTED_EXECUTABLE_PTH.items():
        assert len(want) == 64 and want == want.lower()
    assert live.executable_pth, (
        "no executable startup surface was found at all; the pin would then "
        "be vacuous and this test would prove nothing")


def test_F02_the_parent_REFUSES_TO_LAUNCH_on_changed_permitted_bytes():
    """The parent-side half: a permitted artifact whose bytes changed is a
    refusal to start the child, not merely something the child never runs.
    Tampering is reported rather than tolerated."""
    d = Path(tempfile.mkdtemp())
    name = sorted(ei.EXPECTED_EXECUTABLE_PTH)[0]
    (d / name).write_bytes(b"import hook_payload\n")
    report = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert report.pinned is False
    assert "changed content" in report.detail
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "REFUSING TO LAUNCH" in launcher, (
        "the launcher does not refuse on an untrusted startup surface")


def test_F02_sitecustomize_and_usercustomize_are_absent_and_would_be_refused():
    assert ei.FORBIDDEN_STARTUP_MODULES == ("sitecustomize", "usercustomize")
    for name in ei.FORBIDDEN_STARTUP_MODULES:
        assert importlib.util.find_spec(name) is None, (
            "%s exists on this machine and runs at startup in every "
            "non--S process" % name)
    bad = ei.startup_report(sitedirs=[], find_spec=lambda n: object())
    assert bad.pinned is False and "sitecustomize" in bad.detail
    # and under -S neither is imported at all, which is the actual protection
    r = _run(["-S", "-B", "-c",
              "import sys; print(sorted(m for m in sys.modules "
              "if m in ('sitecustomize', 'usercustomize')))"])
    assert r.stdout.strip() == "[]", r.stdout


# ===========================================================================
# 5 — the launcher: two processes, and the flags each one gets
# ===========================================================================

def test_the_launcher_hardens_the_parent_and_gives_the_child_dash_S_not_dash_E():
    src = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef)}
    parent = ast.unparse(funcs["run_parent"])
    reexec = ast.unparse(funcs["_reexec_parent"])
    assert "'-S'" in parent and "'-B'" in parent, (
        "the child is not spawned with -S and -B")
    assert "'-E'" not in parent, (
        "the child is spawned with -E, which makes the interpreter ignore "
        "PYTHONPYCACHEPREFIX and reopens the repository's own __pycache__")
    assert "'-E'" in reexec, "the parent is not hardened with -E"
    assert "'-S'" in reexec, "the parent is not hardened with -S"


def test_the_launcher_attests_end_to_end_under_dash_S():
    r = _run([str(LAUNCHER), "itsf.mc.owner_control"])
    assert r.returncode == 0, r.stderr[-1500:]
    assert "startup surfaces trusted" in r.stderr
    assert "-S set (read-only" in r.stderr
    assert "holds 0 caches" in r.stderr


def test_the_private_pycache_prefix_is_fresh_and_unpredictable():
    """A fixed path could be pre-planted. Two runs must not share one."""
    seen = set()
    for _ in range(2):
        r = _run([str(LAUNCHER), "itsf.mc.owner_control"])
        assert r.returncode == 0, r.stderr[-600:]
        line = [ln for ln in r.stderr.splitlines() if "pycache_prefix" in ln][0]
        seen.add(line.split("pycache_prefix", 1)[1].split(" holds")[0].strip())
    assert len(seen) == 2, f"the prefix was reused across runs: {seen}"


# ===========================================================================
# 6 — R3: sanctioned real-run entry coverage
# ===========================================================================

#: Every `scripts/*.py` carrying a `__main__` entry, classified. MEASURED then
#: registered: a new script appearing here unclassified fails the test below,
#: which is the only way this inventory stays true.
#:
#: SANCTIONED_REAL_RUN_ENTRY = reaches real market bytes and calls the real-run
#: gate with the PRODUCTION attestation paths, so the trusted-launch
#: requirement applies to it.
ENTRY_CLASSIFICATION = {
    "scripts/s0_real_run.py": "SANCTIONED_REAL_RUN_ENTRY",
    "scripts/run_data_qa.py": "SANCTIONED_REAL_RUN_ENTRY",
    "scripts/qa_addendum_a1.py": "SANCTIONED_REAL_RUN_ENTRY",
    "scripts/qa_addendum_a2.py": "SANCTIONED_REAL_RUN_ENTRY",
    "scripts/s0_input_preflight.py": "SANCTIONED_REAL_RUN_ENTRY",
    # the launcher itself: it starts governed runs and performs none
    "scripts/run_governed.py": "INTERNAL_ONLY",
    # prose renderers and builders: the real-data names in them are docstrings
    "scripts/render_qa_addendum.py": "NON_REAL",
    "scripts/mc_ds_rehearsal.py": "NON_REAL",
    "scripts/archive_code_6_block_builder.py": "NON_REAL",
    "scripts/build_verifier_dir.py": "NON_REAL",
    "scripts/fetch_symbology_d5.py": "NON_REAL",
    "scripts/final_candidate_scans.py": "NON_REAL",
    "scripts/mc_cost_probe.py": "NON_REAL",
    "scripts/physical_copy_verify.py": "NON_REAL",
}

#: Production functions that ARE the real-run entry for their lifecycle.
SANCTIONED_MODULE_ENTRIES = (
    "src/itsf/mc/supplement_runner.py",
    "src/itsf/mc/consumer.py",
    "src/itsf/mc/real_input.py",
)


def test_R3_the_entry_inventory_is_complete_and_classified():
    """An entry nobody classified is an entry nobody gated."""
    found = {}
    for path in sorted((REPO / "scripts").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "__main__" in text:
            found[path.relative_to(REPO).as_posix()] = True
    unclassified = sorted(set(found) - set(ENTRY_CLASSIFICATION))
    assert not unclassified, (
        "these scripts have a __main__ entry and no classification; classify "
        "each SANCTIONED_REAL_RUN_ENTRY or NON_REAL/INTERNAL_ONLY:\n  "
        + "\n  ".join(unclassified))
    gone = sorted(set(ENTRY_CLASSIFICATION) - set(found))
    assert not gone, f"classified scripts that no longer exist: {gone}"
    assert sum(v == "SANCTIONED_REAL_RUN_ENTRY"
               for v in ENTRY_CLASSIFICATION.values()) >= 5


def test_R3_every_sanctioned_entry_is_bound_to_the_real_run_gate():
    """The binding, statically: each sanctioned entry reaches
    `assert_real_run_allowed` with the production defaults, directly or through
    a default-flag loader. That gate is where the launch requirement lives, so
    binding to it IS binding to the trusted launch."""
    unbound = []
    for rel, kind in sorted(ENTRY_CLASSIFICATION.items()):
        if kind != "SANCTIONED_REAL_RUN_ENTRY":
            continue
        text = (REPO / rel).read_text(encoding="utf-8")
        direct = "assert_real_run_allowed()" in text
        loader = "DevelopmentSignalLoader(" in text
        if not (direct or loader):
            unbound.append(rel)
    assert unbound == [], (
        "these sanctioned real-run entries reach neither the gate with "
        "production defaults nor a default-flag loader:\n  "
        + "\n  ".join(unbound))


def test_R3_the_gate_refuses_a_real_run_outside_the_trusted_launch():
    """The behaviour, dynamically. This is the single requirement that covers
    every entry in the inventory above."""
    with pytest.raises(guards.RunBlockedError) as caught:
        guards.assert_real_run_allowed()
    assert "trusted launch boundary" in str(caught.value)
    assert guards.G9_FLAG.exists() and guards.SECOND_COPY_FLAG.exists(), (
        "the refusal above must come from the LAUNCH, not from a missing "
        "attestation flag, or this test proves the wrong thing")


def test_R3_the_gate_passes_when_the_launch_is_attested():
    """A gate that refuses everything is not a gate."""
    guards.assert_real_run_allowed(
        launch=ei.LaunchAttestation("/injected", 0, "injected", True))


@pytest.mark.parametrize("rel", [
    "scripts/run_data_qa.py",
    "scripts/qa_addendum_a1.py",
    "scripts/qa_addendum_a2.py",
])
def test_R3_direct_invocation_of_a_sanctioned_entry_fails_closed(rel):
    """DIRECT-ENTRY BYPASS, executed. Each of these calls the gate as the
    first statement of its main, so running it directly reaches the refusal
    and nothing consequential.

    `scripts/s0_real_run.py` is deliberately NOT executed here: running a real
    S0 entry is the very act under prevention, and its gate is a `GateCheck`
    that converts this refusal into a failed gate. Its binding is proven
    statically above and the gate's behaviour dynamically in the case before.
    """
    r = _run([str(REPO / rel)])
    assert r.returncode != 0, (
        f"{rel} exited 0 when launched directly:\n{r.stdout[-800:]}")
    combined = r.stdout + r.stderr
    assert ("trusted launch boundary" in combined
            or "RunBlockedError" in combined), combined[-1200:]


def test_R3_a_sanctioned_entry_is_reachable_through_the_launcher():
    """The other direction: the boundary must not make real runs impossible,
    only unattested ones. The gate itself is driven through the launcher."""
    r = _run([str(LAUNCHER), "itsf.guards:assert_real_run_allowed"])
    assert r.returncode == 0, r.stderr[-1500:]
    assert "-S set (read-only" in r.stderr


# ===========================================================================
# 7 — F06: the shared primitive reaches the physical registry write
# ===========================================================================

def test_F06_all_three_supported_writers_reach_the_same_physical_write():
    """DYNAMIC, not just AST. Every supported writer is driven for real and the
    one physical write is counted, so a second write path added later shows up
    here rather than in a race nobody reproduces.

    NO GIT-COMMIT REQUIREMENT IS ADDED. The registry is a separate repository
    and nothing in the append path commits it; the invariant that matters is
    ordering and durable bytes at the physical write, which is what is asserted.
    """
    import test_qros_cf_astra_repairs as R1

    path = Path(tempfile.mkdtemp()) / "TRIAL_REGISTRY.md"
    sid = R1._two_row_ledger(path)

    seen = []
    real = rb._compare_and_append

    def counting(target, decided, addition):
        seen.append(Path(target).name)
        return real(target, decided, addition)

    rb._compare_and_append = counting
    try:
        rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="one",
                             head_commit=C40, utc_stamp=UTC, path=path)
        hold_seq = int(path.read_text(encoding="utf-8").strip()
                       .splitlines()[-1].split("|")[1].strip())
        rb.append_owner_release(scope=oc.GLOBAL_SCOPE, reason="two",
                                head_commit=C40, utc_stamp=UTC,
                                releases_event_sequence=hold_seq, path=path)
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    finally:
        rb._compare_and_append = real

    assert len(seen) == 3, (
        "one of the three supported writers did not go through the shared "
        f"serialized primitive: {seen}")
    text = path.read_text(encoding="utf-8")
    assert "OWNER_HOLD" in text and "OWNER_RELEASE" in text
    assert "SUPPLEMENT_RUN_STARTED" in text


def test_F06_the_physical_write_is_inside_the_lock():
    """Ordering and durable bytes: the write happens while the lock is held,
    so two appends cannot interleave between the equality check and the write."""
    src = (REPO / "src" / "itsf" / "mc" / "registry_boundary.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_compare_and_append")
    withs = [n for n in ast.walk(fn) if isinstance(n, ast.With)]
    assert withs, "the compare-and-swap no longer takes a lock"
    inside = ast.unparse(withs[0])
    assert "write_bytes" in inside, "the physical write left the lock"
    assert "read_bytes" in inside, "the equality re-read left the lock"


def test_F06_no_git_commit_requirement_was_added():
    """Aaron's instruction, asserted so a later reader does not add one by
    tidiness. The scientific invariant is ordering and durable bytes."""
    src = (REPO / "src" / "itsf" / "mc" / "registry_boundary.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    calls = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert not [c for c in calls if "commit" in c and "subprocess" in c], (
        "a git commit was introduced into the registry append path")


# ===========================================================================
# 8 — F03 / F04 / F05 preservation, since shared files were touched
# ===========================================================================

def test_F03_PRESERVED_the_official_manifest_is_still_the_sole_authority(
        tmp_path):
    from itsf.data import manifests as M

    d = tmp_path / "job"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({"job_id": "j", "files": [
        {"filename": "official.dbn.zst", "hash": "sha256:" + "a" * 64}]}),
        encoding="utf-8")
    (d / "_local_manifest.json").write_text(json.dumps({"files": {
        "replacement.dbn.zst": {"sha256": "b" * 64}}}), encoding="utf-8")
    with pytest.raises(M.ManifestError) as caught:
        M.load_manifest(d)
    assert "never an override" in str(caught.value)


def test_F04_PRESERVED_verified_bytes_are_the_bytes_consumed(tmp_path):
    from itsf.data import manifests as M

    good = b'{"status": "available"}'
    target = tmp_path / "condition.json"
    target.write_bytes(good)
    manifest = {"files": {"condition.json": {
        "sha256": hashlib.sha256(good).hexdigest()}}}
    assert M.read_verified_bytes(target, manifest) == good
    target.write_bytes(b'{"status": "degraded"}')
    with pytest.raises(M.ManifestError):
        M.read_verified_bytes(target, manifest)


def test_F05_PRESERVED_a_non_canonical_owner_scope_still_fails_closed():
    import test_qros_cf_astra_repairs as R1

    row = ("| 90 | %s | OWNER_HOLD | %s | Aaron | [MC-DS-S004-] reason: stop |"
           % (UTC, C40))
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(R1.LIVE_REGISTRY + row + "\n")
    assert caught.value.code == "owner_control_scope_unrecognized"


def test_nothing_here_wrote_to_the_real_registry():
    import test_qros_cf_astra_repairs as R1

    assert (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(
        encoding="utf-8") == R1.LIVE_REGISTRY
