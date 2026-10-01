"""The OPERATIONAL execution ledger -- deliberately OUTSIDE the sealed digest set.

`R1_TRIAL_REGISTRY.md` is sealed byte-for-byte and must stay that way: it is the
immutable lineage/trial-registration SNAPSHOT taken at the S1 seal. It cannot
carry lifecycle events that happen after the seal, because appending to it would
break the digest the whole engine refuses to run without.

So the mutable lifecycle lives here instead, in `R1_EXECUTION_LEDGER.md`:

    S2_BUILD_COMPLETE . S3_AUTHORIZED . RUN_STARTED (consumes the trial) .
    POWER_GATE_EXECUTED . OWNER_POWER_GATE_DECISION . OUTCOME_BUNDLE_CREATED .
    REVEAL_AUTHORIZED . REVEALED . VERDICT_CLOSED

Two different integrity models, on purpose:

    sealed registry       EXACT IMMUTABLE DIGEST      -- one sha256, forever
    operational ledger    APPEND-ONLY HASH CHAIN      -- each entry commits to
                          its parent, so history cannot be edited, deleted or
                          reordered without breaking every descendant

The genesis entry binds the ledger to the seal, so an operational ledger cannot
be silently attached to a different lineage or a different seal.

**This file changes no scientific design.** It records what happened, never what
is true about the market.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .errors import LedgerError, SealIdentityError

LEDGER_FILE = "R1_EXECUTION_LEDGER.md"

GENESIS = "GENESIS"
S2_BUILD_COMPLETE = "S2_BUILD_COMPLETE"
S3_AUTHORIZED = "S3_AUTHORIZED"
RUN_STARTED = "RUN_STARTED"                  # <- consumes the trial
POWER_GATE_EXECUTED = "POWER_GATE_EXECUTED"
OWNER_POWER_GATE_DECISION = "OWNER_POWER_GATE_DECISION"
OUTCOME_BUNDLE_CREATED = "OUTCOME_BUNDLE_CREATED"
REVEAL_AUTHORIZED = "REVEAL_AUTHORIZED"
REVEALED = "REVEALED"
VERDICT_CLOSED = "VERDICT_CLOSED"

EVENT_TYPES = (GENESIS, S2_BUILD_COMPLETE, S3_AUTHORIZED, RUN_STARTED,
               POWER_GATE_EXECUTED, OWNER_POWER_GATE_DECISION,
               OUTCOME_BUNDLE_CREATED, REVEAL_AUTHORIZED, REVEALED,
               VERDICT_CLOSED)

#: Events that may only ever be appended to the OPERATIONAL ledger. Recording
#: one in the sealed registry is a category error and is refused.
OPERATIONAL_ONLY = tuple(e for e in EVENT_TYPES if e != GENESIS)

_ENTRY_RE = re.compile(
    r"^\| (?P<seq>\d+) \| (?P<utc>[0-9TZ:\- ]+) \| `(?P<event>[A-Z0-9_]+)` \| "
    r"(?P<actor>[^|]*) \| (?P<detail>[^|]*) \| `(?P<parent>[0-9a-f]{64}|-)` \| "
    r"`(?P<digest>[0-9a-f]{64})` \|$", re.M)

ZERO = "-"


@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    utc: str
    event: str
    actor: str
    detail: str
    parent: str
    digest: str

    def recompute(self) -> str:
        return entry_digest(self.seq, self.utc, self.event, self.actor,
                            self.detail, self.parent)


def entry_digest(seq: int, utc: str, event: str, actor: str, detail: str,
                 parent: str) -> str:
    """Each entry commits to its parent: edit one, break every descendant."""
    payload = json.dumps({"seq": seq, "utc": utc, "event": event,
                          "actor": actor, "detail": detail, "parent": parent},
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _clean(text: str) -> str:
    """Table cells may not carry a pipe or a newline."""
    return " ".join(str(text).replace("|", "/").split())


def read_entries(path: Path | str) -> tuple[LedgerEntry, ...]:
    p = Path(path)
    if not p.exists():
        raise LedgerError(f"operational ledger not found at {p}")
    text = p.read_text(encoding="utf-8")
    return tuple(LedgerEntry(seq=int(m["seq"]), utc=m["utc"].strip(),
                             event=m["event"], actor=m["actor"].strip(),
                             detail=m["detail"].strip(), parent=m["parent"],
                             digest=m["digest"])
                 for m in _ENTRY_RE.finditer(text))


def verify_chain(path: Path | str) -> tuple[LedgerEntry, ...]:
    """Append-only verification. Raises on edit, deletion or reordering."""
    entries = read_entries(path)
    if not entries:
        raise LedgerError("operational ledger has no entries -- fail closed")
    if entries[0].event != GENESIS:
        raise LedgerError("the first ledger entry must be the GENESIS record")
    parent = ZERO
    for i, e in enumerate(entries, start=1):
        if e.seq != i:
            raise LedgerError(
                f"ledger sequence broken at position {i}: found seq {e.seq}. "
                f"Entries may be APPENDED, never deleted or reordered.")
        if e.parent != parent:
            raise LedgerError(
                f"ledger entry {e.seq} does not chain to its parent: "
                f"expected {parent[:12]}, found {e.parent[:12]}. History was "
                f"edited, deleted or reordered.")
        if e.recompute() != e.digest:
            raise LedgerError(
                f"ledger entry {e.seq} ({e.event}) was edited: its content no "
                f"longer hashes to its recorded digest.")
        parent = e.digest
    return entries


def current_digest(path: Path | str) -> str:
    """The head of the chain -- the ledger's current identity."""
    return verify_chain(path)[-1].digest


