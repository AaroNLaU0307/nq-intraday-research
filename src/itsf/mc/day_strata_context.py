"""Assembling a `GateContext`, and refusing an incomplete one.

WHAT WAS MISSING. `GateContext` exists, the gates exist, and NOTHING in
`src/` ever built one — only tests did, seven times. That is the same gap
shape the row producer was: every piece present, no production path
between them.

WHY AN INCOMPLETE CONTEXT IS DANGEROUS rather than merely unhelpful. Every
optional field defaults to `None`. A gate handed `chain=None` does not
crash in an obvious way — it evaluates whatever `None` makes its condition
do, and reports a PASS or a refusal that describes nothing real. So the
assembler refuses a context a stage's gates cannot evaluate, instead of
letting the gates discover it one at a time.

THE REQUIREMENT MAP IS DERIVED, NOT REMEMBERED. It is read from the
runner's AST — which `ctx.<field>` each gate function actually touches —
because a hand-written mirror of another module goes stale the first time
that module changes. This project produced five instances of exactly that
in one day, so the map is computed rather than listed.

WHAT THIS MODULE DOES NOT DO. It does not gather `authority` or `prepared`:
those come from the real Development input, behind
`assert_real_run_allowed`, and a context assembler that reached for them
would be a second real-data read in a module the authorization gate does
not guard. The caller supplies them AFTER the gate lets it, and
`assert_complete(ctx, "B_DERIVE")` is what refuses if it did not.
"""

from __future__ import annotations

import ast
import io
import subprocess
from pathlib import Path

__all__ = ["ContextError", "required_fields", "assert_complete",
           "build_precheck_context"]

_RUNNER = Path(__file__).resolve().parent / "supplement_runner.py"

#: Fields whose legitimate value can be falsy, so "missing" must mean
#: `is None` and never "is falsy". `repo_dirty_paths=()` is a CLEAN
#: repository, which is the value the gate most wants to see.
_FALSY_IS_VALID = frozenset({"repo_dirty_paths", "frozen_hashes_ok"})


class ContextError(Exception):
    """The context cannot answer this stage's gates. Refuses; never fills in."""


def required_fields(stage: str) -> frozenset:
    """Every `ctx.<field>` the gates of `stage` actually read.

    Derived from `supplement_runner.py`'s AST. Reading the frozen file is
    fine; nothing here writes it."""
    from . import supplement_contract as sc

    if stage not in sc.GATE_TABLE:
        raise ContextError("%r is not a stage with a gate table" % stage)
    tree = ast.parse(io.open(_RUNNER, encoding="utf-8").read())
    defs = {n.name: n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)}
    wanted = {"_g_" + gate for gate in sc.GATE_TABLE[stage]}
    fields = set()
    seen = set()

    def _fields_of(name, visited):
        """`ctx.<field>` reads, FOLLOWING CALLS.

        WIDENED 2026-08-30, and the tripwire in
        `test_day_strata_context` is what caught it. The wired C_BUILD_1
        gates are one line each -- `_classify_c_build_1(ctx, "<gate>")` --
        so the `ctx.c_build_outcome` read lives one level down. A
        body-only walk reported that stage as needing NOTHING, which would
        have let `assert_complete` pass a context the gates then choked on.

        Third instance of this exact narrowness in one night (the builder
        code table and the mkdir scan were the others): a derivation that
        stops at the function boundary describes a fraction of what it
        claims to."""
        if name in visited or name not in defs:
            return set()
        visited.add(name)
        found = set()
        for inner in ast.walk(defs[name]):
            if (isinstance(inner, ast.Attribute)
                    and getattr(inner.value, "id", "") == "ctx"):
                found.add(inner.attr)
            if isinstance(inner, ast.Call):
                callee = getattr(inner.func, "id", None)
                # only follow a call that is HANDED the context; a helper
                # that never sees `ctx` cannot read a field off it.
                if callee and callee != name and any(
                        getattr(a, "id", None) == "ctx" for a in inner.args):
                    found |= _fields_of(callee, visited)
        return found

    for gate_fn in sorted(wanted):
        if gate_fn not in defs:
            continue
        seen.add(gate_fn)
        fields |= _fields_of(gate_fn, set())
    missing_gates = sorted(wanted - seen)
    if missing_gates:
        raise ContextError(
            "the gate table names %s but the runner defines no such "
            "function; the derivation would silently under-report what this "
            "stage needs" % missing_gates)
    return frozenset(fields)


def assert_complete(ctx, stage: str) -> None:
    """Refuse a context this stage's gates cannot evaluate.

    A gate handed `None` does not fail loudly — it evaluates whatever
    `None` makes its condition do and reports something that describes
    nothing. Refusing here names the missing field instead."""
    absent = []
    for field in sorted(required_fields(stage)):
        if not hasattr(ctx, field):
            absent.append("%s (no such field)" % field)
            continue
        value = getattr(ctx, field)
        if value is None and field not in _FALSY_IS_VALID:
            absent.append(field)
    if absent:
        raise ContextError(
            "%s cannot be evaluated: the context carries no %s. A gate "
            "handed None reports a verdict about nothing, so this refuses "
            "instead of letting each gate discover it separately."
            % (stage, ", ".join(absent)))


def build_precheck_context(*, supplement_id: str, utc_stamp: str,
                           repo_root: Path | None = None):
    """A context carrying everything A_PRECHECK's gates read.

    `authority` and `prepared` are deliberately left unset — see the module
    docstring. Call `assert_complete(ctx, "B_DERIVE")` after supplying them
    and it will refuse if you did not.

    Every value comes from ONE unambiguous source, named here so a reader
    can check the assembler did not invent a policy:

        g9_flag / second_copy_flag   itsf.guards
        runs_root / archive_root     itsf.contracts (the RULED roots)
        registry_text / chain        mc.registry_boundary — ONE read
        head_commit / dirty paths    git
        frozen_hashes_ok             guards.verify_frozen_hashes()
    """
    from .. import contracts, guards
    from . import registry_boundary as rb
    from .supplement_runner import GateContext

    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[3]

    snapshot, chain = rb.resolve_for_supplement(supplement_id)

    try:
        guards.verify_frozen_hashes()
        frozen_ok = True
    except Exception:                                          # noqa: BLE001
        frozen_ok = False

    return GateContext(
        supplement_id=supplement_id,
        head_commit=_git(root, "rev-parse", "HEAD"),
        registry_text=snapshot.text,
        runs_root=Path(contracts.RULED_RUNS_ROOT),
        archive_root=Path(contracts.RULED_ARCHIVE_ROOT),
        repo_dirty_paths=_dirty_paths(root),
        g9_flag=Path(guards.G9_FLAG),
        second_copy_flag=Path(guards.SECOND_COPY_FLAG),
        frozen_hashes_ok=frozen_ok,
        chain=chain,
        utc_stamp=utc_stamp,
    )


def _git(root: Path, *args) -> str:
    out = subprocess.run(["git", "-C", str(root), *args],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise ContextError("git %s failed: %s" % (" ".join(args),
                                                  out.stderr.strip()))
    return out.stdout.strip()


def _dirty_paths(root: Path) -> tuple:
    """`git status --porcelain` paths, as a tuple.

    An EMPTY tuple means clean, and that is a real answer — which is why
    `repo_dirty_paths` is in `_FALSY_IS_VALID`. Treating empty as "not
    supplied" would make a clean repository look like a missing field."""
    text = _git(root, "status", "--porcelain")
    return tuple(line[3:] for line in text.splitlines() if line.strip())
