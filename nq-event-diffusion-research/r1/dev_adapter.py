"""The authorized Development-data adapter -- IMPLEMENTED, not deferred.

S3 is a RUN stage, not a BUILD stage, so the loader that a real run will use is
built and validated HERE, in S2, against synthetic files, mocks, fake manifests
and tiny deterministic fixtures. **No real R1 event price was read to test it.**

What it does, in order, and it fails closed at every step:

    1. role        DEVELOPMENT_SIGNAL only -- IV and Lockbox are refused at the
                   ROLE, before any path is constructed or any file is opened
    2. manifest    the vendor manifest's own sha256 must equal the pinned value
    3. files       every data file's sha256 must equal its manifest entry
    4. schema      records must carry ts_event, open, high, low, close, volume
    5. window      every timestamp must fall inside the role's date window AND
                   inside the requested ET date
    6. duplicates  two records for one ET minute is a refusal, never a silent
                   last-writer-wins

Prices are Databento fixed-point integers (1e-9); they are converted once, at
the boundary, and never re-scaled downstream.

**On L-10.** The invariant isolates cost calibration: R1 reads the DERIVED
spread table and never raw BBO. This module decodes `ohlcv-1m` for the
DEVELOPMENT_SIGNAL role, which is a different thing, and it is the ONLY module
allowed to touch a decoder. `r1.invariants.scan_no_raw_decoder_import` keeps
the exception explicit and audited: every other module still refuses, and no
module anywhere may name a `bbo` schema.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

from .bars import Bar
from .errors import AuthorityError, R1Error, SealIdentityError
from .roles import DataRole, check_role, resolve_window

#: Databento fixed-point price scale.
FIXED_PRICE_SCALE = 1_000_000_000

DATA_GLOB = "*.ohlcv-1m.dbn.zst"
MANIFEST_NAME = "manifest.json"
REQUIRED_FIELDS = ("ts_event", "open", "high", "low", "close", "volume")

ET = "America/New_York"


@dataclass(frozen=True)
class RawRecord:
    """One decoded record, before it becomes a Bar."""
    ts_event_ns: int
    open: int
    high: int
    low: int
    close: int
    volume: int


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# decoders
# --------------------------------------------------------------------------

def decode_dbn(path: Path) -> Iterable[RawRecord]:
    """Real vendor format. The decoder is imported HERE, never at module level.

    A lazy import keeps the package's import graph free of the decoder, so a
    machine without `databento` can still load, test and audit every other part
    of R1.
    """
    import databento as dbn                       # noqa: PLC0415 - deliberate

    arr = dbn.DBNStore.from_file(path).to_ndarray()
    missing = [f for f in REQUIRED_FIELDS if f not in arr.dtype.names]
    if missing:
        raise R1Error(f"{path.name}: malformed schema, missing {missing}")
    for rec in arr:
        yield RawRecord(int(rec["ts_event"]), int(rec["open"]),
                        int(rec["high"]), int(rec["low"]), int(rec["close"]),
                        int(rec["volume"]))


def decode_jsonl_fixture(path: Path) -> Iterable[RawRecord]:
    """Tiny deterministic fixture format, for S2 validation only.

    It exists so every fail-closed branch above can be exercised without a byte
    of real market data. Real runs never reach it: the suffix decides.
    """
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise R1Error(f"{path.name}:{line_no}: malformed record") from exc
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            raise R1Error(f"{path.name}:{line_no}: malformed schema, missing "
                          f"{missing}")
        yield RawRecord(int(rec["ts_event"]), int(rec["open"]), int(rec["high"]),
                        int(rec["low"]), int(rec["close"]), int(rec["volume"]))


def _decoder_for(path: Path) -> Callable[[Path], Iterable[RawRecord]]:
    name = path.name
    if name.endswith(".dbn.zst") or name.endswith(".dbn"):
        return decode_dbn
    if name.endswith(".jsonl"):
        return decode_jsonl_fixture
    raise R1Error(f"{name}: unsupported data format -- fail closed rather than "
                  f"guessing a decoder")


def _et_parts(ts_ns: int) -> tuple[str, int]:
    """(ET date, ET minute-of-day) for a nanosecond UTC timestamp."""
    import pandas as pd                           # noqa: PLC0415 - deliberate

    ts = pd.Timestamp(ts_ns, unit="ns", tz="UTC").tz_convert(ET)
    return ts.strftime("%Y-%m-%d"), ts.hour * 60 + ts.minute


# --------------------------------------------------------------------------
# the adapter
# --------------------------------------------------------------------------

class DevelopmentDataAdapter:
    """A `BarSource` over the authorized NQ Development OHLCV archive.

    Constructing it verifies role, manifest identity and every file digest.
    Nothing is decoded until a date is actually requested, and a decoded day is
    cached so a run reads each file once.
    """

    role = "development_signal"

    def __init__(self, job_dir: Path | str, *,
                 expected_manifest_sha256: str,
                 data_role: "DataRole | str" = DataRole.DEVELOPMENT_SIGNAL,
                 glob: str = DATA_GLOB,
                 verify_files: bool = True):
        # 1. ROLE FIRST -- before any path is built, before any open()
        role = check_role(data_role)
        if role is not DataRole.DEVELOPMENT_SIGNAL:
            raise AuthorityError(
                f"{role.value} is not the Development signal role; R1's OD-1 "
                f"grant covers NQ Development OHLCV only")
        self._window = resolve_window(role)

        job = Path(job_dir)
        if not job.is_dir():
            raise R1Error(f"data directory not found: {job}")
        manifest_path = job / MANIFEST_NAME
        if not manifest_path.exists():
            raise R1Error(f"vendor manifest not found: {manifest_path}")

        # 2. MANIFEST IDENTITY
        got = _sha256(manifest_path)
        if got != expected_manifest_sha256:
            raise SealIdentityError(
                f"vendor manifest identity mismatch -- fail closed: "
                f"{got[:16]} != {expected_manifest_sha256[:16]}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        try:
            expected = {e["filename"]: e["hash"].split(":", 1)[-1]
                        for e in manifest["files"]}
        except (KeyError, TypeError, AttributeError) as exc:
            raise R1Error("vendor manifest is malformed") from exc

        files = sorted(job.glob(glob))
        if not files:
            raise R1Error(f"no data files matching {glob!r} in {job}")

        # 3. FILE DIGESTS
        digests: list[str] = []
        for p in files:
            want = expected.get(p.name)
            if want is None:
                raise SealIdentityError(
                    f"{p.name} is absent from the vendor manifest -- fail closed")
            have = _sha256(p)
            if have != want:
                raise SealIdentityError(
                    f"digest mismatch on {p.name} -- fail closed: "
                    f"{have[:16]} != {want[:16]}")
            digests.append(have)

        self.job_dir = job
        self.files = tuple(files)
        self.manifest_sha256 = got
        self.files_digest_rollup = hashlib.sha256(
            "\n".join(sorted(digests)).encode("utf-8")).hexdigest()
        self._cache: dict[str, dict[int, Bar]] = {}
        self._loaded = False

    # ---------------------------------------------------------------- reads
    def _load_all(self) -> None:
        if self._loaded:
            return
        lo, hi = self._window
        for path in self.files:
            decoder = _decoder_for(path)
            for rec in decoder(path):
                date_et, minute = _et_parts(rec.ts_event_ns)
                # 5. WINDOW -- the role's authorized dates, no exceptions
                if not (lo <= date_et < hi):
                    raise AuthorityError(
                        f"{path.name}: record at {date_et} is outside the "
                        f"{self.role} window [{lo}, {hi}) -- fail closed")
                day = self._cache.setdefault(date_et, {})
                # 6. DUPLICATES -- never last-writer-wins
                if minute in day:
                    raise R1Error(
                        f"duplicate record for {date_et} minute {minute} "
                        f"({path.name}) -- fail closed; PSMV measured ZERO "
                        f"duplicate RTH minutes in this archive")
                day[minute] = Bar(
                    minute=minute,
                    open=rec.open / FIXED_PRICE_SCALE,
                    high=rec.high / FIXED_PRICE_SCALE,
                    low=rec.low / FIXED_PRICE_SCALE,
                    close=rec.close / FIXED_PRICE_SCALE,
                    volume=int(rec.volume))
        self._loaded = True

    def bars_for(self, date_et: str) -> Mapping[int, Bar]:
        lo, hi = self._window
        if not (lo <= date_et < hi):
            raise AuthorityError(
                f"{date_et} is outside the authorized {self.role} window "
                f"[{lo}, {hi}) -- fail closed")
        self._load_all()
        return self._cache.get(date_et, {})

    def has_date(self, date_et: str) -> bool:
        self._load_all()
        return date_et in self._cache

    @property
    def dates(self) -> tuple[str, ...]:
        self._load_all()
        return tuple(sorted(self._cache))

    def identity(self) -> dict[str, str | int]:
        """What the run identity binds: files, digests, window. No prices."""
        return {
            "job_dir": str(self.job_dir),
            "n_files": len(self.files),
            "manifest_sha256": self.manifest_sha256,
            "files_digest_rollup_sha256": self.files_digest_rollup,
            "role": self.role,
            "window_start": self._window[0],
            "window_end_exclusive": self._window[1],
        }
