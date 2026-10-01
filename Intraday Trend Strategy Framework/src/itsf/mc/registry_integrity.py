"""Registry integrity, split in two: the current dependency, and history.

QROS-CF v2 §2.6 (DEC-0006 I3; converged F13, F15a). This module replaces
the after-the-fact registration table that `tests/test_mc_supplement_
integration.py` used to carry -- a mirror of registry rows in a test file,
which forced a framework commit after every registry event and, because
the whole tree was the authorization identity, could only be committed
once the run was terminal.

TWO QUESTIONS, TWO FUNCTIONS, TWO TIERS.

    current_dependency_check(text, run_id)     tier B -- may block
        The chain the next run depends on: it resolves; no owner hold
        applies; if its terminal is a verification row, that row is BOUND
        -- a witness names the same attestation hash and the same row, the
        attestation file exists and hashes to it, names this id, and
        restates the sealed sha256 of the P4 it verified.

    history_health(text)                       tier C -- never blocks
        Every chain, the same binding, plus the witness hash chain (each
        witness's previous_sha256 equals its predecessor's sha256). A gap
        in 2026-08 history is reported; it does not hold a 2026-09 run.

Parser legality is NOT binding validity (Astra F13): a syntactically legal
P5 that cites an attestation belonging to another run, or an attestation
that never mentions the sealed artifact it claims to have verified, is
refused here by name. Forged-but-legal rows are the tests' fixtures.

NEVER reads the registry file (callers hand it text through the boundary);
resolves only through `registry_boundary.mediate`; writes nothing.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
import json
import re
from pathlib import Path

from . import owner_control as _oc

__all__ = ["WITNESS_DIR", "ATTESTATION_ROOTS", "Problem", "CheckReport",
           "verification_rows", "locate_witness", "locate_attestation",
           "verify_binding", "current_dependency_check", "history_health",
           "witness_chain_problems"]

WITNESS_DIR = Path(r"C:\Users\Aaron\quant-data\registry-witness\itsf")
#: Where an attestation may live when the witness records no path: the
#: framework's ops/ (S001's attestation was committed there) and the review
#: area (every strict-blind verifier wrote its own directory).
ATTESTATION_ROOTS = (Path(__file__).resolve().parents[3] / "ops",
                     Path(r"C:\Users\Aaron\quant-data\review"))
_HEX64 = re.compile(r"[0-9a-f]{64}")
_VERIFICATION_SHORT_IDS = ("P5", "F2v")


@_dc.dataclass(frozen=True)
class Problem:
    code: str
    detail: str
    supplement_id: str = ""
    seq: str = ""


@_dc.dataclass(frozen=True)
class CheckReport:
    ok: bool
    problems: tuple
    checked: tuple = ()          # what was examined, for the record


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(text: str):
    """Chains for `text`, THROUGH THE BOUNDARY (C2): both lifecycles run
    over one snapshot; any refusal is total. Returns (chains, refusal)."""
    from . import registry_boundary as _rb

    snapshot = _rb.RegistrySnapshot(
        text=text, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source="registry_integrity:text handed in (no file was read)")
    resolution = _rb.mediate(snapshot)
    if resolution.refusal:
        return ({}, f"[{resolution.refusing_lifecycle}] {resolution.refusal}")
    return (dict(resolution.supplement_chains), None)


def verification_rows(chain) -> tuple:
    """The P5 / F2v events of one resolved chain."""
    return tuple(e for e in getattr(chain, "events", ())
                 if getattr(e, "short_id", "") in _VERIFICATION_SHORT_IDS)


def _claimed_attestation_sha(event) -> str | None:
    fields = getattr(event, "fields", {}) or {}
    if event.short_id == "P5":
        return fields.get("attestation_sha256")
    # F2v: the detail cites "attestation <path> sha256 <64-hex>"; the LAST
    # 64-hex token after the word "attestation" is the attestation's.
    detail = fields.get("detail", "")
    tail = detail.split("attestation", 1)[1] if "attestation" in detail else ""
    found = _HEX64.findall(tail)
    return found[0] if found else None


def _sealed_sha_before(chain, event) -> str | None:
    """The sealed_sha256 of the P4 this verification row follows."""
    sealed = None
    for e in getattr(chain, "events", ()):
        if e.pos >= event.pos:
            break
        if e.short_id == "P4":
            sealed = (e.fields or {}).get("sealed_sha256")
    return sealed


def locate_witness(event, witness_dir: Path = WITNESS_DIR) -> dict | None:
    """The witness whose `last_line` is this row and whose attestation
    hash equals the row's. Both must hold; one alone is not a binding."""
    want = _claimed_attestation_sha(event)
    seq = str(event.row.seq).strip()
    if not want or not witness_dir.is_dir():
        return None
    for path in sorted(witness_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:                                      # noqa: BLE001
            continue
        last = str(data.get("last_line", "")).strip()
        if not last.startswith(f"| {seq} |"):
            continue
        if data.get("attestation_sha256") != want:
            continue
        data["_witness_path"] = str(path)
        return data


def locate_attestation(sha: str, witness: dict | None,
                       roots=ATTESTATION_ROOTS) -> Path | None:
    """The attestation file: the witness's path if it hashes right, else a
    hash search over `*ATTESTATION*.md` under the known roots (a handful
    of small files; never the sealed cells)."""
    if witness and witness.get("attestation"):
        p = Path(witness["attestation"])
        if p.is_file() and _sha256(p) == sha:
            return p
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.glob("*ATTESTATION*.md")) + \
                sorted(root.glob("*/*ATTESTATION*.md")):
            if _sha256(p) == sha:
                return p
    return None


