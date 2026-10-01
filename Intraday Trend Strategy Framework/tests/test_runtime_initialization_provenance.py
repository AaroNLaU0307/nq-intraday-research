"""A native resolution is permitted for one extent only: a pinned runtime
module running its FIRST normal initialisation.

WHY THE EXTENT AND NOT THE EVENT. Denying the whole `ctypes.*` family refused
`ctypes.WinDLL('user32')` while the pinned runtime was initialising itself, and
`BundleEscapeDenied` is a `PermissionError` is an `OSError` is a `WindowsError`
-- which dateutil catches. The refusal was swallowed, a different timezone
backend was substituted, and every test still passed. So the failure this file
guards against is not "something was denied"; it is "something was denied, the
caller absorbed it, and the run looked fine".

The correction must not become a permission for the event class, which is what
every test below is really about: the same call is permitted in one place and
refused everywhere else, and the difference is mechanical -- where execution
is, what loaded the code on the stack, and where the library resolves to.

Everything runs against synthetic modules under a synthetic runtime root in
`tmp_path`. No real runtime, no real bundle and no real library is loaded.
"""
from __future__ import annotations

import importlib
import sys
import threading
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import code_review_bundle_guard as G                        # noqa: E402

RECORDER = "itsf_prov_recorder"


@pytest.fixture
def roots(tmp_path):
    """A synthetic runtime root, reviewed root and runner root."""
    runtime = tmp_path / "runtime"
    reviewed = tmp_path / "tree"
    runner = tmp_path / "runner"
    for path in (runtime, reviewed, runner):
        path.mkdir()
    (runtime / (RECORDER + ".py")).write_text("CALLS = []\n", encoding="utf-8")
    # A library the synthetic runtime "ships", so target validation can be
    # exercised without depending on this host's system directory.
    (runtime / "fakelib.dll").write_bytes(b"\x00")
    return runtime, reviewed, runner


@pytest.fixture
def policy(roots, monkeypatch):
    runtime, reviewed, runner = roots
    made = G.RuntimeInitPolicy(runtime_roots=(runtime,),
                               runner_roots=(runner,),
                               reviewed_roots=(reviewed,))
    made.install()
    monkeypatch.syspath_prepend(str(runtime))
    monkeypatch.syspath_prepend(str(reviewed))
    before = set(sys.modules)
    try:
        yield made
    finally:
        made.deactivate()
        for name in set(sys.modules) - before:
            sys.modules.pop(name, None)


def _module(root: Path, name: str, body: str) -> Path:
    path = root / (name + ".py")
    path.write_text(body, encoding="utf-8")
    return path


def _recorder():
    return importlib.import_module(RECORDER)


#: A module body that records what the policy sees while it is running.
WATCH = """
import %s as R
import code_review_bundle_guard as G
_p = G._ACTIVE_POLICY
_a = _p.active()
R.CALLS.append({
    "module": %%r,
    "depth": len(_p._stack()),
    "innermost": None if _a is None else _a.module,
    "eligible": None if _a is None else _a.eligible,
})
""" % RECORDER


# == 1-3. the extent is recognised, and it ends both ways ==================

def test_1_a_first_runtime_initialisation_is_recognised(policy, roots):
    """The extent exists WHILE the module body runs, names that module, and is
    marked eligible -- all observed from inside the initialisation rather than
    reconstructed afterwards."""
    runtime, _, _ = roots
    _module(runtime, "prov_one", WATCH % "prov_one")
    importlib.import_module("prov_one")
    seen = _recorder().CALLS[-1]
    assert seen["innermost"] == "prov_one"
    assert seen["eligible"] is True
    assert seen["depth"] >= 1


def test_2_the_extent_ends_when_the_loader_returns(policy, roots):
    runtime, _, _ = roots
    _module(runtime, "prov_two", WATCH % "prov_two")
    importlib.import_module("prov_two")
    assert policy.active() is None
    assert policy._stack() == []


def test_3_the_extent_ends_when_the_loader_RAISES(policy, roots):
    """The case a `try/finally` exists for. An extent left open by a failed
    import would keep permitting native resolutions for the rest of the run --
    from code that has nothing to do with the module that failed."""
    runtime, _, _ = roots
    _module(runtime, "prov_three", "raise RuntimeError('initialisation failed')")
    with pytest.raises(RuntimeError):
        importlib.import_module("prov_three")
    assert policy.active() is None
    assert policy._stack() == []


