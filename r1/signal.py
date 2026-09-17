"""TASK 4 (signal) and TASK 3 (E4) -- the only two things R1 predicts from.

    R_init  = C(08:31) - C(08:29)          sealed C.1 / E.1
    d_event = sign(R_init)
    R_init == 0 exactly  ->  NO DIRECTION  ->  E4 exclusion, counted separately

The signal reads through a `SignalWindow`, which refuses any bar at or after
08:32:00 ET. L-1 is therefore enforced by the only object that can reach a bar:
mutating every post-08:31 bar cannot change the signal, because the signal
cannot see them (`tests/test_signal.py` proves it by mutation).

**Exact equality, with no epsilon.** The sealed convention is `R_init == 0`
exactly (ITSF's frozen L82). A tolerance would be a magnitude threshold, and a
magnitude threshold is exactly what L-8 and sealed C.3 forbid: R1 has one
reaction window, one entry, one exit, and NO threshold in the Primary.

**E4 must not run on real events during S2.** `apply_e4` refuses any bar source
that is not synthetic unless it is handed an S3 authorization token.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bars import BarSource, SignalWindow
from .contract import SealedContract
from .errors import AnchorError, AuthorityError

S3_TOKEN_PREFIX = "S3_RUN_AUTHORIZED_BY_AARON:"


@dataclass(frozen=True)
class Signal:
    """The complete signal for one event. No magnitude gate, no second signal."""
    date_et: str
    r_init: float
    d_event: int          # +1, -1, or 0 == no direction (E4)

    @property
    def has_direction(self) -> bool:
        return self.d_event != 0


def sign(x: float) -> int:
    """Exact three-way sign. `0.0` and `-0.0` are both no-direction."""
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def build_signal(source: BarSource, date_et: str,
                 contract: SealedContract) -> Signal:
    """R_init and d_event for one event day, through the L-1 window."""
    window = SignalWindow(source, date_et, contract)
    pre = window.require(contract.pre_release_anchor_minute)     # C(08:29)
    post = window.require(contract.reaction_close_minute)        # C(08:31)
    r_init = post.close - pre.close
    return Signal(date_et=date_et, r_init=r_init, d_event=sign(r_init))


def try_build_signal(source: BarSource, date_et: str,
                     contract: SealedContract) -> Signal | None:
    """`build_signal`, but a missing anchor returns None instead of raising.

    L-12: a missing anchor makes the event NA and excluded -- never forward
    filled, never interpolated, never substituted from a neighbouring bar.
    """
    try:
        return build_signal(source, date_et, contract)
    except AnchorError:
        return None


@dataclass(frozen=True)
class E4Result:
    """The signal-defined exclusion stage, reported separately by construction."""
    pre_seal_structural_n: int
    e4_count: int
    e4_dates: tuple[str, ...]
    na_dates: tuple[str, ...]
    signals: tuple[Signal, ...]

    @property
    def post_seal_signal_defined_n(self) -> int:
        return self.pre_seal_structural_n - self.e4_count - len(self.na_dates)


def apply_e4(source: BarSource, dates, contract: SealedContract, *,
             structural_n: int | None = None,
             s3_authorization: str | None = None) -> E4Result:
    """Apply E4 AFTER structural eligibility. Synthetic sources only in S2.

    POST_SEAL_SIGNAL_DEFINED_N = PRE_SEAL_STRUCTURAL_N - E4_COUNT, and the E4
    count is emitted separately rather than folded into `n` -- sealed S.3
    requires S2 to publish it as its first outcome-adjacent act.
    """
    if getattr(source, "role", None) != "synthetic":
        if not isinstance(s3_authorization, str) or \
                not s3_authorization.startswith(S3_TOKEN_PREFIX):
            raise AuthorityError(
                "E4 evaluates R_init, which reads real prices. S2 BUILD "
                "authorizes synthetic validation only: the real "
                "Development-sample E4 count must NOT be computed during S2. "
                "Run it in S3 under Aaron's authorization.")

    dates = tuple(dates)
    signals: list[Signal] = []
    e4: list[str] = []
    na: list[str] = []
    for d in dates:
        s = try_build_signal(source, d, contract)
        if s is None:
            na.append(d)
            continue
        if s.has_direction:
            signals.append(s)
        else:
            e4.append(d)
    return E4Result(
        pre_seal_structural_n=(structural_n if structural_n is not None
                               else len(dates)),
        e4_count=len(e4),
        e4_dates=tuple(e4),
        na_dates=tuple(na),
        signals=tuple(signals),
    )
