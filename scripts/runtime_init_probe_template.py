# -*- coding: utf-8 -*-
"""Runtime-initialization boundary probe, shipped as
`probes/test_runtime_init_boundary.py`.

WHY THIS EXISTS. A previous delivery stopped a reviewer before any substantive
work because `GUARD_REPORT.json` recorded a refusal the reviewer could not
attribute to anything in the sealed surface. Two things had to change: the
refusal itself (a pinned runtime module was being refused while initialising
normally), and the reviewer's ability to tell a PRESCRIBED refusal from an
accident without taking the builder's word for it.

WHAT THIS PROBE ESTABLISHES, by making it happen rather than asserting it:

  * the same native resolution that is permitted inside a first runtime
    initialisation is REFUSED when this probe performs it -- the carve-out is
    an extent, not a permission for the event class;
  * every native resolution the policy did permit names the module that was
    initialising, the extent it happened in, the event and the resolved target;
  * every refusal the guard recorded is attributed to a sealed negative
    control that declared it in advance.

The third is the one that makes the other two checkable: if anything in this
run had been refused without a control prescribing it, that assertion fails
here and the runner exits non-zero, whether or not a library swallowed the
exception and let the session look successful.
"""
TEMPLATE = '''# -*- coding: utf-8 -*-
"""The native-resolution carve-out is an EXTENT, and every refusal is named.

Generated into the bundle by scripts/runtime_init_probe_template.py.
"""
import pytest

import code_review_bundle_guard as G

PRESCRIBED_BY = "probes/test_runtime_init_boundary.py"


def _guard():
    assert G.ACTIVE is not None, (
        "the guard is not armed -- this probe is only meaningful under "
        "run_bundle_tests.py, which arms it before importing pytest")
    return G.ACTIVE


def test_native_resolution_outside_a_runtime_initialisation_is_refused():
    """The negative control for the carve-out itself.

    `ctypes.dlopen` is permitted while a pinned runtime module runs its first
    normal initialisation. THIS call is made from probe code, with no
    initialisation open, so it must be refused -- otherwise the carve-out would
    be a permission for the event class rather than for an extent, and the
    whole `ctypes.*` family denial would be worth nothing.

    The library asked for is the same one the runtime itself resolves during
    initialisation, so the ONLY difference between the permitted case and this
    one is where execution is.
    """
    guard = _guard()
    guard.expect("ctypes.dlopen", contains="user32",
                 prescribed_by=PRESCRIBED_BY + "::"
                 "test_native_resolution_outside_a_runtime_initialisation"
                 "_is_refused",
                 why="a native resolution performed by probe code, with no "
                     "runtime initialisation open, must be refused")
    before = len(guard.denials)
    import ctypes
    with pytest.raises(G.BundleEscapeDenied):
        ctypes.WinDLL("user32")
    assert len(guard.denials) == before + 1, (
        "the resolution was not refused at the attempt")


def test_permitted_native_resolutions_name_what_permitted_them():
    """Provenance, not prose. Each permitted event carries the module that was
    initialising, the extent identity, the event and the resolved target -- so
    the reviewer can check the policy's own claim rather than read it."""
    guard = _guard()
    assert guard.policy is not None, "no runtime-initialization policy is armed"
    events = guard.policy.events
    assert events, (
        "no native resolution was permitted at all. That is not necessarily "
        "wrong, but it means this probe is measuring nothing -- report it")
    for record in events:
        for field in ("event", "lifecycle", "initializing_module",
                      "initializing_origin", "target"):
            assert record.get(field), (
                "a permitted native resolution is missing %r: %r"
                % (field, record))
        assert record["event"] in G.NATIVE_RESOLUTION_EVENTS
        assert record.get("executing_provenance") == G.RUNTIME
        assert record.get("permitted") is True


def test_every_refusal_so_far_is_attributed_to_a_prescribed_control():
    """The admission rule, stated as the property it protects.

    A refusal nothing prescribed is the failure this whole mechanism exists to
    surface: a library can catch it, substitute a fallback, and let every test
    pass while the review executes against something else. So an unattributed
    refusal fails here AND fails the runner, which does the same reconciliation
    after the session ends and exits non-zero on it.
    """
    guard = _guard()
    orphans = [r for r in guard.denial_records if not r["prescribed_by"]]
    assert not orphans, (
        "the guard refused something no sealed negative control prescribes: "
        "%r. Report this and STOP -- do not treat a passing test session as "
        "evidence that it did not matter" % (orphans[:3],))
'''


def render() -> str:
    return TEMPLATE