# == 4-5. one chance per module key ========================================

def test_4_a_second_attempt_after_SUCCESS_is_not_a_first_initialisation(
        policy, roots):
    runtime, _, _ = roots
    _module(runtime, "prov_four", WATCH % "prov_four")
    importlib.import_module("prov_four")
    sys.modules.pop("prov_four")
    importlib.import_module("prov_four")
    first, second = _recorder().CALLS[-2:]
    assert first["eligible"] is True
    assert second["eligible"] is False


def test_4_a_second_attempt_after_a_RAISE_is_not_a_first_initialisation(
        policy, roots):
    """The reason the set is keyed on ATTEMPTED rather than COMPLETED. A
    completion-keyed set would hand a second eligible extent to exactly the
    module whose first attempt failed -- the one case where a retry is most
    likely to be someone else's idea rather than the import system's."""
    runtime, _, _ = roots
    _module(runtime, "prov_five",
            "raise RuntimeError('first attempt fails')\n")
    with pytest.raises(RuntimeError):
        importlib.import_module("prov_five")
    assert policy.attempted("prov_five")
    _module(runtime, "prov_five", WATCH % "prov_five")
    sys.modules.pop("prov_five", None)
    importlib.invalidate_caches()
    importlib.import_module("prov_five")
    assert _recorder().CALLS[-1]["eligible"] is False


def test_5_a_reload_is_not_a_first_initialisation(policy, roots):
    runtime, _, _ = roots
    _module(runtime, "prov_six", WATCH % "prov_six")
    module = importlib.import_module("prov_six")
    importlib.reload(module)
    first, second = _recorder().CALLS[-2:]
    assert first["eligible"] is True
    assert second["eligible"] is False


def test_5_calling_into_an_initialised_module_later_is_not_an_extent(
        policy, roots):
    """Ordinary use of a runtime module, after it is loaded, carries no extent
    at all -- so a native resolution from there is judged with nothing active."""
    runtime, _, _ = roots
    _module(runtime, "prov_seven", "def later():\n    return True\n")
    module = importlib.import_module("prov_seven")
    assert module.later() is True
    assert policy.active() is None


# == 6-7. nesting, and threads =============================================

def test_6_nested_first_initialisations_nest(policy, roots):
    """An import inside an import: both extents are eligible, the inner one is
    innermost while it runs, and the outer one is innermost again afterwards."""
    runtime, _, _ = roots
    _module(runtime, "prov_inner", WATCH % "prov_inner")
    _module(runtime, "prov_outer",
            (WATCH % "prov_outer_before") + "\nimport prov_inner\n"
            + (WATCH % "prov_outer_after"))
    importlib.import_module("prov_outer")
    before, inner, after = _recorder().CALLS[-3:]
    assert before["innermost"] == "prov_outer" and before["depth"] == 1
    assert inner["innermost"] == "prov_inner" and inner["depth"] == 2
    assert inner["eligible"] is True
    assert after["innermost"] == "prov_outer" and after["depth"] == 1


def test_7_another_thread_inherits_no_active_extent(policy, roots):
    """Thread-local, stated as the thing that would go wrong otherwise: a
    thread started during an initialisation must not be able to resolve native
    libraries under someone else's extent."""
    runtime, _, _ = roots
    seen = {}

    def watcher():
        seen["active"] = policy.active()
        seen["depth"] = len(policy._stack())

    _module(runtime, "prov_thread", "")
    body = (
        "import threading\n"
        "import %s as R\n"
        "import code_review_bundle_guard as G\n"
        "R.CALLS.append({'module': 'prov_thread_host',\n"
        "                'depth': len(G._ACTIVE_POLICY._stack()),\n"
        "                'innermost': G._ACTIVE_POLICY.active().module,\n"
        "                'eligible': True})\n"
        "t = threading.Thread(target=R.WATCHER)\n"
        "t.start(); t.join()\n" % RECORDER)
    recorder = _recorder()
    recorder.WATCHER = watcher
    _module(runtime, "prov_thread_host", body)
    importlib.import_module("prov_thread_host")
    assert recorder.CALLS[-1]["innermost"] == "prov_thread_host"
    assert seen["active"] is None, (
        "the new thread saw an extent it did not open")
    assert seen["depth"] == 0


# == 8. provenance comes from load origin, never from a name ===============

