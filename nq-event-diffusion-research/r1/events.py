"""TASK 2 -- the event universe loader.

Builds the sealed event population from the frozen F10 calendar and the PSMV
structural artifact, and reproduces PRE_SEAL_STRUCTURAL_N = 252 **without
reading one bar and without computing R_init, a direction, a return or a P&L**.

    E0  CPI or NFP on the frozen calendar, attested time        277
    E1  minus any FOMC calendar coexistence                    -19  -> 258
    E2  minus exact is_roll_transition sessions                  -0  -> 258
    E3  minus missing required structural anchors               -6  -> 252

E2 and E3 are decided by the ACCEPTED PSMV ARTIFACT, which is the sealed
structural authority (sealed S.1-S.3). That is deliberate: re-deriving them
here would mean re-reading market data, and the sealed record already carries
the measurement, digest-pinned.

E4 (`R_init == 0`) is NOT applied here. It is signal-defined, it lives in
`r1.signal`, and it must not run on real events during S2.

Invariants enforced: L-2 (attested release times only), L-3 (no release-time
inference anywhere -- there is no default, no fallback and no time literal in
this module), L-7 (the inclusion mask is a pure function of the calendar, the
symbology map and pre-decision availability -- never of an outcome), L-11
(calendar digest).
"""
from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .contract import SealedContract
from .errors import CalendarError, RunIntegrityError, SealIdentityError
from .roles import DataRole, check_role

ITSF_CALENDAR_PATH = (Path(__file__).resolve().parent.parent.parent
                      / "Intraday Trend Strategy Framework"
                      / "gate1" / "f10_event_calendar" / "f10_events.csv")

REQUIRED_COLUMNS = ("date_et", "event_type", "release_time_status",
                    "is_cpi_release_day", "is_nfp_release_day")


@dataclass(frozen=True)
class Event:
    """One sealed R1 event. Carries no outcome, by construction."""
    date_et: str
    event_type: str            # "CPI" | "NFP"
    release_time_status: str

    @property
    def year(self) -> int:
        return int(self.date_et[:4])


@dataclass(frozen=True)
class EventUniverse:
    events: tuple[Event, ...]
    funnel: dict[str, int]
    excluded: dict[str, str]        # date -> stage/reason
    calendar_sha256: str

    @property
    def n(self) -> int:
        return len(self.events)

    @property
    def dates(self) -> tuple[str, ...]:
        return tuple(e.date_et for e in self.events)

    def digest(self) -> str:
        """L-6: the event-set digest, bound into the run identity before any
        outcome exists. The runner refuses if it changes."""
        payload = "|".join(f"{e.date_et}:{e.event_type}" for e in self.events)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise CalendarError(f"event calendar {path} is empty -- fail closed")
    missing = [c for c in REQUIRED_COLUMNS if c not in rows[0]]
    if missing:
        raise CalendarError(f"event calendar is missing columns {missing}")
    return rows


def load_calendar(contract: SealedContract,
                  path: Path | str | None = None) -> list[dict[str, str]]:
    """Read the frozen calendar, enforcing L-11 then L-2/L-3.

    There is no `default_release_time` parameter, no fallback and no "typical"
    release clock anywhere in this function. A row without an attested time is
    a refusal, never an assumption (L-3 / IR-17).
    """
    check_role(DataRole.DEVELOPMENT_SIGNAL)
    p = Path(path) if path is not None else ITSF_CALENDAR_PATH
    if not p.exists():
        raise CalendarError(f"frozen event calendar not found at {p}")

    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != contract.event_calendar_sha256:                      # L-11
        raise SealIdentityError(
            f"event calendar digest mismatch -- fail closed (L-11): "
            f"{got[:16]} != {contract.event_calendar_sha256[:16]}")

    rows = _read_rows(p)
    for r in rows:
        if r["event_type"] in contract.event_family:
            status = (r.get("release_time_status") or "").strip()
            if status != contract.release_time_status_required:     # L-2
                raise CalendarError(
                    f"{r['date_et']} {r['event_type']}: release_time_status="
                    f"{status!r}, required "
                    f"{contract.release_time_status_required!r}. R1 refuses "
                    f"rather than inferring a release time (L-2 / L-3).")
    return rows


