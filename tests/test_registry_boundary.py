"""The single validation boundary for `ops/TRIAL_REGISTRY.md`.

C2 of `MC-REG-COLLISION-001`, as modified and ratified by a fresh Sol
session on 2026-08-25, requires TWO tests and names them:

  * an architecture / no-bypass test — no production code reads that path
    or calls either resolver outside the boundary, except unconditional-
    refusal stubs;
  * a behavioural test — one read, both lifecycles against the identical
    immutable snapshot, and a refusal from either leaving nothing usable.

Both live here. The no-bypass half is the one that decays silently: an
allowlist entry outlives the reason it was added, so every entry on it is
proved to refuse by CALLING it, never by declaring it.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from itsf.mc import registry_boundary as rb

SRC = Path(__file__).resolve().parent.parent / "src" / "itsf"

#: Names that resolve a lifecycle over the registry. Calling any of these
#: from production code outside the boundary is what C2 forbids.
_RESOLVERS = frozenset({
    "resolve_supplement_chains", "resolve_supplement_chain", "resolve_chain",
    "resolve_supplement_chains_or_raise", "find_live_authorization",
    "resolve_mc_chains", "find_live_mc_authorization",
})
_READS = frozenset({"read_text", "read_bytes"})

#: The modules allowed to touch either, and WHY. `registry_boundary` is the
#: boundary; the two grammar modules DEFINE the resolvers and are consumed
#: through it.
_BOUNDARY_MODULES = frozenset({
    "registry_boundary", "supplement_registry", "mc_registry",
})

#: C2's only exception: functions incapable of returning authorization,
#: readiness, or a usable chain. Each is proved below by calling it.
_REFUSAL_STUBS = (
    ("itsf.mc.day_strata_supplement", "authorize_supplement", ("",)),
    ("itsf.mc.day_strata_supplement", "run_supplement_production", ()),
    ("itsf.mc.consumer", "authorize_real_mc", ("",)),
    ("itsf.mc.consumer", "run_real_mc", ()),
    ("itsf.mc.real_input", "prepare_real_mc_input", ()),
)
_STUB_MODULES = frozenset(m.rsplit(".", 1)[-1] for m, _f, _a in _REFUSAL_STUBS)


def _module_facts(path: Path):
    """Non-docstring registry mentions, read calls and resolver calls."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))

    names, reads, resolvers = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings \
                and "TRIAL_REGISTRY" in node.value:
            names.append(node.value)
        if isinstance(node, ast.Call):
            fn = node.func
            called = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else "")
            if called in _READS:
                reads.append(called)
            if called in _RESOLVERS:
                resolvers.append(called)
    return names, reads, resolvers


# ===========================================================================
# 1 — architecture / no bypass
# ===========================================================================

def test_no_production_module_resolves_the_registry_outside_the_boundary():
    """C2, stated as the property rather than as an inventory of today's
    call sites. An inventory silently excludes the paths N13 creates."""
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        stem = path.stem
        if stem in _BOUNDARY_MODULES:
            continue
        _names, _reads, resolvers = _module_facts(path)
        if resolvers and stem not in _STUB_MODULES:
            offenders.append(f"{path.relative_to(SRC.parent.parent)}: calls "
                             f"{sorted(set(resolvers))}")
    assert not offenders, (
        "production code resolves the registry outside "
        "registry_boundary:\n  " + "\n  ".join(offenders))


def test_no_production_module_reads_the_registry_path_outside_the_boundary():
    """A second read of a MUTABLE shared file is the exact loophole Sol
    rewrote C2 to close: MC validation could pass on one version while
    supplement resolution acted on another."""
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        stem = path.stem
        if stem in _BOUNDARY_MODULES or stem in _STUB_MODULES:
            continue
        names, reads, _resolvers = _module_facts(path)
        if names and reads:
            offenders.append(
                f"{path.relative_to(SRC.parent.parent)}: names the registry "
                f"{names[:1]} and reads ({sorted(set(reads))})")
    assert not offenders, (
        "production code reads ops/TRIAL_REGISTRY.md outside "
        "registry_boundary:\n  " + "\n  ".join(offenders))


@pytest.mark.parametrize("module,func,args", _REFUSAL_STUBS,
                         ids=[f"{m.rsplit('.', 1)[-1]}.{f}"
                              for m, f, _a in _REFUSAL_STUBS])
def test_every_allowlisted_stub_actually_refuses(module, func, args):
    """C2's exception is "incapable of returning authorization, readiness,
    or a usable chain" — a behavioural property, so it is proved
    behaviourally.

    An allowlist entry that is merely declared outlives the reason it was
    added. This one cannot: the day any of these stops raising, it stops
    qualifying for the exception and this test says so."""
    import importlib

    fn = getattr(importlib.import_module(module), func)
    with pytest.raises(Exception) as ei:
        fn(*args)
    assert not isinstance(ei.value, AssertionError), (
        f"{module}.{func} raised AssertionError — that is a bug escaping, "
        "not a governed refusal")


