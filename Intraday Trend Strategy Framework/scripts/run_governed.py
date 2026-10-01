"""The trusted launch boundary for every governed real run.

QROS-CF ROOT BLOCKER A, FINAL BOUNDED REPAIR. The independent reviewer
reproduced two things about the previous shape:

  F01  the parent imported `itsf.execution_identity` BEFORE the trusted
       execution boundary existed, and `-B` prevents bytecode WRITES but not
       READS -- a timestamp-valid forged `.pyc` in the governed tree therefore
       influenced launch behaviour from inside the supposed trust boundary.
  F02  the documented direct form `python scripts/run_governed.py ...` starts
       an ORDINARY interpreter. Startup customization influences that first
       process, and `-S` applied only to the child it went on to spawn.

So the trust root moved OUT of project-governed Python semantics.

THE BOOTSTRAP TRUST ASSUMPTION, stated once and not proved by this file --
because a launcher that tried to prove its own trust while already executing is
the recursion this repair must not introduce:

    trusted bootstrap boundary =
        OS process creation
      + the selected Python executable and its stdlib startup under the
        hardened flags, which are fixed AT process creation and are read-only
      + the explicitly invoked launcher SOURCE bytes

Everything after that boundary is checked. Nothing before it is, and nothing
here pretends otherwise. There is no machine hashing, no executable signing, no
launcher signature, no provenance framework and no trust ledger: the recursion
stops at the assumption above.

THE SANCTIONED FORM

    python -I -S -B scripts/run_governed.py <module>[:<callable>] [args...]
    scripts\\run_governed.cmd            <module>[:<callable>] [args...]

`-I` supplies `-E`, `-s` and `-P`. The `.cmd` file is only a fixed spelling of
that same form. The unflagged form is NOT a sanctioned production launch: it
fails closed, spawns nothing, and deliberately does NOT re-exec itself -- an
upgrade attempted from an already-untrusted interpreter proves nothing about
what ran in it.

WHY THE PARENT IMPORTS NOTHING FROM THE PROJECT. A forged cache can only
influence code that gets imported. The parent's job is to construct the child;
it does that with the standard library alone, so there is no governed module
whose bytes a cache could substitute. `HOSTILE_ENV_VARS` is the one small
constant it needs, and it is duplicated below as a frozen tuple with its
equality to the authoritative project constant pinned by test rather than by
hope.

THE CHILD'S CONDITIONS, all fixed at ITS process creation:

    -I  isolated: implies -E (env ignored), -s (no user site), -P (safe_path)
    -S  no site processing: no `.pth` line, no sitecustomize, no usercustomize
    -B  no bytecode written
    -X pycache_prefix=<fresh private dir>
        every cache lookup -- READ as well as write -- leaves the repository,
        into a directory created for this run at a path nothing could predict.
        Passed as -X rather than an environment variable precisely because -I
        makes the interpreter ignore PYTHONPYCACHEPREFIX.

`-P` (safe_path) is what stops the script's own directory from being prepended
to `sys.path`, so the governed tree cannot shadow a stdlib module during
bootstrap. The child then APPENDS the site directories and `src/`, never
prepends, so stdlib resolution stays ahead of the governed tree until the
attestation has been taken.

Measured, not assumed: under `-I -S -B` with the site directories appended,
pandas, numpy, scipy, pyarrow, databento, zstandard, exchange_calendars and
pandas_market_calendars all import, `site` is absent from `sys.modules`, and no
`.pth` executes.

WHAT THE STARTUP-SURFACE BYTE CHECK IS NOW FOR. It runs in the child, AFTER the
attestation, as reporting and secondary verification. It is no longer the proof
that startup code could not execute -- `-S`, fixed at process creation, is.
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

#: Child mode is a flag rather than a second file: one file, one story.
CHILD_FLAG = "--itsf-governed-child"
SITEDIR_FLAG = "--itsf-sitedir"

#: The parent's own conditions, every one fixed at process creation and exposed
#: read-only on `sys.flags`. `-I` supplies the last three.
REQUIRED_PARENT_FLAGS = ("no_site", "ignore_environment",
                         "dont_write_bytecode", "safe_path")

#: The sanctioned spelling, kept as data so the refusal can print it and a test
#: can pin it.
SANCTIONED_FORM = ("python -I -S -B scripts/run_governed.py "
                   "<module>[:<callable>] [args...]")

#: DUPLICATED DELIBERATELY, and minimally. The parent must scrub these before
#: constructing the child, and importing the project to learn them is exactly
#: what Root A forbids. This is a frozen copy, not a second policy authority:
#: `tests/test_qros_cf_pre_cert.py` pins it equal to
#: `itsf.execution_identity.HOSTILE_ENV_VARS` from the governed context, so the
#: two cannot drift.
HOSTILE_ENV_VARS = ("PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME",
                    "PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE",
                    "GIT_CONFIG", "GIT_CONFIG_GLOBAL", "GIT_TEMPLATE_DIR",
                    "GIT_CEILING_DIRECTORIES")


# --------------------------------------------------------------------------
# parent -- STANDARD LIBRARY ONLY until the child has been constructed
# --------------------------------------------------------------------------
def missing_parent_flags(flags=None) -> list:
    """Which required launch conditions this process does NOT have."""
    flags = sys.flags if flags is None else flags
    return [name for name in REQUIRED_PARENT_FLAGS
            if not getattr(flags, name, 0)]


def site_directories() -> list:
    """Every real site directory, discovered with the stdlib.

    `import site` is a standard-library import; under `-S` only its automatic
    INVOCATION is skipped, so its helpers still answer. `sysconfig` is the
    fallback so a stripped build yields something rather than nothing.
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
    out = [p for p in dict.fromkeys(found) if p and Path(p).is_dir()]
    if not out:
        raise SystemExit("run_governed: no site directory found; the child "
                         "would start with no installed packages")
    return out