def build_universe(contract: SealedContract,
                   path: Path | str | None = None) -> EventUniverse:
    """The sealed E0 -> E3 funnel. Pure function of calendar + sealed authority."""
    rows = load_calendar(contract, path)

    e0: dict[str, str] = {}
    fomc_any: set[str] = set()
    for r in rows:
        if r["event_type"] == "FOMC":
            fomc_any.add(r["date_et"])
        if r.get("is_cpi_release_day") == "true":
            e0[r["date_et"]] = "CPI"
        if r.get("is_nfp_release_day") == "true":
            e0.setdefault(r["date_et"], "NFP")

    excluded: dict[str, str] = {}

    # E1 -- FOMC coexistence. The sealed record carries the exact removed set;
    # it is cross-checked against the live calendar rather than trusted blindly.
    sealed_fomc = set(contract.fomc_coexistence_dates)
    live_fomc = {d for d in e0 if d in fomc_any}
    if live_fomc != sealed_fomc:
        raise SealIdentityError(
            "FOMC coexistence set disagrees with the sealed PSMV record: "
            f"calendar {len(live_fomc)} vs sealed {len(sealed_fomc)}")
    for d in sorted(sealed_fomc):
        excluded[d] = "E1_fomc_coexistence"

    # E2 -- exact roll-transition sessions. Sealed measurement: exactly zero.
    if contract.roll_transition_exclusions != 0:                 # pragma: no cover
        raise SealIdentityError("sealed roll-transition exclusion count is not 0")

    # E3 -- missing required structural anchors, from the sealed PSMV artifact.
    for d, reason in contract.structural_excluded_dates.items():
        excluded[d] = f"E3_{reason}"

    kept = tuple(Event(d, t, contract.release_time_status_required)
                 for d, t in sorted(e0.items()) if d not in excluded)

    funnel = {
        "E0_cpi_or_nfp_calendar_events": len(e0),
        "E1_minus_any_fomc_calendar_entry": len(e0) - len(sealed_fomc),
        "E2_minus_exact_roll_transition_sessions":
            len(e0) - len(sealed_fomc) - contract.roll_transition_exclusions,
        "E3_minus_missing_required_structural_anchors": len(kept),
    }

    universe = EventUniverse(events=kept, funnel=funnel, excluded=excluded,
                             calendar_sha256=contract.event_calendar_sha256)
    _verify_against_sealed(contract, universe)
    return universe


def _verify_against_sealed(contract: SealedContract, u: EventUniverse) -> None:
    """Conservation + agreement with the sealed structural authority."""
    f = u.funnel
    sealed_e0 = contract.e0_calendar_events
    if f["E0_cpi_or_nfp_calendar_events"] != sealed_e0:
        raise SealIdentityError(f"E0 = {f['E0_cpi_or_nfp_calendar_events']}, "
                                f"sealed record says {sealed_e0}")
    if u.n != contract.pre_seal_structural_n:
        # NOT a researcher judgement about a shrunken sample, and NOT an
        # UNRESOLVED verdict with a smaller n. PSMV fixed the structural
        # universe before the seal; failing to reproduce it exactly means the
        # run is broken (see r1.errors.RunIntegrityError).
        raise RunIntegrityError(
            f"RUN_INTEGRITY_FAILURE: reproduced n = {u.n}, sealed "
            f"PRE_SEAL_STRUCTURAL_N = {contract.pre_seal_structural_n}. The "
            f"structural event universe must reproduce EXACTLY. E4 exact-zero "
            f"exclusions are a separate, prespecified stage that determines "
            f"POST_SEAL_SIGNAL_DEFINED_N; they are not structural shrinkage.")
    by_type = count_by_type(u.events)
    if by_type.get("CPI") != contract.cpi_structural_n or \
            by_type.get("NFP") != contract.nfp_structural_n:
        raise SealIdentityError(
            f"event-type split {by_type} disagrees with the sealed "
            f"CPI {contract.cpi_structural_n} / NFP {contract.nfp_structural_n}")
    # conservation: every E0 date is either kept or excluded, exactly once
    if len(u.events) + len(u.excluded) != f["E0_cpi_or_nfp_calendar_events"]:
        raise SealIdentityError("funnel is not conserved: kept + excluded != E0")


def count_by_type(events: Iterable[Event]) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in events:
        out[e.event_type] = out.get(e.event_type, 0) + 1
    return out


def era_of(contract: SealedContract, event: Event) -> str:
    for name, lo, hi in contract.eras:
        if lo <= event.year <= hi:
            return name
    raise CalendarError(f"{event.date_et} falls outside the sealed eras")
