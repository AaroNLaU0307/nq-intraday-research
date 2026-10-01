"""TASK 14 / invariant L-9 -- the fail-closed data-role boundary.

Transcribed from ITSF `src/itsf/data/roles.py` (pinned in `r1.itsf_pin`), whose
contract is frozen. The one rule that matters:

    INTERNAL_VALIDATION_SIGNAL and PHYSICAL_LOCKBOX are deliberately absent
    from ROLE_WINDOWS. Any attempt to resolve them raises `RoleError` AT THE
    BOUNDARY -- BEFORE any path is constructed and before any file is opened --
    rather than leaking a KeyError that could be mistaken for a lookup bug.

R1 may load exactly one role: DEVELOPMENT_SIGNAL, under the OD-1 grant.
Internal Validation does not exist on this machine, the Lockbox does not exist
on this machine, and R1 must never probe for either: `resolve_window` refuses
on the ROLE, not on the filesystem, so no forbidden path is ever built.
"""
from __future__ import annotations

from enum import Enum

from .errors import RoleError


class DataRole(str, Enum):
    DEVELOPMENT_SIGNAL = "development_signal"
    EXECUTION_COST_CALIBRATION = "execution_cost_calibration"
    INTERNAL_VALIDATION_SIGNAL = "internal_validation_signal"   # never loadable
    PHYSICAL_LOCKBOX = "physical_lockbox"                       # never loadable


#: (start_inclusive, end_exclusive). Transcribed from ITSF ROLE_WINDOWS.
ROLE_WINDOWS: dict[DataRole, tuple[str, str]] = {
    DataRole.DEVELOPMENT_SIGNAL: ("2010-06-06", "2022-01-01"),
    DataRole.EXECUTION_COST_CALIBRATION: ("2025-01-01", "2025-04-01"),
}

#: The roles R1 is authorized to read at all, under OD-1.
R1_AUTHORIZED_ROLES: frozenset[DataRole] = frozenset({
    DataRole.DEVELOPMENT_SIGNAL,
    DataRole.EXECUTION_COST_CALIBRATION,   # derived spread table only (L-10)
})

FORBIDDEN_ROLES: frozenset[DataRole] = frozenset({
    DataRole.INTERNAL_VALIDATION_SIGNAL,
    DataRole.PHYSICAL_LOCKBOX,
})


def _coerce(role: "DataRole | str") -> DataRole:
    if isinstance(role, DataRole):
        return role
    try:
        return DataRole(role)
    except ValueError as exc:                     # unknown role -> fail closed
        raise RoleError(f"unknown data role {role!r}; R1 fails closed on "
                        f"unknown roles rather than guessing") from exc


def check_role(role: "DataRole | str") -> DataRole:
    """Authorize a role. Raises RoleError BEFORE any I/O is attempted."""
    r = _coerce(role)
    if r in FORBIDDEN_ROLES:
        raise RoleError(
            f"{r.value} is NOT GRANTED to R1 and is not present on this "
            f"machine. Access is a separate single-use Owner budget; in the "
            f"sealed ITSF data-role table, IV failure = hypothesis death. "
            f"Refused at the role boundary -- no path was constructed.")
    if r not in R1_AUTHORIZED_ROLES:
        raise RoleError(f"{r.value} is outside the OD-1 grant")
    return r


def resolve_window(role: "DataRole | str") -> tuple[str, str]:
    """The authorized date window for a role. Fails closed for everything else."""
    r = check_role(role)
    try:
        return ROLE_WINDOWS[r]
    except KeyError as exc:                        # pragma: no cover - defensive
        raise RoleError(f"no window is defined for {r.value}; fail closed"
                        ) from exc
