"""THE HOST CHECK, and the exact limit of what it claims.

MC-R001 ran 39h52m and was destroyed by a Windows Update planned restart.
Nothing had looked at the host. This check refuses to START a multi-day run
on a machine that is ALREADY waiting to restart -- and that is all it does.
The tests below pin both halves: the refusal that exists, and the claim that
must never be made for it.

No real MC is executed here, no registry key is written, and every registry
read is replaced by an injected probe.
"""
import pytest

from itsf import host_preflight as hp


def _probe(present=(), values=None):
    """A stand-in for the two registry readers. The ONLY thing injected --
    every decision the check makes is the production one."""
    present = set(present)
    values = dict(values or {})
    return (lambda path: path in present,
            lambda path, name: values.get((path, name)))


CBS = REBOOT_KEYS = dict(hp.REBOOT_PENDING_KEYS and
                         {n: p for n, p in hp.REBOOT_PENDING_KEYS})


# == the refusal ==========================================================

@pytest.mark.parametrize("marker", sorted(REBOOT_KEYS))
def test_a_pending_reboot_marker_refuses(marker):
    """Both servicing markers are set BEFORE the restart they are waiting
    for, so a run started on top of one is started on a countdown."""
    exists, value = _probe(present=[REBOOT_KEYS[marker]])
    with pytest.raises(hp.HostNotFitError) as ei:
        hp.assert_host_fit_for_long_run(key_exists=exists, value=value)
    assert ei.value.code == "host_reboot_pending"
    assert marker in str(ei.value)


def test_a_clean_host_passes_and_returns_its_context():
    exists, value = _probe()
    context = hp.assert_host_fit_for_long_run(key_exists=exists, value=value)
    assert context["pending_reboot_markers"] == ()


def test_both_markers_are_named_when_both_are_present():
    """A refusal that named only the first would hide half the reason."""
    exists, value = _probe(present=list(REBOOT_KEYS.values()))
    with pytest.raises(hp.HostNotFitError) as ei:
        hp.assert_host_fit_for_long_run(key_exists=exists, value=value)
    for marker in REBOOT_KEYS:
        assert marker in str(ei.value)


# == what is deliberately NOT a refusal ===================================

def test_pending_file_renames_alone_do_not_refuse():
    """`PendingFileRenameOperations` is set by ordinary installers for
    renames that merely happen to complete at a restart. On a developer
    machine it is close to always present, so refusing on it would make the
    check fire constantly -- and a check that always fires is a check people
    route around. It is reported instead."""
    exists, value = _probe(values={
        (hp._SESSION_MANAGER, "PendingFileRenameOperations"): ["a", "b"]})
    context = hp.assert_host_fit_for_long_run(key_exists=exists, value=value)
    assert context["pending_file_rename_operations"] is True


def test_active_hours_span_is_reported_as_arithmetic_not_assurance():
    """Windows caps Active Hours at 18 hours, so it cannot cover a 40-hour
    run however it is set. The span is computed and surfaced so that fact is
    visible rather than assumed -- the machine that lost MC-R001 had a
    15-hour window and restarted in the gap."""
    exists, value = _probe(values={
        (hp._WU_UX_SETTINGS, "ActiveHoursStart"): 14,
        (hp._WU_UX_SETTINGS, "ActiveHoursEnd"): 5})
    context = hp.host_context(exists, value)
    assert context["active_hours_span_hours"] == 15
    assert context["active_hours_start"] == 14
    assert context["active_hours_end"] == 5


def test_a_host_with_no_windows_registry_does_not_crash():
    """The production readers return None/False off Windows rather than
    raising, so the check degrades to 'nothing known' instead of breaking a
    launch on a platform it cannot inspect."""
    assert hp._hklm_key_exists("nonexistent") in (True, False)
    context = hp.host_context()
    assert "pending_reboot_markers" in context


# == the claim that must never be made ====================================

def test_the_module_states_that_it_cannot_prevent_a_restart():
    """THE property this file exists to protect.

    The check detects a restart that is already pending. It cannot stop
    Windows from restarting, and describing it as protection would be the
    exact mistake that makes an operator trust a 40-hour run to it. The
    docstring is the contract, so the contract is asserted.
    """
    text = hp.__doc__ or ""
    assert "CANNOT PREVENT A RESTART" in text
    assert "never" in text.lower()


# == the entry binds it, before anything expensive ========================

def test_the_entry_runs_the_preflight_before_the_gate_and_the_bundle():
    """Order is the point: the host is checked before the launch gate, the
    authorization and any byte of the bundle, so an unfit host costs
    nothing."""
    import inspect
    import scripts.mc_real_run as entry

    body = inspect.getsource(entry.main)
    assert "assert_host_fit_for_long_run" in body
    assert body.index("assert_host_fit_for_long_run") < \
        body.index("assert_real_run_allowed()")
    assert body.index("assert_host_fit_for_long_run") < \
        body.index("precheck_bundle_on_disk")


def test_the_entry_refuses_with_its_own_exit_code(monkeypatch):
    """A refusal here is distinguishable from every other refusal the entry
    can make -- 2 (no root), 3 (commit mismatch), 4 (wrong root), 5 (host)."""
    import scripts.mc_real_run as entry
    from itsf.mc import real_input as ri

    def refuse():
        raise hp.HostNotFitError("host_reboot_pending", "injected")

    monkeypatch.setattr(hp, "assert_host_fit_for_long_run", refuse)
    assert entry.main(bundle_root=str(ri.SEALED_RUN_DIR)) == 5


def test_no_real_mc_is_executed_by_this_module():
    """Pinned at the source level: nothing here reaches the runner."""
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    called = {n.func.attr if isinstance(n.func, ast.Attribute)
              else getattr(n.func, "id", "")
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "execute_full_mc" not in called
    assert "run_epistemic" not in called