def test_8_provenance_is_decided_by_where_code_was_loaded_from(policy, roots):
    runtime, reviewed, runner = roots
    assert policy.provenance(str(runtime / "x.py")) == G.RUNTIME
    assert policy.provenance(str(reviewed / "x.py")) == G.REVIEWED
    assert policy.provenance(str(runner / "x.py")) == G.RUNNER
    assert policy.provenance(str(Path(runtime).parent / "elsewhere.py")) \
        == G.UNREGISTERED


def test_8_generated_and_unregistered_code_acquires_no_provenance(policy):
    """`exec`-ed and `compile`-ed code, and anything else with no location, is
    UNREGISTERED. A module that calls itself something is not thereby a runtime
    module: the name is supplied by the code being classified."""
    for filename in ("<string>", "<stdin>", "<frozen some.other.thing>", ""):
        assert policy.provenance(filename) == G.UNREGISTERED


def test_8_the_import_machinery_itself_counts_as_runtime(policy):
    """The frozen bootstrap runs between a wrapped loader and the module it is
    executing, so it has to be classified -- and it is the interpreter's own
    import machinery. The filenames are read off the machinery's code objects
    rather than written down here."""
    for filename in G._import_machinery_files():
        assert policy.provenance(filename) == G.RUNTIME
    assert G._import_machinery_files(), "the machinery was not identified"


def test_8_reviewed_code_running_inside_an_extent_breaks_the_chain(
        policy, roots):
    """The hole a frame-by-frame walk closes. Being INSIDE a runtime
    initialisation is not enough: if reviewed code is on the stack between the
    event and the extent, the resolution is refused."""
    runtime, reviewed, _ = roots
    _module(reviewed, "prov_reviewed_helper",
            "import code_review_bundle_guard as G\n"
            "import sys\n"
            "def resolve():\n"
            "    p = G._ACTIVE_POLICY\n"
            "    return p.judge('ctypes.dlopen', ('fakelib',),"
            " sys._getframe())\n")
    _module(runtime, "prov_host",
            "import %s as R\n"
            "import prov_reviewed_helper as H\n"
            "R.CALLS.append(H.resolve())\n" % RECORDER)
    importlib.import_module("prov_host")
    permitted, record = _recorder().CALLS[-1]
    assert permitted is False
    assert "REVIEWED" in record["refused"]


# == 9-10. the carve-out is an extent, not an event permission =============

def test_9_a_resolution_inside_a_first_initialisation_is_permitted(
        policy, roots):
    """The case the whole model exists to allow -- and the four things that
    have to be true at once for it."""
    runtime, _, _ = roots
    _module(runtime, "prov_permit",
            "import %s as R\n"
            "import sys\n"
            "import code_review_bundle_guard as G\n"
            "R.CALLS.append(G._ACTIVE_POLICY.judge("
            "'ctypes.dlopen', ('fakelib',), sys._getframe()))\n" % RECORDER)
    importlib.import_module("prov_permit")
    permitted, record = _recorder().CALLS[-1]
    assert permitted is True
    assert record["initializing_module"] == "prov_permit"
    assert record["executing_provenance"] == G.RUNTIME
    assert record["lifecycle"]
    assert record["target"].endswith("fakelib.dll")
    assert record["event"] == "ctypes.dlopen"


def test_10_the_same_resolution_outside_any_extent_is_refused(policy):
    permitted, record = policy.judge("ctypes.dlopen", ("fakelib",),
                                     sys._getframe())
    assert permitted is False
    assert "no runtime initialisation is active" in record["refused"]


def test_10_a_resolution_inside_an_INELIGIBLE_extent_is_refused(policy, roots):
    """A reviewed module's initialisation is an extent too -- an ineligible
    one. The innermost extent is the one that counts, so an outer eligible
    runtime initialisation does not reach past it."""
    runtime, reviewed, _ = roots
    _module(reviewed, "prov_reviewed_mod",
            "import %s as R\n"
            "import sys\n"
            "import code_review_bundle_guard as G\n"
            "R.CALLS.append(G._ACTIVE_POLICY.judge("
            "'ctypes.dlopen', ('fakelib',), sys._getframe()))\n" % RECORDER)
    _module(runtime, "prov_outer_runtime", "import prov_reviewed_mod\n")
    importlib.import_module("prov_outer_runtime")
    permitted, record = _recorder().CALLS[-1]
    assert permitted is False
    assert "not a first normal RUNTIME initialisation" in record["refused"]