def verify_binding(chain, event, *, witness_dir: Path = WITNESS_DIR,
                   roots=ATTESTATION_ROOTS) -> tuple:
    """Problems binding one verification row to its evidence; () when bound."""
    sid = event.supplement_id
    seq = str(event.row.seq)
    out = []
    sha = _claimed_attestation_sha(event)
    if not sha:
        return (Problem("verification_row_cites_no_attestation",
                        f"{event.short_id} at seq {seq} names no attestation sha256",
                        sid, seq),)
    witness = locate_witness(event, witness_dir)
    if witness is None:
        out.append(Problem("verification_witness_missing",
                           f"no witness under {witness_dir} has last_line seq "
                           f"{seq} AND attestation_sha256 {sha[:12]}", sid, seq))
    attestation = locate_attestation(sha, witness, roots)
    if attestation is None:
        out.append(Problem("attestation_file_missing_or_sha_mismatch",
                           f"no attestation file hashing to {sha[:12]} was found "
                           f"(witness path or {[str(r) for r in roots]})", sid, seq))
        return tuple(out)
    text = attestation.read_text(encoding="utf-8", errors="replace")
    if sid not in text:
        out.append(Problem("attestation_supplement_id_mismatch",
                           f"{attestation.name} never names {sid}", sid, seq))
    sealed = _sealed_sha_before(chain, event)
    if sealed and sealed not in text:
        out.append(Problem("attestation_sealed_sha_mismatch",
                           f"{attestation.name} never restates the sealed sha256 "
                           f"{sealed[:12]} of the P4 it claims to have verified",
                           sid, seq))
    if witness is not None:
        w_sid = witness.get("supplement_id")
        if w_sid and w_sid != sid:
            out.append(Problem("witness_supplement_id_mismatch",
                               f"witness names {w_sid}, row is {sid}", sid, seq))
        w_sealed = witness.get("sealed_sha256")
        if w_sealed and sealed and w_sealed != sealed:
            out.append(Problem("witness_sealed_sha_mismatch",
                               "witness sealed_sha256 differs from the P4's",
                               sid, seq))
    return tuple(out)