def ancestry(path: Path | str) -> tuple[str, ...]:
    return tuple(e.digest for e in verify_chain(path))


def append_event(path: Path | str, event: str, actor: str, detail: str, *,
                 utc: str | None = None) -> LedgerEntry:
    """Append one event. Verifies the whole chain first, then extends it."""
    if event not in EVENT_TYPES:
        raise LedgerError(f"unknown ledger event {event!r}; the lifecycle is "
                          f"{list(EVENT_TYPES)}")
    if event == GENESIS:
        raise LedgerError("GENESIS is written once, by `create_ledger`")
    p = Path(path)
    entries = verify_chain(p)
    seq = entries[-1].seq + 1
    parent = entries[-1].digest
    stamp = utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    actor, detail = _clean(actor), _clean(detail)
    digest = entry_digest(seq, stamp, event, actor, detail, parent)
    row = (f"| {seq} | {stamp} | `{event}` | {actor} | {detail} | "
           f"`{parent}` | `{digest}` |\n")
    with p.open("a", encoding="utf-8", newline="") as fh:
        fh.write(row)
    return LedgerEntry(seq, stamp, event, actor, detail, parent, digest)


def refuse_operational_event_in_sealed_registry(event: str) -> None:
    """RUN_STARTED and its siblings may never be written to the sealed file."""
    if event in OPERATIONAL_ONLY:
        raise SealIdentityError(
            f"{event} may NOT be recorded in the sealed R1_TRIAL_REGISTRY.md: "
            f"that file is sealed byte-for-byte and appending to it would "
            f"break the seal the engine refuses to run without. Operational "
            f"lifecycle events belong in {LEDGER_FILE}.")


def create_ledger(path: Path | str, *, contract, sealed_registry_sha256: str,
                  seal_attestation_commit: str, utc: str | None = None) -> LedgerEntry:
    """Write the genesis record, binding the ledger to lineage and seal."""
    p = Path(path)
    if p.exists():
        raise LedgerError(f"{p.name} already exists; genesis is written once")
    stamp = utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    detail = _clean(
        f"lineage R1 (Scheduled-Release Information-Diffusion Continuation); "
        f"SAMPLE_FORMAL_TRIAL_ORDINAL={contract.sample_formal_trial_ordinal}; "
        f"PRIOR_LINEAGE=ITSF S0-T001; INHERITED_RESEARCHER_EXPOSURE_COUNT="
        f"{contract.inherited_researcher_exposure_count}; "
        f"SEALED_TRIAL_REGISTRY_SHA256={sealed_registry_sha256}; "
        f"CONTENT_COMMIT={contract.content_commit}; "
        f"SEAL_ATTESTATION_COMMIT={seal_attestation_commit}")
    digest = entry_digest(1, stamp, GENESIS, "main agent", detail, ZERO)
    header = f"""# R1 EXECUTION LEDGER — operational, append-only

```
RECORD_TYPE       = OPERATIONAL_EXECUTION_LEDGER (append-only hash chain)
SEALED            = NO -- deliberately OUTSIDE the S1 sealed digest set
SEALED_COUNTERPART= R1_TRIAL_REGISTRY.md, which is sealed byte-for-byte and is
                    the IMMUTABLE lineage / trial-registration snapshot. It is
                    never edited, and no lifecycle event is ever added to it.
INTEGRITY         = each entry commits to its parent's digest; editing,
                    deleting or reordering any historical entry breaks every
                    descendant. Verified by `r1.ledger.verify_chain`.
```

**What belongs here:** every post-seal lifecycle event — S2 build completion,
S3 authorization, `RUN_STARTED` (the row that CONSUMES the trial), power-gate
execution and the Owner's decision on it, outcome-bundle creation, reveal
authorization, the reveal itself, and verdict closure.

**What does not:** anything that changes scientific design. This ledger records
what happened; it never states what is true about the market.

| # | utc | event | actor | detail | parent | digest |
|---|---|---|---|---|---|---|
| 1 | {stamp} | `{GENESIS}` | main agent | {detail} | `{ZERO}` | `{digest}` |
"""
    p.write_text(header, encoding="utf-8", newline="\n")
    return LedgerEntry(1, stamp, GENESIS, "main agent", detail, ZERO, digest)


def assert_sealed_registry_unchanged(contract, root: Path | None = None) -> None:
    """The sealed registry keeps EXACT-DIGEST integrity, forever."""
    from .contract import PROJECT_ROOT, sha256_file
    root = root or PROJECT_ROOT
    got = sha256_file(root / "R1_TRIAL_REGISTRY.md")
    if got != contract.trial_registry_sha256:
        raise SealIdentityError(
            f"the sealed trial registry has changed: {got[:16]} != "
            f"{contract.trial_registry_sha256[:16]}. It is immutable.")
