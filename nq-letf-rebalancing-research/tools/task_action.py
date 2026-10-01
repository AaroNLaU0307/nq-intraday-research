#!/usr/bin/env python3
"""Canonical Task Scheduler action-argument construction for the forward PIT task.

WHY THIS EXISTS
---------------
The project path contains a space ("Quant trade"). With the naive form

    cmd.exe /c "<script>" "<python>"

cmd.exe strips the surrounding quotes and then breaks the command at the first
space, producing:

    'C:\\Users\\Aaron\\OneDrive\\Desktop\\Quant' is not recognized ...   (exit 1)

The correct form doubles the outer quotes and adds /s, which tells cmd.exe to
strip ONLY the outermost pair and treat the remainder verbatim:

    cmd.exe /d /s /c ""<script>" "<python>""                             (exit 0)

/d additionally skips any AutoRun command, so a machine-local AutoRun registry
value cannot inject itself into an unattended scheduled run.

This module is the single source of truth for that string. The PowerShell
installer calls it rather than re-deriving the quoting, so the two cannot drift
apart -- drift is exactly how this bug would come back.

Run directly to emit the argument string:
    python task_action.py --script <path.cmd> --interpreter <python.exe>
"""

from __future__ import annotations

import argparse
import sys

CMD_PREFIX = "/d /s /c "


def build_action_arguments(script: str, interpreter: str) -> str:
    """Build the cmd.exe argument string for the scheduled action.

    Both paths are embedded verbatim; only the outer quoting is added.
    """
    for label, value in (("script", script), ("interpreter", interpreter)):
        if not value or not value.strip():
            raise ValueError(f"{label} path must not be empty")
        if '"' in value:
            raise ValueError(f"{label} path must not contain a double quote: {value!r}")
    return f'{CMD_PREFIX}""{script}" "{interpreter}""'


def validate_action_arguments(arguments: str) -> tuple[bool, str]:
    """Check a stored Arguments value preserves the required quoting semantics.

    Returns (ok, reason). Used by the installer after registration and by the
    regression tests, so a silently reverted action is caught rather than
    assumed correct.
    """
    if not arguments:
        return False, "empty arguments"
    if not arguments.startswith(CMD_PREFIX):
        return False, f"must start with {CMD_PREFIX!r} (got {arguments[:12]!r})"

    body = arguments[len(CMD_PREFIX):]
    if not body.startswith('""'):
        return False, "missing doubled opening quote after /d /s /c"
    if not body.endswith('""'):
        return False, "missing doubled closing quote at end"

    # Inside the outer pair there must be exactly two quoted tokens.
    inner = body[1:-1]
    if not (inner.startswith('"') and inner.endswith('"')):
        return False, "inner command is not quote-delimited"
    quotes = inner.count('"')
    if quotes != 4:
        return False, f"expected exactly two quoted tokens, found {quotes // 2}"
    return True, "ok"


def split_action_arguments(arguments: str) -> tuple[str, str]:
    """Recover (script, interpreter) from a canonical argument string."""
    ok, reason = validate_action_arguments(arguments)
    if not ok:
        raise ValueError(f"not a canonical action argument string: {reason}")
    inner = arguments[len(CMD_PREFIX) + 1:-1]
    parts = inner.split('" "')
    if len(parts) != 2:
        raise ValueError("could not split into exactly two tokens")
    return parts[0].lstrip('"'), parts[1].rstrip('"')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True)
    parser.add_argument("--interpreter", required=True)
    parser.add_argument("--validate", default=None, help="validate a string instead")
    args = parser.parse_args(argv)

    if args.validate is not None:
        ok, reason = validate_action_arguments(args.validate)
        print("OK" if ok else f"INVALID: {reason}")
        return 0 if ok else 1

    sys.stdout.write(build_action_arguments(args.script, args.interpreter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
