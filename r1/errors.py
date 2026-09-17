"""R1 error types. Every one of these is a FAIL-CLOSED refusal.

No R1 module may catch these and continue with a default. A default is exactly
what invariants L-3, L-9 and L-11 exist to forbid.
"""
from __future__ import annotations


class R1Error(Exception):
    """Base for every R1 refusal."""


class SealIdentityError(R1Error):
    """The sealed identity does not match: a digest, the content commit, or a
    sealed scientific constant. The engine must refuse to run (L-6, L-11)."""


class RoleError(R1Error):
    """A forbidden data role was requested (L-9). Raised BEFORE any file read."""


class AuthorityError(R1Error):
    """An action beyond the current stage authorization was attempted --
    e.g. touching real Development bars through the outcome path during S2."""


class AnchorError(R1Error):
    """A required anchor is missing or was substituted (L-12). The event is NA,
    excluded and counted; it is never forward-filled or interpolated."""


class LeakageError(R1Error):
    """A read outside the permitted causal window was attempted (L-1, L-4, L-5)."""


class CalendarError(R1Error):
    """A calendar row is unusable: missing or non-attested release time (L-2),
    or an attempt to infer/default a release time (L-3)."""


class OutcomeExposureError(R1Error):
    """An attempt to read, print or return a sealed R1 outcome without an
    explicit Owner-authorized reveal."""
