"""Synthetic fixture toolkit. NO real market data is used anywhere in S2.

Every price here is fabricated. The builders are deliberately explicit -- you
name the four anchors and, when a test needs one, the shape of the path between
them -- so a test's intent is readable from its arguments rather than from a
generated series.
"""
from __future__ import annotations

from r1.bars import Bar, SyntheticBarSource

PRE_WINDOW_LO = 480          # 08:00, the sealed participation window start


def _bar(minute: int, o: float, h: float, low: float, c: float,
         v: int = 0) -> Bar:
    return Bar(minute=minute, open=o, high=h, low=low, close=c, volume=v)


def event_day_bars(contract, *, pre_close: float, react_close: float,
                   entry_open: float, exit_open: float,
                   hold_path: list[float] | None = None,
                   hold_low_offset: float = 0.0,
                   hold_high_offset: float = 0.0,
                   pre_volume: int = 10,
                   include_pre_window: bool = True,
                   include_rth: bool = False,
                   rth_high: float = 0.0, rth_low: float = 0.0,
                   rth_bars: int | None = None,
                   noise_after_signal: float = 0.0) -> list[Bar]:
    """One synthetic event day.

    `noise_after_signal` shifts every bar at or after the signal horizon
    (08:32) -- the mutation lever for L-1.
    """
    bars: list[Bar] = []

    if include_pre_window:
        for m in range(PRE_WINDOW_LO, contract.pre_release_anchor_minute):
            bars.append(_bar(m, pre_close, pre_close, pre_close, pre_close,
                             pre_volume))

    # C(08:29): the last bar close strictly before the release instant
    bars.append(_bar(contract.pre_release_anchor_minute, pre_close, pre_close,
                     pre_close, pre_close, pre_volume))
    # the release minute itself is never an anchor; include it for realism
    bars.append(_bar(contract.pre_release_anchor_minute + 1, pre_close,
                     max(pre_close, react_close), min(pre_close, react_close),
                     (pre_close + react_close) / 2.0, pre_volume))
    # C(08:31): the reaction close, and the instant the signal completes
    bars.append(_bar(contract.reaction_close_minute, react_close, react_close,
                     react_close, react_close, pre_volume))

    # 08:32 -- the latency minute. Never traded, never read.
    n = noise_after_signal
    bars.append(_bar(contract.signal_complete_minute, react_close + n,
                     react_close + n, react_close + n, react_close + n, 1))

    # O(08:33) .. the hold, .. O(09:29)
    span = contract.exit_minute - contract.entry_minute
    if hold_path is None:
        step = (exit_open - entry_open) / span
        hold_path = [entry_open + step * i for i in range(span)]
    if len(hold_path) != span:
        raise ValueError(f"hold_path must have {span} entries, got {len(hold_path)}")

    for i, close in enumerate(hold_path):
        m = contract.entry_minute + i
        o = entry_open if i == 0 else hold_path[i - 1]
        hi = max(o, close) + hold_high_offset + n
        lo = min(o, close) - hold_low_offset + n
        bars.append(_bar(m, o + (n if i else 0.0), hi, lo, close + n, 5))

    bars.append(_bar(contract.exit_minute, exit_open + n, exit_open + n,
                     exit_open + n, exit_open + n, 5))

    if include_rth:
        count = rth_bars if rth_bars is not None else contract.expected_rth_minutes
        for j in range(count):
            m = contract.rth_lo_minute + j
            mid = (rth_high + rth_low) / 2.0
            hi = rth_high if j == 0 else mid
            lo = rth_low if j == 0 else mid
            bars.append(_bar(m, mid, hi, lo, mid, 5))
    return bars


def rth_only_day(contract, *, high: float, low: float,
                 complete: bool = True) -> list[Bar]:
    """A prior session that contributes (or deliberately fails to contribute)
    to ADR14."""
    count = contract.expected_rth_minutes if complete \
        else contract.expected_rth_minutes - 1
    mid = (high + low) / 2.0
    out = []
    for j in range(count):
        m = contract.rth_lo_minute + j
        out.append(_bar(m, mid, high if j == 0 else mid,
                        low if j == 0 else mid, mid, 5))
    return out


def source_with(contract, days: dict[str, list[Bar]]) -> SyntheticBarSource:
    src = SyntheticBarSource()
    for date, bars in days.items():
        src.add_day(date, bars)
    return src


def simple_event_source(contract, dates, *, pre=100.0, react=101.0,
                        entry=101.0, exit_price=102.0, **kw) -> SyntheticBarSource:
    """N identical synthetic event days -- the default arm fixture."""
    return source_with(contract, {
        d: event_day_bars(contract, pre_close=pre, react_close=react,
                          entry_open=entry, exit_open=exit_price, **kw)
        for d in dates})
