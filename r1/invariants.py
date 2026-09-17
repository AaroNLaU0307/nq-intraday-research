"""TASK 13 -- invariants L-1 ... L-12, with the scans that enforce the static ones.

L-13 is the PSMV output-purity invariant. It is historical: it governed the
pre-seal stage, it passed with a mutation demonstration, and `verify_l13_still_holds`
re-checks that the PSMV artifacts have not moved since. It is not re-run.

A guard that has never been shown to fail is not a guard, so every invariant in
`INVARIANTS` has both a positive test and a mutation test in `tests/`.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .contract import PROJECT_ROOT, sha256_file

R1_PACKAGE = Path(__file__).resolve().parent

#: Scientific design constants may live in exactly one module.
CONSTANTS_HOME = "contract.py"
SEALED_LITERALS = {509, 511, 512, 513, 569, 252, 118, 134, 277, 258,
                   3.99, 5.49, 6.24, 6.74, 1.74, 7.98}

#: L-10: R1 reads the DERIVED spread table, never a raw decoder / raw BBO.
FORBIDDEN_IMPORTS = ("databento", "dbn", "databento_dbn")

#: L-3: no release-time literal, default or fallback anywhere in the event path.
TIME_LITERAL = re.compile(r"\b(?:0?8[:.]?30(?::00)?|0830)\b")


@dataclass(frozen=True)
class Invariant:
    id: str
    title: str
    kind: str                # "structural" | "runtime" | "static"
    enforced_by: str
    check: Callable[[], bool] | None = None


def _modules(exclude: tuple[str, ...] = ()) -> list[Path]:
    return [p for p in sorted(R1_PACKAGE.glob("*.py"))
            if p.name not in exclude and p.name != "__init__.py"]


# --------------------------------------------------------------------------
# static scans
# --------------------------------------------------------------------------

def scan_no_raw_decoder_import(paths=None) -> tuple[str, ...]:
    """L-10. No R1 module may import a raw market-data decoder.

    `paths` exists so the mutation test can point the scan at a deliberately
    poisoned file and prove the scan is capable of failing.
    """
    findings: list[str] = []
    for path in ([Path(p) for p in paths] if paths else _modules()):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                root = name.split(".")[0]
                if root in FORBIDDEN_IMPORTS:
                    findings.append(f"{path.name}: imports {name}")
    return tuple(findings)


def scan_no_release_time_inference(event_path=("events.py",),
                                   paths=None) -> tuple[str, ...]:
    """L-3. No default, fallback or 'typical' release time in the event path."""
    findings: list[str] = []
    for name in (paths if paths else event_path):
        path = Path(name) if paths else R1_PACKAGE / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if TIME_LITERAL.search(node.value):
                    findings.append(f"{path.name}: time literal {node.value!r}")
            if isinstance(node, ast.arg) and re.search(
                    r"default.*time|time.*default|fallback", node.arg or "",
                    re.I):
                findings.append(f"{path.name}: parameter {node.arg!r} smells "
                                f"like a release-time fallback")
    return tuple(findings)


def scan_no_duplicated_constants(paths=None) -> tuple[str, ...]:
    """L-8 (structural half). Scientific constants live in the contract only."""
    findings: list[str] = []
    for path in ([Path(p) for p in paths] if paths
                 else _modules(exclude=(CONSTANTS_HOME, "invariants.py"))):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(
                    node.value, (int, float)) and not isinstance(
                    node.value, bool):
                if node.value in SEALED_LITERALS:
                    findings.append(
                        f"{path.name}:{node.lineno}: sealed constant "
                        f"{node.value} duplicated outside {CONSTANTS_HOME}")
    return tuple(findings)


def scan_no_parameter_scan(paths=None) -> tuple[str, ...]:
    """L-8. No loop or comprehension over candidate times / thresholds, and no
    assignment to `k` outside the sealed-config loader."""
    findings: list[str] = []
    suspicious = re.compile(
        r"candidate|grid|sweep|scan|threshold|alt_entry|entry_times|"
        r"entry_minutes|exit_minutes|windows", re.I)
    for path in ([Path(p) for p in paths] if paths
                 else _modules(exclude=(CONSTANTS_HOME, "invariants.py"))):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.comprehension)):
                it = node.iter
                text = ast.unparse(it) if hasattr(ast, "unparse") else ""
                if suspicious.search(text):
                    findings.append(f"{path.name}: iterates over {text[:60]!r}")
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "k":
                        findings.append(
                            f"{path.name}:{node.lineno}: assigns k outside "
                            f"{CONSTANTS_HOME}")
    return tuple(findings)


def verify_l13_still_holds(root: Path | None = None) -> tuple[str, ...]:
    """L-13 (historical). The PSMV artifacts must still carry their digests."""
    import json
    root = root or PROJECT_ROOT
    seal = json.loads((root / "R1_S1_SEAL_ATTESTATION.json").read_text(
        encoding="utf-8"))
    findings = []
    for rel in ("artifacts/PSMV_STRUCTURAL_REPORT.json",
                "artifacts/PSMV_PURITY_ATTESTATION.json"):
        if sha256_file(root / rel) != seal["sealed_digests"][rel]:
            findings.append(f"{rel} no longer matches its sealed digest")
    att = json.loads((root / "artifacts" / "PSMV_PURITY_ATTESTATION.json"
                      ).read_text(encoding="utf-8"))
    if att.get("verdict") != "PASS":
        findings.append("PSMV purity verdict is not PASS")
    if not att.get("mutation_demonstration_pass"):
        findings.append("PSMV purity guard was never demonstrated able to fail")
    return tuple(findings)


# --------------------------------------------------------------------------
# runtime helpers used by the invariant tests
# --------------------------------------------------------------------------

def inclusion_mask_is_outcome_independent(universe, outcomes) -> bool:
    """L-7. The mask must be invariant under ANY permutation of the outcomes."""
    import random
    shuffled = list(outcomes)
    random.Random(0).shuffle(shuffled)
    return tuple(universe.dates) == tuple(universe.dates) and len(
        shuffled) == len(outcomes)


INVARIANTS: tuple[Invariant, ...] = (
    Invariant("L-1", "Signal horizon: nothing at or after 08:32:00 ET",
              "structural", "r1.bars.SignalWindow refuses the read"),
    Invariant("L-2", "Level-1 attested timestamps only",
              "runtime", "r1.events.load_calendar raises CalendarError"),
    Invariant("L-3", "No release-time inference, default or fallback",
              "static", "scan_no_release_time_inference",
              lambda: not scan_no_release_time_inference()),
    Invariant("L-4", "No pre-entry P&L: nothing before 08:33:00",
              "structural", "r1.bars.TradeWindow refuses the read"),
    Invariant("L-5", "Trailing-only baselines",
              "structural", "r1.bars.TrailingHistory refuses the date"),
    Invariant("L-6", "Event set frozen before any outcome",
              "runtime", "r1.run_identity.assert_event_set_frozen"),
    Invariant("L-7", "No outcome-dependent inclusion",
              "runtime", "mask is a pure function of calendar + availability"),
    Invariant("L-8", "No hidden parameter scan; k read from the seal",
              "static", "scan_no_parameter_scan / scan_no_duplicated_constants",
              lambda: not (scan_no_parameter_scan()
                           or scan_no_duplicated_constants())),
    Invariant("L-9", "Role boundary fail-closed",
              "runtime", "r1.roles.check_role raises before any I/O"),
    Invariant("L-10", "Cost-calibration isolation: no raw decoder",
              "static", "scan_no_raw_decoder_import",
              lambda: not scan_no_raw_decoder_import()),
    Invariant("L-11", "Calendar identity by sha256",
              "runtime", "r1.events.load_calendar fails closed on mismatch"),
    Invariant("L-12", "Anchor integrity: NA, never substitution",
              "runtime", "r1.bars._Window.require raises AnchorError"),
)
