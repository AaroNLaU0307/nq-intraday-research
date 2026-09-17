"""Bar access, and the causal windows that make leakage structurally impossible.

Two ideas carry most of R1's leakage safety:

1.  **Nothing reads bars directly.** The signal builder gets a `SignalWindow`,
    the P&L builder gets a `TradeWindow`, the covariate builder gets a
    `TrailingHistory`. Each refuses out-of-window reads with `LeakageError`
    instead of returning data. L-1, L-4 and L-5 are therefore enforced by the
    only object that can reach a bar, not by a reviewer's attention.

2.  **Real Development bars are unreachable in S2.** `DevelopmentBarSource`
    refuses without an explicit S3 authorization token, and it refuses BEFORE
    importing a decoder or building a path -- so S2 cannot accidentally run the
    outcome path over real data, which is precisely what the S2 authorization
    forbids.

`ts_event` is the BAR START minute (the frozen Databento convention PSMV used),
so minute-of-day 509 is the 08:29 bar, whose close prints at 08:30:00.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol

from .errors import AuthorityError, LeakageError

MINUTES_PER_DAY = 1440


@dataclass(frozen=True)
class Bar:
    """One 1-minute OHLCV bar. `minute` is minute-of-day ET of the bar START."""
    minute: int
    open: float
    high: float
    low: float
    close: float
    volume: int = 0


class BarSource(Protocol):
    """Anything that can hand back a day's bars keyed by bar-start minute."""

    def bars_for(self, date_et: str) -> Mapping[int, Bar]: ...

    def has_date(self, date_et: str) -> bool: ...


class SyntheticBarSource:
    """Deterministic in-memory bars. The ONLY source S2 is allowed to use."""

    role = "synthetic"

    def __init__(self, days: Mapping[str, Iterable[Bar]] | None = None):
        self._days: dict[str, dict[int, Bar]] = {}
        for date_et, bars in (days or {}).items():
            self.add_day(date_et, bars)

    def add_day(self, date_et: str, bars: Iterable[Bar]) -> "SyntheticBarSource":
        day = {b.minute: b for b in bars}
        self._days[date_et] = day
        return self

    def bars_for(self, date_et: str) -> Mapping[int, Bar]:
        return self._days.get(date_et, {})

    def has_date(self, date_et: str) -> bool:
        return date_et in self._days

    @property
    def dates(self) -> tuple[str, ...]:
        return tuple(sorted(self._days))


class DevelopmentBarSource:
    """The real NQ Development OHLCV source -- BUILT, and BLOCKED until S3.

    S2 BUILD authorization explicitly does not authorize processing real
    Development data through the completed outcome path. So this class refuses
    at construction unless it is handed an S3 authorization token, and the
    refusal happens before any decoder import and before any path is built:
    an accidental call cannot read a byte of market data.
    """

    role = "development_signal"
    S3_TOKEN_PREFIX = "S3_RUN_AUTHORIZED_BY_AARON:"

    def __init__(self, data_dir, s3_authorization: str | None = None):
        if not isinstance(s3_authorization, str) or not \
                s3_authorization.startswith(self.S3_TOKEN_PREFIX):
            raise AuthorityError(
                "real Development bars are NOT authorized in S2 BUILD. The S2 "
                "grant covers implementation and synthetic validation only; "
                "running the outcome path over real data is an S3 act and "
                "needs Aaron's explicit authorization. No decoder was "
                "imported and no path was constructed.")
        self._data_dir = data_dir
        self._token = s3_authorization

    def bars_for(self, date_et: str) -> Mapping[int, Bar]:   # pragma: no cover
        raise NotImplementedError(
            "S3 integration deliberately left unimplemented in S2: the loader "
            "body would be exercised only by a real run. Build it in S3 "
            "against the same Bar/BarSource contract the synthetic source and "
            "the whole test suite already pin.")

    def has_date(self, date_et: str) -> bool:                # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------
# Causal windows
# --------------------------------------------------------------------------

class _Window:
    """Base: a read-only view of one day that refuses out-of-window minutes."""

    _what = "window"

    def __init__(self, source: BarSource, date_et: str,
                 lo: int | None, hi: int | None):
        self._bars = source.bars_for(date_et)
        self._date = date_et
        self._lo = lo          # inclusive, None = unbounded
        self._hi = hi          # inclusive, None = unbounded
        self.reads: list[int] = []

    def _check(self, minute: int) -> None:
        if self._lo is not None and minute < self._lo:
            raise LeakageError(
                f"{self._what}: minute {minute} is before the permitted floor "
                f"{self._lo} on {self._date}")
        if self._hi is not None and minute > self._hi:
            raise LeakageError(
                f"{self._what}: minute {minute} is at or after the permitted "
                f"horizon {self._hi + 1} on {self._date}")

    def get(self, minute: int) -> Bar | None:
        self._check(minute)
        self.reads.append(minute)
        return self._bars.get(minute)

    def require(self, minute: int) -> Bar:
        bar = self.get(minute)
        if bar is None:
            from .errors import AnchorError
            raise AnchorError(
                f"required bar at minute {minute} is missing on {self._date}. "
                f"No forward fill, no interpolation, no neighbouring-bar "
                f"substitution (L-12): the event is NA, excluded and counted.")
        return bar

    def minutes(self) -> tuple[int, ...]:
        lo = self._lo if self._lo is not None else -1
        hi = self._hi if self._hi is not None else MINUTES_PER_DAY
        return tuple(sorted(m for m in self._bars if lo <= m <= hi))


class SignalWindow(_Window):
    """L-1. Reads strictly BEFORE the signal horizon (08:32:00 ET)."""
    _what = "L-1 signal window"

    def __init__(self, source: BarSource, date_et: str, contract):
        super().__init__(source, date_et, None,
                         contract.signal_read_horizon_minute - 1)


class TradeWindow(_Window):
    """L-4. Reads from the entry fill onward -- no bar before O(08:33)."""
    _what = "L-4 trade window"

    def __init__(self, source: BarSource, date_et: str, contract):
        super().__init__(source, date_et, contract.pnl_read_floor_minute, None)


class TrailingHistory:
    """L-5. Strictly prior sessions only; the current date is unreachable."""

    def __init__(self, source: BarSource, as_of_date_et: str,
                 session_dates: Iterable[str]):
        self._source = source
        self._as_of = as_of_date_et
        self._dates = tuple(d for d in sorted(session_dates)
                            if d < as_of_date_et)

    @property
    def dates(self) -> tuple[str, ...]:
        return self._dates

    def bars_for(self, date_et: str) -> Mapping[int, Bar]:
        if date_et >= self._as_of:
            raise LeakageError(
                f"L-5 trailing history: {date_et} is not strictly prior to "
                f"{self._as_of}. Every normalizer, percentile and tercile "
                f"boundary is trailing-only.")
        return self._source.bars_for(date_et)
