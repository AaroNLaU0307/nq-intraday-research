"""The trusted launch boundary for every governed real run.

QROS-CF F01/F02, PRE-CERT REPAIR. The previous version of this file re-launched
with `-B` and a private `PYTHONPYCACHEPREFIX` and then attested. Preparing the
final-certification transport measured two residuals that shape survives:

  R1  an allowed executable `.pth` was checked AFTER Python startup. A `.pth`
      `import` line runs during site initialisation, before any project line,
      so checking its bytes later cannot constrain what already ran.
  R2  a startup hook could import a governed module, mutate it, delete the
      child entries from `sys.modules`, and leave exactly the permitted
      bootstrap closure -- after which the attestation passed. Reproduced.

Both are the same temporal hole, and no later check reaches either. So the
control is now PREVENTION rather than inspection:

    the governed child runs with `-S`, and under `-S` no `.pth` line is
    executed, `site` is never imported, and neither `sitecustomize` nor
    `usercustomize` is imported.

THE MEASUREMENT THAT MADE THAT POSSIBLE, and it corrects an earlier one. The
first repair recorded that `-S` "cannot be used" because `import pandas` fails
under it. That was true and the conclusion was wrong: `-S` alone fails; `-S`
plus the site directories placed on `sys.path` does not. Measured under
`-S -B` with this machine's three real site directories appended -- pandas,
numpy, scipy, pyarrow, databento, zstandard, exchange_calendars,
pandas_market_calendars and pytest all import, `site` is absent from
`sys.modules`, and no `.pth` executes. Supplying those directories is this
launcher's job, which is why the boundary is two processes rather than one.

THE SHAPE

    scripts/run_governed.cmd            (optional; starts the parent under -S)
      -> PARENT, stdlib only, -S -E -B
           verifies the executable startup surfaces by BYTES
           creates a fresh private pycache directory at an unpredictable path
           scrubs the hostile PYTHON*/GIT_* variables
      -> CHILD, -S -B, PYTHONPYCACHEPREFIX=<fresh>
           appends the site directories handed to it on argv
           imports ONLY itsf.execution_identity and attests
      -> the governed target

WHY THE PARENT ALSO RUNS -S. The parent is not the governed process, but a
`.pth` that executed in it could patch `subprocess` and spawn a child without
`-S`. Running the parent under `-S` too removes that step rather than arguing
about it. `-E` is added for the parent alone: it ignores the hostile PYTHON*
variables outright, and the parent has no use for `PYTHONPYCACHEPREFIX`
because `-B` means it writes nothing. The CHILD must not get `-E`, because
`-E` would make the interpreter ignore the private prefix and the
repository's own `__pycache__` would become readable again.

WHAT IS NOT CLAIMED. The outermost process in any chain has already completed
its own interpreter startup by the time it can run a line of code. What this
boundary gives is that no startup surface executes in the process that runs
governed semantics, and that the parent refuses to spawn at all when a
permitted startup artifact's bytes have changed. It is not a whole-machine
hash and does not pretend to be.

USAGE
    python scripts/run_governed.py <module>[:<callable>] [args...]
    scripts\\run_governed.cmd       <module>[:<callable>] [args...]
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"

PREFIX_VAR = "PYTHONPYCACHEPREFIX"

#: Set by the parent so a child cannot re-launch itself forever if the flags
#: somehow fail to take effect. A second failure is a refusal, not a loop.
RELAUNCH_MARKER = "ITSF_GOVERNED_RELAUNCHED"

#: Child mode is a flag rather than a second file: one file, one story.
CHILD_FLAG = "--itsf-governed-child"
SITEDIR_FLAG = "--itsf-sitedir"


# --------------------------------------------------------------------------
# site directories -- discovered with the stdlib, because -S means they are
# not on sys.path and the child has to be told.
# --------------------------------------------------------------------------
def site_directories() -> list:
    """Every real site directory this interpreter would normally add.

    `import site` works under `-S`; only its automatic INVOCATION is skipped.
    `sysconfig` is the fallback so a stripped build still yields something
    rather than silently yielding nothing.
    """
    found = []
    try:
        import site
        found.extend(site.getsitepackages())
        try:
            found.append(site.getusersitepackages())
        except Exception:                                      # noqa: BLE001
            pass
    except Exception:                                          # noqa: BLE001
        pass
    if not found:
        import sysconfig
        for key in ("purelib", "platlib"):
            path = sysconfig.get_paths().get(key)
            if path:
                found.append(path)
        for scheme in ("nt_user", "posix_user"):
            try:
                found.append(sysconfig.get_path("purelib", scheme))
            except Exception:                                  # noqa: BLE001
                pass
    out = [p for p in dict.fromkeys(found) if p and Path(p).is_dir()]
    if not out:
        raise SystemExit("run_governed: no site directory found; the child "
                         "would start with no installed packages and the "
                         "pinned environment gate would refuse anyway")
    return out


def _startup_surfaces_are_trusted(sitedirs) -> tuple:
    """(ok, detail) for the executable startup artifacts, BY BYTES.

    This is the parent-side half. Prevention (`-S` on the child) is what makes
    the guarantee; this makes a CHANGED permitted artifact a refusal to launch
    rather than a thing the child merely never runs, so tampering is reported
    instead of tolerated.
    """
    sys.path.insert(0, str(SRC))
    from itsf import execution_identity as ei

    report = ei.startup_report(sitedirs=sitedirs)
    return report.pinned, report.detail


def _child_environment(prefix: str) -> dict:
    """The child's environment: the private prefix in, hostile variables out."""
    sys.path.insert(0, str(SRC))
    from itsf import execution_identity as ei

    env = {k: v for k, v in os.environ.items()
           if k not in ei.HOSTILE_ENV_VARS}
    env[PREFIX_VAR] = prefix
    env[RELAUNCH_MARKER] = "1"
    return env