def child_command(prefix: str, sitedirs, argv) -> list:
    """The child's argv. Every trust condition is a flag, fixed at ITS process
    creation -- not something the child asks for once it is already running."""
    cmd = [sys.executable, "-I", "-S", "-B",
           "-X", "pycache_prefix=" + prefix,
           str(Path(__file__).resolve()), CHILD_FLAG]
    for d in sitedirs:
        cmd += [SITEDIR_FLAG, d]
    return cmd + ["--", *argv]


def child_environment(prefix: str) -> dict:
    """Hostile variables out. The private prefix travels as `-X`, not as an
    environment variable, because `-I` makes the child ignore the latter."""
    return {k: v for k, v in os.environ.items()
            if k not in HOSTILE_ENV_VARS}


def run_parent(argv: list) -> int:
    sitedirs = site_directories()
    prefix = tempfile.mkdtemp(prefix="itsf-pycache-")
    try:
        return subprocess.run(child_command(prefix, sitedirs, argv),
                              env=child_environment(prefix)).returncode
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

    # APPENDED, never prepended: stdlib resolution stays ahead of the governed
    # tree until the attestation has been taken. `-P` already kept the script's
    # own directory off `sys.path`.
    for d in sitedirs:
        if d not in sys.path:
            sys.path.append(d)
    if str(SRC) not in sys.path:
        sys.path.append(str(SRC))
    # AND THE REPOSITORY ROOT, so a `scripts.*` target is importable.
    #
    # `-P` keeps the launcher's own directory off `sys.path`, which is what
    # made `scripts.mc_real_run:main` fail to import with
    # `ModuleNotFoundError: No module named 'scripts'` -- the launcher could
    # start a target under `src/` and nothing else. APPENDED like the two
    # above, never prepended, so stdlib resolution still runs ahead of the
    # governed tree until the attestation has been taken.
    if str(REPO) not in sys.path:
        sys.path.append(str(REPO))

    # The FIRST governed import, and the proof comes immediately after it.
    from itsf.execution_identity import assert_governed_launch

    attestation = assert_governed_launch()
    sys.stderr.write("run_governed: child attested: %s\n" % attestation.detail)

    # SECONDARY, and only now: the executable startup surfaces are reported
    # against their pinned bytes. This is no longer the proof that startup code
    # could not execute -- `-S` is -- but a changed pinned surface still refuses,
    # because a machine whose startup changed is one the operator should hear
    # about.
    from itsf import execution_identity as _ei

    report = _ei.startup_report(sitedirs=sitedirs)
    if not report.pinned:
        sys.stderr.write("run_governed: REFUSING -- a permitted executable "
                         "startup artifact is not the one pinned:\n  %s\n"
                         % report.detail)
        return 3
    sys.stderr.write("run_governed: startup surfaces reported clean: %s\n"
                     % report.detail)

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
        sys.stderr.write("usage: %s\n" % SANCTIONED_FORM)
        return 2
    missing = missing_parent_flags()
    if missing:
        # FAIL CLOSED. No child, no target, and deliberately NO self-re-exec:
        # upgrading from an interpreter that is already untrusted would prove
        # nothing about what ran in it before this line.
        sys.stderr.write(
            "run_governed: REFUSING -- this is not a sanctioned production "
            "launch.\n"
            "  missing required launch conditions: %s\n"
            "  the sanctioned form fixes them at process creation:\n"
            "    %s\n"
            "  (or scripts\\run_governed.cmd, the same form spelled once)\n"
            "  This form is not upgraded by re-exec: an interpreter that has "
            "already run\n"
            "  startup code cannot establish that it did not.\n"
            % (", ".join(missing), SANCTIONED_FORM))
        return 2
    return run_parent(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
