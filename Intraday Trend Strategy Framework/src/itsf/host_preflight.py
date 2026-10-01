"""IS THIS HOST FIT TO START A MULTI-DAY GOVERNED RUN?

WHY THIS EXISTS. MC-R001 ran 39h52m of substantive computation and was then
destroyed by a Windows Update planned restart (System event 1074,
MoUsoCoreWorker, "Operating System: Service pack (Planned)"). It had no
durable checkpoint, so the entire run was lost. Nothing in the repository
had looked at the host before spending two days on it.

WHAT THIS CAN AND CANNOT DO, stated plainly because the distinction is the
whole point:

  IT CAN detect that Windows is ALREADY waiting to restart. Those markers
  are set before the restart happens, so a run started on top of one is a
  run started on a countdown.

  IT CANNOT PREVENT A RESTART. Nothing in a Python process can. Windows
  Update decides when to restart, and on this edition the only Owner-side
  controls are Active Hours (an 18-hour maximum window, which cannot cover a
  40-hour run) and Pause Updates. A clean preflight means "no restart is
  pending right now", never "no restart will happen".

So this refuses on the evidence it has and reports the rest as context for
the Owner. It does not pretend the remaining risk is gone, and it must never
be described as protection.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping


class HostNotFitError(RuntimeError):
    """The host is already waiting to restart. Raised before a long run."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


#: REGISTRY KEYS WHOSE MERE EXISTENCE MEANS "Windows is waiting to restart".
#: Both are set by the servicing stack before the restart it is waiting for,
#: which is why their presence is a hard refusal rather than a note.
REBOOT_PENDING_KEYS = (
    ("component_based_servicing",
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing"
     r"\RebootPending"),
    ("windows_update_reboot_required",
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update"
     r"\RebootRequired"),
)

#: ADVISORY ONLY, and deliberately not a refusal. `PendingFileRenameOperations`
#: is set by ordinary installers for renames that merely HAPPEN to need a
#: restart to complete, and on a developer machine it is close to always
#: present. Refusing on it would make the check fire constantly, and a check
#: that always fires is a check people route around.
_SESSION_MANAGER = r"SYSTEM\CurrentControlSet\Control\Session Manager"
_WU_UX_SETTINGS = r"SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"


def _hklm_key_exists(path: str) -> bool:
    try:
        import winreg
    except ImportError:                                     # not Windows
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path):
            return True
    except OSError:
        return False


def _hklm_value(path: str, name: str):
    try:
        import winreg
    except ImportError:                                     # not Windows
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def pending_reboot_markers(key_exists=_hklm_key_exists) -> tuple:
    """The names of every HARD marker currently present. Empty is clean."""
    return tuple(name for name, path in REBOOT_PENDING_KEYS
                 if key_exists(path))


def host_context(key_exists=_hklm_key_exists, value=_hklm_value) -> Mapping:
    """Everything the Owner should see before committing days of compute.

    Advisory. None of it refuses; all of it is the sort of fact that was
    never looked at before MC-R001 was started.
    """
    start = value(_WU_UX_SETTINGS, "ActiveHoursStart")
    end = value(_WU_UX_SETTINGS, "ActiveHoursEnd")
    active_span = None
    if isinstance(start, int) and isinstance(end, int):
        active_span = (end - start) % 24 or 24
    return MappingProxyType({
        "pending_reboot_markers": pending_reboot_markers(key_exists),
        "pending_file_rename_operations": bool(
            value(_SESSION_MANAGER, "PendingFileRenameOperations")),
        "active_hours_start": start,
        "active_hours_end": end,
        # Active Hours is capped at 18 hours by Windows, so it cannot cover a
        # run longer than that however it is configured. Reporting the span
        # makes that arithmetic visible instead of assumed.
        "active_hours_span_hours": active_span,
        "updates_paused_until": value(_WU_UX_SETTINGS,
                                      "PauseUpdatesExpiryTime"),
    })


def assert_host_fit_for_long_run(*, key_exists=_hklm_key_exists,
                                 value=_hklm_value) -> Mapping:
    """Refuse if Windows is ALREADY waiting to restart. Return the context.

    This is the only thing the repository can honestly check. It does not
    make the host safe, and a caller must not report it as having done so.
    """
    context = host_context(key_exists, value)
    markers = context["pending_reboot_markers"]
    if markers:
        raise HostNotFitError(
            "host_reboot_pending",
            "Windows is already waiting to restart (" + ", ".join(markers)
            + "). A long governed run started now is started on a countdown: "
            "restart the machine, let servicing settle, and launch again")
    return context