# --------------------------------------------------------------------------
# parent
# --------------------------------------------------------------------------
def _parent_is_hardened() -> bool:
    return bool(sys.flags.no_site) and bool(sys.flags.dont_write_bytecode)


def _reexec_parent(argv: list) -> int:
    """Run the parent itself under -S -E -B, so no `.pth` ran in it either."""
    if os.environ.get(RELAUNCH_MARKER):
        sys.stderr.write(
            "run_governed: re-launched once and the parent is still not "
            "hardened (no_site=%r dont_write_bytecode=%r); refusing rather "
            "than looping\n"
            % (sys.flags.no_site, sys.flags.dont_write_bytecode))
        return 2
    env = dict(os.environ)
    env[RELAUNCH_MARKER] = "1"
    return subprocess.run(
        [sys.executable, "-S", "-E", "-B", str(Path(__file__).resolve()),
         *argv], env=env).returncode


def run_parent(argv: list) -> int:
    sitedirs = site_directories()
    ok, detail = _startup_surfaces_are_trusted(sitedirs)
    if not ok:
        sys.stderr.write(
            "run_governed: REFUSING TO LAUNCH -- a permitted executable "
            "startup artifact is not the one that was pinned, so the child is "
            "not started at all:\n  %s\n" % detail)
        return 3
    sys.stderr.write("run_governed: startup surfaces trusted: %s\n" % detail)

    prefix = tempfile.mkdtemp(prefix="itsf-pycache-")
    try:
        child = [sys.executable, "-S", "-B", str(Path(__file__).resolve()),
                 CHILD_FLAG]
        for d in sitedirs:
            child += [SITEDIR_FLAG, d]
        child += ["--", *argv]
        return subprocess.run(child, env=_child_environment(prefix)).returncode
    finally:
        # `-B` means the child wrote nothing, so this removes an empty tree.
        shutil.rmtree(prefix, ignore_errors=True)


# --------------------------------------------------------------------------
# child
# --------------------------------------------------------------------------
def run_child(argv: list) -> int:
    sitedirs, rest = [], []
    i = 0
    while i < len(argv):
        if argv[i] == SITEDIR_FLAG:
            sitedirs.append(argv[i + 1])
            i += 2
            continue
        if argv[i] == "--":
            rest = argv[i + 1:]
            break
        i += 1
    if not rest:
        sys.stderr.write("run_governed: child got no target\n")
        return 2

    # The site directories `-S` did not add. Done BEFORE the attestation so
    # the child can import at all; none of them can execute a `.pth`, because
    # appending a path is not site initialisation.
    for d in sitedirs:
        if d not in sys.path:
            sys.path.append(d)
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))

    # ONLY the attestation module, and then the proof, before anything else
    # governed is imported.
    from itsf.execution_identity import assert_governed_launch

    attestation = assert_governed_launch()
    sys.stderr.write("run_governed: %s\n" % attestation.detail)

    target, _, func = rest[0].partition(":")
    import importlib

    module = importlib.import_module(target)
    if not func:
        return 0
    result = getattr(module, func)(*rest[1:])
    return int(result) if isinstance(result, int) else 0


def main(argv: list) -> int:
    if argv and argv[0] == CHILD_FLAG:
        return run_child(argv[1:])
    if not argv:
        sys.stderr.write(
            "usage: python scripts/run_governed.py <module>[:<callable>] "
            "[args...]\n")
        return 2
    if not _parent_is_hardened():
        return _reexec_parent(argv)
    return run_parent(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
