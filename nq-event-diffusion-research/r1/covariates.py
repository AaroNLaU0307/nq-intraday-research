"""TASK 8 -- the four sealed covariates, and nothing else.

    vol_state                  tercile of ADR14, boundaries from the TRAILING
                               250 event-eligible sessions only
    event_type                 CPI | NFP
    era                        2010-2013 | 2014-2017 | 2018-2021
    pre_release_participation  volume 08:00-08:29 / its own trailing 60-event
                               median

All four are context, never gates: sealed H.2 forbids them from selecting
events, and H.1 keeps `d_event` the ONLY variable in the claim. There is no
state x signal grid, no regime search and no second volatility definition
(L-8).

Every baseline here is trailing-only (L-5), and the enforcement is structural:
the trailing values come from a `TrailingHistory`, which cannot reach the
current date, and same-day participation volume is read through the L-1
`SignalWindow`, which cannot reach 08:32 or later. A fixture that randomises
all future rows leaves every value here byte-identical -- `tests/test_covariates.py`
proves it.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .bars import BarSource, SignalWindow, TrailingHistory
from .contract import SealedContract
from .errors import R1Error

VOL_STATES = ("low", "mid", "high")


@dataclass(frozen=True)
class Covariates:
    date_et: str
    event_type: str
    era: str
    adr14: float | None
    vol_state: str | None
    pre_release_participation: float | None


def rth_range(bars, contract: SealedContract) -> float | None:
    """RTH high - low for one day, or None when the session is not complete.

    "Complete" is ITSF's frozen 390-bar rule; an incomplete session does not
    contribute to ADR14 rather than contributing a distorted range.
    """
    rth = [b for m, b in bars.items()
           if contract.rth_lo_minute <= m <= contract.rth_hi_minute]
    if len(rth) != contract.expected_rth_minutes:
        return None
    return max(b.high for b in rth) - min(b.low for b in rth)


def adr14(history: TrailingHistory, contract: SealedContract) -> float | None:
    """Mean RTH range over the previous 14 COMPLETE RTH days, current excluded.

    ITSF's frozen normalizer, reused so R1 stays commensurable with the
    project's existing cost and prop units (sealed F.1).
    """
    ranges: list[float] = []
    for d in reversed(history.dates):          # strictly prior, newest first
        r = rth_range(history.bars_for(d), contract)
        if r is not None:
            ranges.append(r)
        if len(ranges) == contract.adr_lookback_days:
            break
    if len(ranges) < contract.adr_lookback_days:
        return None                            # warm-up: NA, excluded, counted
    return sum(ranges) / len(ranges)


def vol_state(value: float | None, trailing_values,
              contract: SealedContract) -> str | None:
    """Tercile of ADR14 against TRAILING event-eligible sessions only (H.2).

    Full-sample terciles would be a look-ahead and are banned by L-5, so the
    boundaries are recomputed from the most recent `vol_state_lookback_sessions`
    strictly-prior values and from nothing else.
    """
    if value is None:
        return None
    trail = [v for v in trailing_values if v is not None]
    trail = trail[-contract.vol_state_lookback_sessions:]
    if len(trail) < contract.c2_vol_strata:
        return None
    ordered = sorted(trail)
    n = len(ordered)
    lo_cut = ordered[max(0, int(n / 3) - 1)]
    hi_cut = ordered[min(n - 1, int(2 * n / 3))]
    if value <= lo_cut:
        return VOL_STATES[0]
    if value >= hi_cut:
        return VOL_STATES[2]
    return VOL_STATES[1]


def pre_release_volume(source: BarSource, date_et: str,
                       contract: SealedContract) -> int:
    """Total volume in the sealed pre-release window, read causally (L-1)."""
    lo, hi = contract.participation_window_minutes
    window = SignalWindow(source, date_et, contract)
    total = 0
    for minute in range(lo, hi + 1):
        bar = window.get(minute)
        if bar is not None:
            total += int(bar.volume)
    return total


def participation_ratio(volume: int, trailing_volumes,
                        contract: SealedContract) -> float | None:
    """volume / trailing 60-event median. Trailing-only by construction."""
    trail = [v for v in trailing_volumes if v is not None]
    trail = trail[-contract.participation_trailing_events:]
    if not trail:
        return None
    base = median(trail)
    if base == 0:
        return None
    return volume / base


def build_covariates(source: BarSource, event, contract: SealedContract, *,
                     history: TrailingHistory,
                     trailing_adr: "list[float | None] | tuple" = (),
                     trailing_volumes: "list[int] | tuple" = ()) -> Covariates:
    from .events import era_of
    if event.event_type not in contract.event_family:
        raise R1Error(f"{event.event_type!r} is outside the sealed family")
    a = adr14(history, contract)
    vol = vol_state(a, trailing_adr, contract)
    volume = pre_release_volume(source, event.date_et, contract)
    return Covariates(
        date_et=event.date_et,
        event_type=event.event_type,
        era=era_of(contract, event),
        adr14=a,
        vol_state=vol,
        pre_release_participation=participation_ratio(
            volume, trailing_volumes, contract),
    )