def test_10_a_target_outside_the_approved_locations_is_refused(policy, roots):
    """Being inside the extent is not enough either: the library must resolve
    into the runtime tree or a protected system location, and a name that
    resolves nowhere is refused rather than assumed harmless."""
    runtime, _, _ = roots
    _module(runtime, "prov_target",
            "import %s as R\n"
            "import sys\n"
            "import code_review_bundle_guard as G\n"
            "R.CALLS.append(G._ACTIVE_POLICY.judge("
            "'ctypes.dlopen', ('not_a_real_library',), sys._getframe()))\n"
            % RECORDER)
    importlib.import_module("prov_target")
    permitted, record = _recorder().CALLS[-1]
    assert permitted is False
    assert "does not resolve" in record["refused"]


# == 11-12. prescribed refusals, and the admission rule ====================

def _guard(tmp_path):
    return G.Guard(tmp_path, runtime_roots=(tmp_path / "no-runtime",))


def test_11_a_prescribed_refusal_is_attributed_to_the_control(tmp_path):
    """The O4D negative control's shape: declared first, caused second,
    attributed third."""
    guard = _guard(tmp_path)
    guard.expect("open", contains="o4d_escape_probe.tmp",
                 prescribed_by="probes/test_o4d_write_boundary.py::x",
                 why="a write outside the bundle must be refused")
    with pytest.raises(G.BundleEscapeDenied):
        guard("open", (str(tmp_path.parent / "o4d_escape_probe.tmp"), "wb"))
    reconciled = guard.reconcile()
    assert len(reconciled["expected_denials"]) == 1
    assert reconciled["expected_denials"][0]["prescribed_by"].startswith(
        "probes/test_o4d_write_boundary.py")
    assert reconciled["unexpected_denials"] == []
    assert reconciled["missing_prescribed_denials"] == []


@pytest.mark.parametrize("event,target", [
    ("open", "some_other_file.tmp"),          # right event, wrong target
    ("os.mkdir", "o4d_escape_probe.tmp"),     # right target, wrong event
])
def test_11_a_declaration_does_not_absorb_a_DIFFERENT_refusal(tmp_path, event,
                                                              target):
    """A declaration that matched loosely would quietly launder the next
    accident that happened to look similar."""
    guard = _guard(tmp_path)
    guard.expect("open", contains="o4d_escape_probe.tmp",
                 prescribed_by="probes/test_o4d_write_boundary.py::x",
                 why="...")
    with pytest.raises(G.BundleEscapeDenied):
        guard(event, (str(tmp_path.parent / target), "wb"))
    reconciled = guard.reconcile()
    assert len(reconciled["unexpected_denials"]) == 1
    assert len(reconciled["missing_prescribed_denials"]) == 1


def test_12_an_unattributed_refusal_fails_the_run(tmp_path):
    """Even when the test session itself reported success. That is the
    distinction the previous delivery could not make: a library caught the
    refusal, the session passed, and the run looked clean."""
    guard = _guard(tmp_path)
    with pytest.raises(G.BundleEscapeDenied):
        guard("open", (str(tmp_path.parent / "stray.tmp"), "wb"))
    code, reconciled = G.admission_exit_code(guard, 0)
    assert code == 98
    assert len(reconciled["unexpected_denials"]) == 1


def test_12_a_prescribed_refusal_that_never_happened_fails_the_run(tmp_path):
    """The quieter failure: the control stopped controlling, so the property it
    was there to establish is no longer established by anything."""
    guard = _guard(tmp_path)
    guard.expect("open", contains="never_caused.tmp",
                 prescribed_by="probes/somewhere.py::y", why="...")
    code, reconciled = G.admission_exit_code(guard, 0)
    assert code == 98
    assert len(reconciled["missing_prescribed_denials"]) == 1


def test_12_a_clean_run_keeps_its_exit_code(tmp_path):
    """The control for the two above: with every refusal attributed and every
    declaration matched, the admission rule changes nothing."""
    guard = _guard(tmp_path)
    guard.expect("open", contains="o4d_escape_probe.tmp",
                 prescribed_by="probes/test_o4d_write_boundary.py::x",
                 why="...")
    with pytest.raises(G.BundleEscapeDenied):
        guard("open", (str(tmp_path.parent / "o4d_escape_probe.tmp"), "wb"))
    assert G.admission_exit_code(guard, 0)[0] == 0
    assert G.admission_exit_code(guard, 5)[0] == 5
