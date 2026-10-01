"""Official vendor symbology -> roll intervals. Never price.

WHY THIS EXISTS. `build_universe` takes `roll_intervals`, and nothing in this
repository produced any, so every caller passed the default `()`. That is not
a missing convenience: `dataset._straddles_roll` returns False for an empty
transition list, so the ruled `r1_drop_and_extend` rule drops nothing and
vol20 is computed ACROSS contract rolls -- a price discontinuity counted as a
return. NQ.v.0 is a continuous front-month series with 47 rolls over the
Development window, so the contamination is systematic, and it flows into the
terciles, the volatility strata, and every row of the day-strata supplement.

WHERE THE TRANSITIONS COME FROM, and it is the whole point. `RollInterval` is
documented as "one row of the official symbology mapping (IR-16)", and the
authorized DBN files carry exactly that: `stype_in=continuous`,
`stype_out=instrument_id`, and `metadata.mappings["NQ.v.0"]` listing
`{start_date, end_date, symbol}` per instrument. A roll is where that mapping
switches.

NOT FROM THE SYMBOL COLUMN, and not from prices. Measured 2026-09-05 on the
authorized files: after `to_df()` the `symbol` column is `NQ.v.0` for every
row of every file INCLUDING across the 2021-12-13 roll -- it is the
continuous symbol, never the raw contract. Deriving rolls from it is
impossible, and deriving them from price jumps would be inference where the
vendor supplies fact.

THE PURE HALF IS SEPARATE. `coalesce` takes intervals already in hand and is
tested exhaustively without touching a file; `read_vendor_intervals` is the
thin I/O wrapper, and it reads METADATA only -- it never decodes a bar.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence

__all__ = ["VendorInterval", "coalesce", "read_vendor_intervals",
           "roll_transition_dates"]

#: `(start_date, end_date_exclusive, instrument_id)`, all ISO strings. Kept as
#: a plain tuple rather than `s0.context.RollInterval` because `s0` imports
#: `data` and not the other way round; the caller adapts.
VendorInterval = tuple


def coalesce(intervals: Iterable[Sequence[str]]) -> tuple:
    """Merge adjacent intervals carrying the SAME instrument.

    The vendor emits its mapping per FILE, so a contract that spans three
    monthly files appears as three intervals split at month boundaries. Those
    boundaries are not rolls, and treating them as rolls would drop a return
    at the start of every month -- twelve times more drops than there are
    rolls. Merging on `end == next start AND same instrument` is what makes
    the transition list mean what it says.

    Deterministic: input is sorted first, so the caller may pass a set.
    """
    out: list[list[str]] = []
    for start, end, instrument in sorted(tuple(i) for i in intervals):
        if out and out[-1][2] == instrument and out[-1][1] == start:
            out[-1][1] = end
        else:
            out.append([start, end, instrument])
    return tuple(tuple(row) for row in out)


def roll_transition_dates(coalesced: Sequence[Sequence[str]]) -> tuple:
    """The start of every interval after the first -- i.e. each switch.

    The FIRST interval's start is the beginning of the sample, not a roll.
    Including it would drop a return that never crossed anything.
    """
    return tuple(row[0] for row in coalesced[1:])


def read_vendor_intervals(job_dir, filenames: Sequence[str] | None = None,
                          *, continuous_symbol: str = "NQ.v.0") -> list:
    """The vendor mapping out of the authorized DBN files. METADATA ONLY.

    `DBNStore.from_file(...).metadata.mappings` is read; `to_df()` is never
    called, so no bar is decoded here. Refuses a file whose mapping does not
    carry exactly the expected continuous symbol, because a file mapping some
    other instrument would silently contribute foreign transitions.
    """
    import databento as db

    root = Path(job_dir)
    names = (sorted(p.name for p in root.glob("*.dbn.zst"))
             if filenames is None else list(filenames))
    found: list = []
    for name in names:
        mappings = db.DBNStore.from_file(root / name).metadata.mappings or {}
        keys = list(mappings)
        if keys != [continuous_symbol]:
            raise ValueError(
                "%s maps %r, expected exactly [%r] — a foreign instrument "
                "would contribute foreign roll transitions"
                % (name, keys, continuous_symbol))
        for entry in mappings[continuous_symbol]:
            found.append((entry["start_date"].isoformat(),
                          entry["end_date"].isoformat(),
                          str(entry["symbol"])))
    return found
