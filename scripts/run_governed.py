"""Launch a governed entry point under the attested launch conditions.

QROS-CF F01. The gap the re-review found is not that the bytecode check was
weak, it is that it ran too LATE: a census taken at the first-write seam
cannot prove a governed module was not loaded from a forged cache earlier in
the same process, because the forged cache can be deleted in between. The
proof has to be taken before the governed imports, and something has to
establish the conditions it proves. That is this file.

WHAT IT DOES, in order, and the order is the whole point:

  1. If this process was not launched with `-B` and a private
     `PYTHONPYCACHEPREFIX`, re-launch it that way -- a fresh private cache
     directory per run, created here, at a path no earlier tamper could have
     predicted -- and exit with the child's status.
  2. Import ONLY `itsf.execution_identity` (measured: `src/itsf/__init__.py`
     is 0 bytes, so that is exactly two governed modules) and call
     `assert_governed_launch()`, which refuses unless the read-only launch
     flag is set, the private prefix holds zero caches, and no other governed
     module has been imported yet.
  3. Only then import and run the requested entry point.

THE FLAGS ARE MEASURED, NOT COPIED. `-S` and `-I` would stop `.pth`
processing and close F02 by construction; both were tried first and `import
pandas` fails under either, so they trade a startup surface for the pinned
environment. `-E` would make the interpreter ignore `PYTHONPYCACHEPREFIX`,
silently unsetting the prefix and making the repository's own `__pycache__`
readable again. So the minimum compatible launch is `-B` plus the prefix, and
nothing else.

USAGE
    python scripts/run_governed.py <module>[:<callable>] [args...]

`<module>` is imported; if `:<callable>` is given it is called with the
remaining arguments. Nothing here decides anything about a run -- it only
establishes and proves the launch conditions, then hands control over.
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

#: The env var the child is launched with, and the one step 1 keys off.
PREFIX_VAR = "PYTHONPYCACHEPREFIX"

#: Set by the parent so a child cannot re-launch itself forever if the flags
#: somehow fail to take effect. A second failure is a refusal, not a loop.
RELAUNCH_MARKER = "ITSF_GOVERNED_RELAUNCHED"


def _already_launched_correctly() -> bool:
    """Both facts `assert_governed_launch` needs from the launch itself."""
    return bool(sys.flags.dont_write_bytecode) and bool(sys.pycache_prefix)


def _relaunch(argv: list) -> int:
    """Re-run this script with the minimum compatible launch semantics."""
    if os.environ.get(RELAUNCH_MARKER):
        sys.stderr.write(
            "run_governed: re-launched once and the launch conditions still "
            "do not hold (dont_write_bytecode=%r pycache_prefix=%r); "
            "refusing rather than looping\n"
            % (sys.flags.dont_write_bytecode, sys.pycache_prefix))
        return 2
    prefix = tempfile.mkdtemp(prefix="itsf-pycache-")
    env = dict(os.environ)
    env[PREFIX_VAR] = prefix
    env[RELAUNCH_MARKER] = "1"
    try:
        return subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), *argv],
            env=env).returncode
    finally:
        # `-B` means the child wrote nothing, so this removes an empty tree.
        shutil.rmtree(prefix, ignore_errors=True)


def main(argv: list) -> int:
    if not argv:
        sys.stderr.write(__doc__.split("USAGE")[1].strip() + "\n")
        return 2
    if not _already_launched_correctly():
        return _relaunch(argv)

    # STEP 2. Import the attestation module and NOTHING ELSE governed, then
    # prove the launch before any other governed import can happen.
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    from itsf.execution_identity import assert_governed_launch

    attestation = assert_governed_launch()
    sys.stderr.write("run_governed: %s\n" % attestation.detail)

    # STEP 3. Now, and only now, the governed entry point.
    target, _, func = argv[0].partition(":")
    import importlib

    module = importlib.import_module(target)
    if not func:
        return 0
    result = getattr(module, func)(*argv[1:])
    return int(result) if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
