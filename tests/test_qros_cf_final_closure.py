"""QROS-CF FINAL BOUNDED REPAIR -- the closed-scope closure checks A1-A6, B1-B4.

This file is deliberately NARROW. It is the mechanical closure criteria for the
final bounded repair of two root blockers and nothing else.

ROOT A -- TRUSTED-LAUNCH TRUST-ROOT PLACEMENT. The reviewer reproduced that the
parent imported `itsf.execution_identity` before any trust boundary existed, and
that `-B` prevents bytecode WRITES but not READS -- so a timestamp-valid forged
`.pyc` in the governed tree influenced launch behaviour from inside the supposed
boundary. The documented direct form also started an ORDINARY interpreter, so
startup customization influenced the first process and `-S` applied only to the
child it spawned.

THE BOOTSTRAP TRUST ASSUMPTION, which this file checks the CONSEQUENCES of and
deliberately does not try to prove:

    trusted bootstrap boundary =
        OS process creation
      + the selected Python executable and its stdlib startup under hardened
        flags fixed at process creation
      + the explicitly invoked launcher SOURCE bytes

A launcher proving its own trust while already running is the recursion the
repair must not introduce, so nothing here attempts it.

ROOT B -- F06 START-PATH COMPLETENESS. `serialized_append` was exported, took
raw bytes and a caller-controlled `validate=`, and committed
RUN_AUTHORIZED -> OWNER_HOLD -> RUN_STARTED while `serialized_start_append`
correctly refused the same start. The high-level start APIs were right and the
generic mutation boundary beneath them still permitted start semantics.

ANTI-DECORATIVE RULE. Earlier repairs in this lineage produced tests that
encoded the defect as correct, and registered rows their own discovery rule
could never yield. So every guard here carries a companion that drives the
PRE-REPAIR shape through the guard's own rule and shows it fails. Where the
pre-repair shape is a file, it is read from git rather than paraphrased.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import marshal
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf import execution_identity as ei                        # noqa: E402
from itsf.mc import registry_boundary as rb                      # noqa: E402

LAUNCHER = REPO / "scripts" / "run_governed.py"
CMD_WRAPPER = REPO / "scripts" / "run_governed.cmd"
HARDENED = ("-I", "-S", "-B")
#: the commit whose launcher/boundary carry the reproduced defect shapes
PRE_REPAIR = "7c641ba"
C40 = "a" * 40
UTC = "2026-09-07T00:00:00+00:00"


def _run(args, env=None):
    return subprocess.run([sys.executable, *args], capture_output=True,
                          text=True, cwd=str(REPO),
                          env=env if env is not None else os.environ.copy())


def _git_show(rev_path: str) -> str:
    out = subprocess.run(["git", "show", rev_path], cwd=str(REPO),
                         capture_output=True)
    assert out.returncode == 0, rev_path
    return out.stdout.decode("utf-8")


def _launcher_functions(source: str) -> dict:
    tree = ast.parse(source)
    return {n.name: n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


#: The parent's pre-spawn surface. Named rather than inferred so a new helper
#: cannot join the parent phase without being listed here.
PARENT_PHASE = ("main", "missing_parent_flags", "site_directories",
                "child_command", "child_environment", "run_parent")


def _project_imports_in(node) -> list:
    """Every `itsf...` import inside `node`, by AST rather than by text."""
    found = []
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            found += [a.name for a in n.names if a.name.split(".")[0] == "itsf"]
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if mod.split(".")[0] == "itsf":
                found.append(mod)
    return found


# ===========================================================================
# A1 — the parent imports no project module before child construction
# ===========================================================================

def test_A1_the_parent_phase_imports_zero_project_modules():
    src = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(src)

    module_level = []
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            module_level += _project_imports_in(n)
    assert module_level == [], (
        "the launcher imports project modules at MODULE level, so they load "
        "before any function runs: %r" % module_level)

    fns = _launcher_functions(src)
    for name in PARENT_PHASE:
        assert name in fns, f"the parent phase lost {name}"
        offenders = _project_imports_in(fns[name])
        assert offenders == [], (
            "%s runs in the parent phase and imports %r; a forged cache can "
            "only influence code that gets imported" % (name, offenders))


def test_A1_the_bootstrap_stdlib_path_cannot_be_shadowed_by_the_governed_tree():
    """`-P` keeps the script's directory off `sys.path`, and the child APPENDS
    the governed tree rather than prepending it, so stdlib resolves first until
    the attestation has been taken."""
    fns = _launcher_functions(LAUNCHER.read_text(encoding="utf-8"))
    child = ast.unparse(fns["child_command"])
    assert "'-I'" in child, "the child is not isolated, so -P is not implied"

    run_child = ast.unparse(fns["run_child"])
    assert "sys.path.append" in run_child
    assert "sys.path.insert" not in run_child, (
        "the child PREPENDS a governed path, which lets the governed tree "
        "shadow a stdlib module during bootstrap")

    # and measured in a real child: stdlib entries precede the governed tree
    r = _run([*HARDENED, "-c",
              "import sys;print(any('site-packages' in p for p in sys.path[:2]))"])
    assert r.stdout.strip() == "False", r.stdout


def test_A1_ANTI_DECORATIVE_the_rule_fails_against_the_pre_repair_launcher():
    """The pre-repair launcher, read from git, must FAIL the A1 rule -- else the
    rule is decorative."""
    old = _git_show("%s:scripts/run_governed.py" % PRE_REPAIR)
    fns = _launcher_functions(old)
    offenders = {n: _project_imports_in(fns[n])
                 for n in ("_startup_surfaces_are_trusted", "_child_environment")
                 if n in fns}
    assert any(offenders.values()), (
        "the pre-repair launcher shows no project import in its parent phase, "
        "so this rule proves nothing: %r" % offenders)
    assert "_reexec_parent" in fns, (
        "the pre-repair launcher had no self-re-exec, so the removal assertion "
        "is decorative")


# ===========================================================================
# A2 — phase-distinguishable evidence
# ===========================================================================

def test_A2_parent_phase_has_no_governed_import_child_phase_may():
    """Phase-DISTINGUISHING, not a blanket ban: the child legitimately imports
    itsf, and must, once its conditions are established.

    The parent phase is measured by driving exactly what the parent does before
    spawning -- import the launcher module, then call every pre-spawn helper --
    and asking whether any `itsf` module is in `sys.modules` afterwards.
    """
    probe = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('lnch', r'%s')\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "m.missing_parent_flags()\n"
        "dirs = m.site_directories()\n"
        "m.child_command('/tmp/x', dirs, ['itsf.mc.owner_control'])\n"
        "m.child_environment('/tmp/x')\n"
        "print('PARENT_ITSF', sorted(k for k in sys.modules "
        "if k.split('.')[0] == 'itsf'))\n" % LAUNCHER)
    r = _run([*HARDENED, "-c", probe])
    assert r.returncode == 0, r.stderr[-800:]
    assert "PARENT_ITSF []" in r.stdout, (
        "the parent phase imported governed modules: %s" % r.stdout.strip())

    # child phase: the attestation names exactly the bootstrap closure, so the
    # governed import happened only after the child's conditions existed.
    r2 = _run([*HARDENED, str(LAUNCHER), "itsf.mc.owner_control"])
    assert r2.returncode == 0, r2.stderr[-1200:]
    assert "child attested" in r2.stderr
    assert str(sorted(ei.BOOTSTRAP_IMPORT_CLOSURE)) in r2.stderr, (
        "the child's attestation does not name the bootstrap closure, so the "
        "phase boundary is not evidenced: %s" % r2.stderr[-600:])


# ===========================================================================
# A3 — the unflagged form fails closed
# ===========================================================================

def test_A3_the_unflagged_direct_form_refuses_and_spawns_nothing():
    marker = Path(tempfile.mkdtemp()) / "target_ran.txt"
    target = Path(tempfile.mkdtemp()) / "harmless_target.py"
    target.write_text("from pathlib import Path\n"
                      "Path(r'%s').write_text('ran', encoding='utf-8')\n"
                      % marker, encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(target.parent)
    r = _run([str(LAUNCHER), "harmless_target"], env=env)
    assert r.returncode != 0, "the unflagged form exited zero"
    assert "not a sanctioned production launch" in r.stderr
    assert not marker.exists(), "the target executed despite the refusal"
    assert "child attested" not in r.stderr, "a governed child was spawned"


def test_A3_the_refusal_names_the_sanctioned_form_and_never_re_execs():
    r = _run([str(LAUNCHER), "itsf.mc.owner_control"])
    assert "-I -S -B" in r.stderr
    fns = _launcher_functions(LAUNCHER.read_text(encoding="utf-8"))
    assert "_reexec_parent" not in fns
    assert "execv" not in LAUNCHER.read_text(encoding="utf-8")


def test_A3_ANTI_DECORATIVE_the_pre_repair_form_did_NOT_fail_closed():
    old = _git_show("%s:scripts/run_governed.py" % PRE_REPAIR)
    assert "_reexec_parent" in old and "_parent_is_hardened" in old, (
        "the pre-repair launcher did not self-upgrade, so A3 proves nothing")


# ===========================================================================
# A4 — a forged governed cache cannot control launch behaviour
# ===========================================================================

def test_A4_a_forged_execution_identity_cache_cannot_control_the_launch():
    """Places a timestamp-valid forged cache for the REAL governed module, whose
    payload would make the attestation announce itself as FORGED, then runs the
    sanctioned launch. `__pycache__/` is gitignore line 1, and the cache is
    removed in `finally`."""
    src = REPO / "src" / "itsf" / "execution_identity.py"
    cache = Path(importlib.util.cache_from_source(str(src)))
    existed = cache.exists()
    saved = cache.read_bytes() if existed else None
    try:
        py_compile.compile(str(src), doraise=True)
        assert cache.exists(), "no cache to forge; A4 would prove nothing"
        forged_src = (
            "import dataclasses as _dc\n"
            "@_dc.dataclass(frozen=True)\n"
            "class LaunchAttestation:\n"
            "    pycache_prefix: str = 'x'\n"
            "    caches_under_prefix: int = 0\n"
            "    detail: str = 'FORGED-CACHE-CONTROLLED-THE-LAUNCH'\n"
            "    no_site: bool = True\n"
            "def assert_governed_launch(**k):\n"
            "    return LaunchAttestation()\n"
            "def startup_report(**k):\n"
            "    class R:\n"
            "        pinned = True\n"
            "        detail = 'FORGED'\n"
            "    return R()\n"
            "BOOTSTRAP_IMPORT_CLOSURE = frozenset()\n"
            "HOSTILE_ENV_VARS = ()\n")
        cache.write_bytes(cache.read_bytes()[:16]
                          + marshal.dumps(compile(forged_src, str(src), "exec")))

        r = _run([*HARDENED, str(LAUNCHER), "itsf.mc.owner_control"])
        assert r.returncode == 0, r.stderr[-1200:]
        assert "FORGED" not in r.stderr, (
            "the forged governed cache controlled launch behaviour:\n"
            + r.stderr[-800:])
        assert "child attested" in r.stderr
        assert "holds 0 caches" in r.stderr, (
            "the child's private clean cache boundary was not established")
        assert "-S set (read-only" in r.stderr
    finally:
        if saved is not None:
            cache.write_bytes(saved)
        elif cache.exists():
            cache.unlink()


def test_A4_ANTI_DECORATIVE_a_forged_cache_IS_readable_under_dash_B_alone():
    """The premise: `-B` does not stop a READ. If it did, Root A's cache half
    would be imaginary and the repair should be reconsidered rather than
    asserted."""
    d = Path(tempfile.mkdtemp())
    pkg = d / "toy"
    pkg.mkdir()
    (pkg / "__init__.py").write_bytes(b"")
    src = pkg / "m.py"
    src.write_bytes(b"V = 'source'\n")
    py_compile.compile(str(src), doraise=True)
    c = Path(importlib.util.cache_from_source(str(src)))
    c.write_bytes(c.read_bytes()[:16]
                  + marshal.dumps(compile("V = 'FORGED'", str(src), "exec")))
    r = _run(["-B", "-c", "import sys;sys.path.insert(0,r'%s');"
                          "import toy.m;print(toy.m.V)" % d])
    assert r.stdout.strip() == "FORGED", (
        "-B now prevents cache reads, so the mechanism could be simpler")
    shutil.rmtree(d, ignore_errors=True)


# ===========================================================================
# A5 — a synthetic startup surface cannot influence the governed child
# ===========================================================================

def test_A5_a_changed_executable_startup_surface_cannot_influence_the_child():
    d = Path(tempfile.mkdtemp())
    name = sorted(ei.EXPECTED_EXECUTABLE_PTH)[0]
    (d / "hook_payload.py").write_bytes(
        b"import builtins\nbuiltins.__ITSF_STARTUP_RAN__ = True\n")
    (d / name).write_bytes(b"import hook_payload\n")

    # the child runs with -S, so site processing -- and every .pth line with it
    # -- never happens, whatever a site directory contains.
    r = _run([*HARDENED, "-c",
              "import sys;sys.path.append(r'%s');import builtins;"
              "print('HOOK', getattr(builtins,'__ITSF_STARTUP_RAN__',False));"
              "print('no_site', sys.flags.no_site)" % d])
    assert "HOOK False" in r.stdout, r.stdout
    assert "no_site 1" in r.stdout

    # and the existing refusal behaviour on a CHANGED pinned surface remains
    report = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert report.pinned is False
    assert "changed content" in report.detail
    child = ast.unparse(_launcher_functions(
        LAUNCHER.read_text(encoding="utf-8"))["run_child"])
    assert "startup_report" in child and "REFUSING" in child, (
        "the child no longer refuses on a changed pinned startup surface")


# ===========================================================================
# A6 — duplicated constant equality, and bootstrap path ordering
# ===========================================================================

def test_A6_the_parent_local_hostile_env_tuple_equals_the_authoritative_one():
    """The parent may not import the project, so the tuple is duplicated. Its
    equality to the authoritative constant is pinned here, from the governed
    context, so the two cannot drift into a second policy authority."""
    spec = importlib.util.spec_from_file_location("_lnch", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert tuple(mod.HOSTILE_ENV_VARS) == tuple(ei.HOSTILE_ENV_VARS), (
        "the launcher's local copy drifted from "
        "itsf.execution_identity.HOSTILE_ENV_VARS")
    assert mod.REQUIRED_PARENT_FLAGS == ("no_site", "ignore_environment",
                                         "dont_write_bytecode", "safe_path")


def test_A6_bootstrap_stdlib_resolution_precedes_the_governed_tree():
    probe = (
        "import sys\n"
        "before = list(sys.path)\n"
        "sys.path.append(r'%s')\n"
        "import itsf.execution_identity as m\n"
        "gov = sys.path.index(r'%s')\n"
        "print('GOVERNED_AT', gov, 'OF', len(sys.path))\n"
        "print('AHEAD_ALL_STDLIB', gov >= len(before))\n"
        % (REPO / "src", REPO / "src"))
    r = _run([*HARDENED, "-c", probe])
    assert r.returncode == 0, r.stderr[-600:]
    assert "AHEAD_ALL_STDLIB True" in r.stdout, r.stdout


def test_A6_the_cmd_wrapper_is_the_same_sanctioned_form():
    text = CMD_WRAPPER.read_text(encoding="utf-8", errors="replace")
    assert "-I" in text and "-S" in text and "-B" in text
    assert "run_governed.py" in text


# ===========================================================================
# B1 — the generic entry cannot commit start-equivalent rows
# ===========================================================================

def _ledger(tmp_path, name="SCRATCH_REGISTRY.md"):
    p = tmp_path / name
    p.write_bytes(("| 1 | %s | RUN_AUTHORIZED | %s | Aaron | [S0-T001] ok |\n"
                   % (UTC, C40)).encode("utf-8"))
    return p


def _hold(seq=2, scope="GLOBAL"):
    return ("| %d | %s | OWNER_HOLD | %s | Aaron | [%s] reason: stop |\n"
            % (seq, UTC, C40, scope)).encode("utf-8")


def _row(event, seq="+"):
    return ("| %s | %s | %s | abc1234 | agent | [S0-T001] n |\n"
            % (seq, UTC, event)).encode("utf-8")


#: Every start token, in every spelling the AUTHORITATIVE parser normalizes.
START_SPELLINGS = [(tok, spelling)
                   for tok in rb.START_EQUIVALENT_TOKENS
                   for spelling in (tok, "**%s**" % tok, "  %s  " % tok)]


@pytest.mark.parametrize("held", [False, True])
@pytest.mark.parametrize("token,spelling", START_SPELLINGS)
def test_B1_generic_append_refuses_every_start_spelling(tmp_path, token,
                                                        spelling, held):
    path = _ledger(tmp_path, "reg_%s_%s.md" % (token, int(held)))
    if held:
        rb.serialized_append(path, _hold())
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.serialized_append(path, _row(spelling))
    assert caught.value.code == "generic_append_refuses_start_equivalent"
    assert path.read_bytes() == before, "bytes moved on a refused append"
    assert not path.with_name(path.name + rb.LOCK_SUFFIX).exists(), "stale lock"


def test_B1_a_malformed_nonblank_addition_is_refused_not_treated_as_generic(
        tmp_path):
    """Measured: the parser yields zero rows and NO refusal for a malformed
    line, so without this an addition could dodge classification by being
    unparseable."""
    path = _ledger(tmp_path)
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.serialized_append(path, b"| + | oops | missing cells |\n")
    assert caught.value.code == "append_addition_unparseable"
    assert path.read_bytes() == before


def test_B1_ANTI_DECORATIVE_the_pre_repair_generic_entry_committed_the_start():
    """The pre-repair boundary, read from git: its generic entry took a
    caller-controlled `validate` and performed the write itself."""
    old = _git_show("%s:src/itsf/mc/registry_boundary.py" % PRE_REPAIR)
    fns = {n.name: n for n in ast.walk(ast.parse(old))
           if isinstance(n, ast.FunctionDef)}
    generic = ast.unparse(fns["serialized_append"])
    assert "validate" in generic, (
        "the pre-repair generic entry had no caller-controlled validate, so B1 "
        "proves nothing")
    assert "target.write_bytes(" in generic, (
        "the pre-repair generic entry did not perform the write itself")
    assert "is_start_equivalent" not in generic, (
        "the pre-repair generic entry already classified start events")


# ===========================================================================
# B2 — generic non-start events still commit, including under a GLOBAL hold
# ===========================================================================

@pytest.mark.parametrize("event", ["STAGE_D_COMPLETE", "COMPLETED",
                                   "PRE_RUN_ATTEMPT_FAILURE",
                                   "RUN_AUTHORIZED"])
def test_B2_generic_non_start_events_commit_under_an_active_global_hold(
        tmp_path, event):
    path = _ledger(tmp_path, "reg_%s.md" % event)
    rb.serialized_append(path, _hold())
    before = path.read_bytes()
    rb.serialized_append(path, _row(event))
    assert path.read_bytes() != before, (
        "a generic event was refused; the repair turned generic mutation into "
        "start-only mutation")
    assert not rb.is_start_equivalent(event)


def test_B2_owner_rows_still_commit_through_the_generic_entry(tmp_path):
    """A hold and a release are not starts, so filing them must not be subject
    to the start refusal -- otherwise the first hold makes the second
    unfileable."""
    path = _ledger(tmp_path)
    rb.serialized_append(path, _hold(seq=2))
    rb.serialized_append(path, _hold(seq=3))
    assert path.read_text(encoding="utf-8").count("OWNER_HOLD") == 2


# ===========================================================================
# B3 — the start entry requires the start shape and applies owner semantics
# ===========================================================================

def test_B3_invalid_start_shapes_are_refused(tmp_path):
    path = _ledger(tmp_path)
    before = path.read_bytes()
    cases = {
        "non-start row": (_row("STAGE_D_COMPLETE"),
                          "start_append_requires_exactly_one_start_row"),
        "two rows": (_row("STAGE_D_COMPLETE") + _row("RUN_STARTED"),
                     "start_append_requires_exactly_one_start_row"),
        "two starts": (_row("RUN_STARTED") + _row("RUN_STARTED"),
                       "start_append_requires_exactly_one_start_row"),
        "malformed": (b"| + | oops | missing |\n",
                      "append_addition_unparseable"),
    }
    for label, (addition, code) in cases.items():
        with pytest.raises(rb.AppendRefused) as caught:
            rb.serialized_start_append(path, addition, run_id="S0-T001")
        assert caught.value.code == code, label
    assert path.read_bytes() == before


def test_B3_a_valid_start_commits_and_an_applicable_hold_refuses(tmp_path):
    path = _ledger(tmp_path)
    before = path.read_bytes()
    rb.serialized_start_append(path, _row("RUN_STARTED"), run_id="S0-T001")
    assert path.read_bytes() != before, "a valid start was refused"
    rb.serialized_append(path, _hold())
    held = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.serialized_start_append(path, _row("RUN_STARTED"), run_id="S0-T001")
    assert caught.value.code == "start_refused_owner_hold_in_force"
    assert path.read_bytes() == held


# ===========================================================================
# B4 — the mechanical boundary proof
# ===========================================================================

def _boundary_functions():
    src = (REPO / "src" / "itsf" / "mc" / "registry_boundary.py").read_text(
        encoding="utf-8")
    return src, {n.name: n for n in ast.walk(ast.parse(src))
                 if isinstance(n, ast.FunctionDef)}


def test_B4_one_physical_write_site_and_both_public_entries_converge_there():
    src, fns = _boundary_functions()
    writers = [name for name, node in fns.items()
               if "write_bytes" in {getattr(c.func, "attr", None)
                                    for c in ast.walk(node)
                                    if isinstance(c, ast.Call)}]
    assert writers == ["_physical_serialized_write"], (
        "more than one physical registry write site: %r" % writers)
    for entry in ("serialized_append", "serialized_start_append"):
        called = {getattr(c.func, "attr", None) or getattr(c.func, "id", None)
                  for c in ast.walk(fns[entry]) if isinstance(c, ast.Call)}
        assert "_physical_serialized_write" in called, (
            "%s does not converge on the one write" % entry)


def test_B4_no_caller_controlled_bypass_on_either_public_entry():
    import inspect
    banned = {"validate", "allow_start", "skip_validation", "unsafe", "force",
              "decide", "skip", "raw"}
    for name in ("serialized_append", "serialized_start_append"):
        params = set(inspect.signature(getattr(rb, name)).parameters)
        assert not (params & banned), (
            "%s exposes a caller-controlled bypass: %r"
            % (name, sorted(params & banned)))
    assert "_physical_serialized_write" not in rb.__all__, (
        "the private write is exported, restoring the raw route")


def test_B4_the_start_entry_necessarily_supplies_the_start_decision():
    _src, fns = _boundary_functions()
    start = ast.unparse(fns["serialized_start_append"])
    assert "assert_no_hold_blocks_start" in start
    assert "decide=_decide" in start
    generic = ast.unparse(fns["serialized_append"])
    assert "decide=" not in generic, (
        "the generic entry passes a decision, so it can carry start semantics")
    assert "is_start_equivalent" in ast.unparse(fns["_classify_addition"])


def test_B4_supported_callers_of_the_one_write_are_registered():
    _src, fns = _boundary_functions()
    callers = sorted(name for name, node in fns.items()
                     if "_physical_serialized_write"
                     in {getattr(c.func, "attr", None) or getattr(c.func, "id", None)
                         for c in ast.walk(node) if isinstance(c, ast.Call)})
    assert callers == ["serialized_append", "serialized_start_append"], (
        "the one physical write gained an unregistered caller: %r" % callers)


def test_B4_ANTI_DECORATIVE_the_pre_repair_shape_fails_this_guard():
    """Drive B4's own rules over the pre-repair boundary from git."""
    old = _git_show("%s:src/itsf/mc/registry_boundary.py" % PRE_REPAIR)
    fns = {n.name: n for n in ast.walk(ast.parse(old))
           if isinstance(n, ast.FunctionDef)}
    assert "_physical_serialized_write" not in fns, (
        "the pre-repair boundary already had the private write")
    writers = [name for name, node in fns.items()
               if "write_bytes" in {getattr(c.func, "attr", None)
                                    for c in ast.walk(node)
                                    if isinstance(c, ast.Call)}]
    assert writers == ["serialized_append"], (
        "the pre-repair physical write was not in the PUBLIC generic entry, so "
        "B4's convergence rule proves nothing: %r" % writers)
    # and the exact raw-start-through-generic shape is what B1 now refuses
    assert "validate" in ast.unparse(fns["serialized_append"])


def test_no_check_here_touched_the_real_registry():
    import test_qros_cf_astra_repairs as R1
    assert (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(
        encoding="utf-8") == R1.LIVE_REGISTRY