def test_the_runner_obtains_its_chain_through_the_boundary():
    """`supplement_runner` is the one production path C2 names explicitly."""
    import inspect

    from itsf.mc import supplement_runner as sr

    src = inspect.getsource(sr.run_supplement_production)
    assert "registry_boundary" in src
    assert "resolve_for_supplement" in src


def test_every_gate_context_takes_registry_text_and_chain_from_ONE_read():
    """THE LIVE FORM. This test used to assert the obligation was VACUOUS —
    no production code built a `GateContext` at all — and its own docstring
    said what to do when that stopped being true:

        "WHEN THE EXECUTION PATH IS BUILT this test will fail, and the
         correct response is NOT to delete it. It is to replace the
         assertion with the live one: `GateContext.registry_text` must be
         `snapshot.text` from the same boundary call that produced
         `GateContext.chain` — one read, one snapshot, both fields."

    2026-08-29: `mc/day_strata_context.build_precheck_context` became the
    first production constructor, the test went red, and this is that
    replacement. The tripwire worked — it fired at exactly the moment the
    obligation became real, which is the only moment anyone would have
    thought to check.

    Building a `GateContext` from a SECOND read would reintroduce the
    split-snapshot defect C2 was rewritten to close: two reads of one
    mutable file can disagree, and then the chain a gate refuses on is not
    the registry the run recorded.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            builds = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                      and (getattr(n.func, "attr", None) == "GateContext"
                           or getattr(n.func, "id", None) == "GateContext")]
            if not builds:
                continue
            where = f"{path.relative_to(SRC.parent.parent)}:{fn.lineno} {fn.name}"

            # ONE boundary call in this function, unpacked into two names.
            resolves = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                        and getattr(n.func, "attr", "") == "resolve_for_supplement"]
            if len(resolves) != 1:
                offenders.append(
                    f"{where}: {len(resolves)} resolve_for_supplement call(s); "
                    "exactly one is required so both fields come from the "
                    "same snapshot")
                continue
            bound = None
            for node in ast.walk(fn):
                if (isinstance(node, ast.Assign)
                        and node.value in resolves
                        and isinstance(node.targets[0], ast.Tuple)):
                    bound = [getattr(e, "id", "") for e in node.targets[0].elts]
            if not bound or len(bound) != 2:
                offenders.append(
                    f"{where}: the boundary call's result is not unpacked "
                    "into (snapshot, chain)")
                continue
            snap_name, chain_name = bound

            for call in builds:
                got = {kw.arg: kw.value for kw in call.keywords}
                text = got.get("registry_text")
                chain = got.get("chain")
                text_ok = (isinstance(text, ast.Attribute)
                           and getattr(text.value, "id", "") == snap_name
                           and text.attr == "text")
                chain_ok = (isinstance(chain, ast.Name)
                            and chain.id == chain_name)
                if not (text_ok and chain_ok):
                    offenders.append(
                        f"{where}: GateContext at line {call.lineno} does not "
                        f"take registry_text from {snap_name}.text AND chain "
                        f"from {chain_name}")
    assert not offenders, (
        "a GateContext is built from something other than one boundary "
        "read:" + '\n  ' + '\n  '.join(offenders)
        + '\n\n' + "Two reads of one mutable file can disagree, and "
          "then the chain a gate refuses on is not the registry the run "
          "recorded.")


def test_the_live_form_is_actually_looking_at_something():
    """The replacement's own vacuity guard. The test above passes trivially
    if no production code builds a GateContext — which was TRUE until
    2026-08-29 and is what the previous form asserted. If that becomes true
    again, this says so instead of reporting clean."""
    constructors = 0
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            fn = getattr(node, "func", None)
            name = (getattr(fn, "attr", None) or getattr(fn, "id", None)
                    if isinstance(node, ast.Call) else None)
            if name == "GateContext":
                constructors += 1
    assert constructors >= 1, (
        "no production code builds a GateContext any more, so the check "
        "above passes over nothing. Either restore the constructor or put "
        "back the vacuous form with its inversion note.")


# ===========================================================================
# 2 — behaviour: one read, one snapshot, either refusal is total
# ===========================================================================

def _snapshot(text: str) -> rb.RegistrySnapshot:
    return rb.RegistrySnapshot(
        text=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source="<in-memory>")


def test_one_mediation_performs_exactly_one_read(tmp_path, monkeypatch):
    """Not "few reads" — one. Two reads of a mutable file is the defect."""
    target = tmp_path / "TRIAL_REGISTRY.md"
    target.write_text("| # | utc | event | commit | actor | note |\n",
                      encoding="utf-8")

    calls = []
    real = rb._read_text
    monkeypatch.setattr(rb, "_read_text",
                        lambda p: (calls.append(p), real(p))[1])

    resolution = rb.resolve_registry(target)
    assert len(calls) == 1, f"{len(calls)} reads, expected exactly 1"
    assert resolution.usable


def test_both_lifecycles_receive_the_identical_snapshot(monkeypatch):
    """Same object identity of the text, not merely equal strings."""
    from itsf.mc import mc_registry as mr
    from itsf.mc import supplement_registry as sr

    seen = {}
    monkeypatch.setattr(sr, "resolve_supplement_chains",
                        lambda t: (seen.setdefault("sup", t), ({}, None))[1])
    monkeypatch.setattr(mr, "resolve_mc_chains",
                        lambda t: (seen.setdefault("mc", t), ({}, None))[1])

    snap = _snapshot("| # | utc | event | commit | actor | note |\n")
    rb.mediate(snap)
    assert seen["sup"] is seen["mc"] is snap.text


def test_an_mc_refusal_makes_a_perfectly_good_supplement_chain_unusable():
    """THE CROSS-LIFECYCLE COUPLING, and the reason C2 exists.

    The supplement chain here resolves on its own. It is unusable anyway,
    because the MC record over the same bytes is broken — a registry whose
    governance record is broken is one nobody gets to act on."""
    from itsf.mc import supplement_registry as sr
    from test_mc_supplement_registry import C1, Reg, SID, UTC

    reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
    reg.raw(f"| 4 | {UTC} | **MC_RUN_AUTHORIZEDD** | {C1} | Aaron "
            f"| [MC-R001] run_id: MC-R001 |")
    text = reg.text()

    chains, refusal = sr.resolve_supplement_chains(text)
    assert refusal is None and chains, "the supplement side is fine alone"

    resolution = rb.mediate(_snapshot(text))
    assert not resolution.usable
    assert resolution.refusing_lifecycle == "mc"
    assert resolution.supplement_chains == {} and resolution.mc_chains == {}

    chain = rb.supplement_chain(resolution, SID)
    assert chain.problem, "the MC refusal must reach the supplement caller"
    assert "[mc]" in chain.problem
    assert chain.live_authorizations == ()


def test_a_supplement_refusal_is_equally_total():
    from test_mc_supplement_registry import C1, Reg, SID, UTC

    reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
    reg.raw(f"| 4 | {UTC} | **SUPPLEMENT_NOT_A_REAL_TOKEN** | {C1} "
            f"| main agent | [{SID}] schema: x |")
    resolution = rb.mediate(_snapshot(reg.text()))
    assert not resolution.usable
    assert resolution.refusing_lifecycle == "supplement"
    assert resolution.supplement_chains == {} and resolution.mc_chains == {}


def test_a_refused_resolution_cannot_be_constructed_carrying_chains():
    """The constructor enforces it rather than trusting callers to check.
    "The caller will check" is how a refused resolution becomes an action."""
    snap = _snapshot("")
    with pytest.raises(rb.BoundaryError):
        rb.MediatedResolution(snapshot=snap, supplement_chains={"a": 1},
                              refusal="something", refusing_lifecycle="mc")
    with pytest.raises(rb.BoundaryError):
        rb.MediatedResolution(snapshot=snap, refusal="something",
                              refusing_lifecycle="")
    with pytest.raises(rb.BoundaryError):
        rb.MediatedResolution(snapshot=snap, refusing_lifecycle="mc")


def test_a_resolver_that_explodes_becomes_a_refusal_not_an_exception():
    """An exception a caller might catch and read as "no problem found" is
    the failure this subsystem exists to prevent."""
    from itsf.mc import mc_registry as mr

    def boom(_text):
        raise RuntimeError("resolver exploded")

    import unittest.mock as _m
    with _m.patch.object(mr, "resolve_mc_chains", boom):
        resolution = rb.mediate(_snapshot(""))
    assert not resolution.usable
    assert resolution.refusing_lifecycle == "mc"
    assert "mc_resolver_internal_error" in resolution.refusal


def test_the_snapshot_records_which_bytes_a_decision_was_taken_against():
    text = "| # | utc | event | commit | actor | note |\n"
    snap = rb.read_snapshot.__wrapped__(None) if hasattr(
        rb.read_snapshot, "__wrapped__") else _snapshot(text)
    assert snap.sha256 == hashlib.sha256(
        snap.text.encode("utf-8")).hexdigest()
    assert snap.n_bytes == len(snap.text.encode("utf-8"))


def test_the_boundary_carries_its_ruling_provenance():
    assert "MC_REG_COLLISION_001" in rb.BOUNDARY_RULING
    assert rb.BOUNDARY_RULING_DELEGATED is True
    assert rb.mediate(_snapshot("")).delegated is True