def current_dependency_check(text: str, run_id: str, *,
                             witness_dir: Path = WITNESS_DIR,
                             roots=ATTESTATION_ROOTS) -> CheckReport:
    """Tier B: what the NEXT start of `run_id` depends on."""
    problems = []
    checked = []
    chains, refusal = _resolve(text)
    if refusal is not None:
        return CheckReport(False, (Problem("chain_unresolvable", refusal, run_id),),
                           ("chain resolution",))
    checked.append("chain resolution")
    try:
        _oc.assert_no_owner_hold(text, run_id)
        checked.append("owner hold")
    except _oc.OwnerControlRefusal as exc:
        problems.append(Problem(exc.code, exc.detail, run_id))
    chain = chains.get(run_id)
    if chain is not None:
        for event in verification_rows(chain):
            checked.append(f"binding of {event.short_id} seq {event.row.seq}")
            problems.extend(verify_binding(chain, event, witness_dir=witness_dir,
                                           roots=roots))
    return CheckReport(not problems, tuple(problems), tuple(checked))


def witness_chain_problems(witness_dir: Path = WITNESS_DIR) -> tuple:
    """The witness hash chain, judged by CONTENT first and by name second.

    Each witness records `previous_sha256` -- the registry hash the
    previous witness certified. The chain is INTACT when that hash is the
    `sha256` of some earlier witness; which file the `previous_witness`
    name points at is a filing convenience. Three outcomes:

        witness_chain_mismatch        previous_sha256 matches NO witness:
                                      an append happened that no witness
                                      certified -- an integrity gap
        witness_previous_name_mismatch the hash resolves to a witness, but
                                      not the one named -- a filing defect
                                      (measured 2026-09-07: the S001 T1
                                      witness names the P4 witness while
                                      its hash is the F3 witness's)
        witness_chain_gap             the named predecessor file is absent
    """
    if not witness_dir.is_dir():
        return (Problem("witness_dir_missing", str(witness_dir)),)
    by_name = {}
    for path in sorted(witness_dir.glob("*.json")):
        try:
            by_name[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:                               # noqa: BLE001
            return (Problem("witness_unreadable", f"{path.name}: {exc}"),)
    by_sha = {}
    for name, data in by_name.items():
        if data.get("sha256"):
            by_sha.setdefault(data["sha256"], []).append(name)
    out = []
    for name, data in by_name.items():
        prev = data.get("previous_witness")
        want = data.get("previous_sha256")
        if not prev and not want:
            continue
        holders = by_sha.get(want, [])
        if not holders:
            out.append(Problem("witness_chain_mismatch",
                               f"{name}.previous_sha256 {str(want)[:12]} is the "
                               "sha256 of no witness: an uncertified append"))
            continue
        if prev and prev not in by_name:
            out.append(Problem("witness_chain_gap",
                               f"{name} names previous {prev}, which is absent "
                               f"(its hash resolves to {holders})"))
        elif prev and prev not in holders:
            out.append(Problem("witness_previous_name_mismatch",
                               f"{name} names previous {prev} but its "
                               f"previous_sha256 is the sha256 of {holders}"))
    return tuple(out)


def history_health(text: str, *, witness_dir: Path = WITNESS_DIR,
                   roots=ATTESTATION_ROOTS) -> CheckReport:
    """Tier C: every chain's bindings plus the witness hash chain. Reported,
    never a gate."""
    problems = []
    checked = []
    chains, refusal = _resolve(text)
    if refusal is not None:
        return CheckReport(False, (Problem("chain_unresolvable", refusal),),
                           ("chain resolution",))
    for sid in sorted(chains):
        chain = chains[sid]
        for event in verification_rows(chain):
            checked.append(f"{sid} {event.short_id} seq {event.row.seq}")
            problems.extend(verify_binding(chain, event, witness_dir=witness_dir,
                                           roots=roots))
    checked.append("witness chain")
    problems.extend(witness_chain_problems(witness_dir))
    return CheckReport(not problems, tuple(problems), tuple(checked))
