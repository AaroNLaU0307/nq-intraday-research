"""TASK 11 -- OD-3 pre-reveal power-gate machinery. BUILT, NOT RUN.

Sealed I.3, in order:

    STEP 1  s_hat = sd of  d_ctrl * (O(09:29) - O(08:33))  on NON-EVENT days at
            the same clock minutes -- CONTROL C2's dispersion. It is not the R1
            outcome, and reading it exposes no R1 target metric.
    STEP 2  SE_hat = s_hat / sqrt(n_final)
            MDE_80 = M + 2.486 * SE_hat        MDE_50 = M + 1.645 * SE_hat
    STEP 3  Report M, s_hat, SE_hat, MDE_80, MDE_50 to Aaron, who decides
            PROCEED_TO_REVEAL or PARK_FOR_INSUFFICIENT_POWER.

**The separation that matters.** Every function here takes floats and the
sealed contract. There is no parameter, anywhere in this module, through which
a Primary result object could arrive -- no event arm, no trade, no mean, no
sign distribution, no verdict. `prove_gate_independence()` proves it by walking
this module's import graph and its signatures, and the test suite fails the
build if the dependency graph ever allows accidental access.

**This module does not run the gate.** `s_hat` must come from real non-event C2
dispersion, which needs real Development bars; those are blocked until S3
(`r1.bars.DevelopmentBarSource`). `refuse_real_gate()` states the boundary
explicitly for callers that try.
"""
from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from math import sqrt
from pathlib import Path

from .contract import SealedContract
from .errors import AuthorityError, R1Error

#: Sealed I.3 constants. One-sided 95 %, 80 % / 50 % power.
Z_80: float = 2.486
Z_50: float = 1.645

PROCEED = "PROCEED_TO_REVEAL"
PARK = "PARK_FOR_INSUFFICIENT_POWER"

#: Names no object reaching this module may carry. The gate is outcome-blind.
FORBIDDEN_INPUT_TYPES = ("TradeResult", "C1Result", "Verdict", "PrimaryEvidence",
                         "EventUniverse", "Signal", "E4Result")


@dataclass(frozen=True)
class PowerGatePacket:
    """The bounded Owner-decision packet of sealed I.3 STEP 3.

    It carries the design's RESOLVING POWER and nothing about the event arm.
    `owner_decision` is None until Aaron fills it in: the machinery never
    decides, and never recommends.
    """
    materiality_m_usd: float
    s_hat: float
    n_final: int
    se_hat: float
    mde_50: float
    mde_80: float
    ci_half_width_would_exceed_m: bool
    owner_decision: str | None = None
    note: str = ("outcome-blind: computed from control C2 dispersion only; no "
                 "R1 event-arm quantity entered this packet")

    def with_owner_decision(self, decision: str) -> "PowerGatePacket":
        if decision not in (PROCEED, PARK):
            raise R1Error(f"owner decision must be {PROCEED} or {PARK}")
        return PowerGatePacket(
            materiality_m_usd=self.materiality_m_usd, s_hat=self.s_hat,
            n_final=self.n_final, se_hat=self.se_hat, mde_50=self.mde_50,
            mde_80=self.mde_80,
            ci_half_width_would_exceed_m=self.ci_half_width_would_exceed_m,
            owner_decision=decision, note=self.note)


def build_packet(s_hat: float, n_final: int,
                 contract: SealedContract) -> PowerGatePacket:
    """Sealed I.3 STEP 2, on numbers only. No outcome object can reach here."""
    if not isinstance(s_hat, (int, float)) or isinstance(s_hat, bool):
        raise R1Error("s_hat must be a number -- the gate takes dispersion, "
                      "never an outcome object")
    if s_hat <= 0:
        raise R1Error("s_hat must be positive")
    if n_final < 2:
        raise R1Error("n_final must be at least 2 for a standard error")
    se = float(s_hat) / sqrt(float(n_final))
    m = contract.materiality_m_usd
    return PowerGatePacket(
        materiality_m_usd=m, s_hat=float(s_hat), n_final=int(n_final),
        se_hat=se, mde_50=m + Z_50 * se, mde_80=m + Z_80 * se,
        # sealed I.3: if the CI half-width would exceed M the design cannot
        # distinguish supported from excluded, and the only honest outcomes are
        # INSUFFICIENT_EVIDENCE or PARKED.
        ci_half_width_would_exceed_m=(1.96 * se) > m)


def refuse_real_gate() -> None:
    """The real gate is an S3 act. State it, do not half-run it."""
    raise AuthorityError(
        "the OD-3 power gate needs REAL non-event C2 dispersion, which needs "
        "real Development bars. S2 BUILD authorizes neither. The gate is "
        "built, tested on synthetic dispersion, and left unexecuted.")


def prove_gate_independence(module_paths=None) -> dict[str, object]:
    """Structural proof that the gate path cannot reach a Primary result.

    Walks this module's AST: every import, every annotation and every default.
    If any outcome-carrying type appears, the proof FAILS -- which is the
    build-completeness condition the S2 authorization names.
    """
    here = Path(__file__).resolve()
    paths = [Path(p) for p in module_paths] if module_paths else [here]
    findings: list[str] = []
    imported: set[str] = set()

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
                for alias in node.names:
                    if alias.name in FORBIDDEN_INPUT_TYPES:
                        findings.append(
                            f"{path.name}: imports outcome type {alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
        src = path.read_text(encoding="utf-8")
        for name in FORBIDDEN_INPUT_TYPES:
            # a bare mention in a string (this docstring) is not a dependency;
            # an annotation or a call is.
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == name:
                    findings.append(f"{path.name}: references {name}")
                elif isinstance(node, ast.Attribute) and node.attr == name:
                    findings.append(f"{path.name}: references {name}")
        del src

    for forbidden_module in ("r1.trade", "r1.verdict", "r1.signal",
                            ".trade", ".verdict", ".signal", ".events"):
        if forbidden_module in imported:
            findings.append(f"imports outcome-bearing module {forbidden_module}")

    # signatures: no parameter may be annotated with an outcome type
    import sys
    mod = sys.modules[__name__]
    for fn_name, fn in vars(mod).items():
        if not callable(fn) or not hasattr(fn, "__module__"):
            continue
        if getattr(fn, "__module__", None) != __name__:
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):       # pragma: no cover - builtins
            continue
        for pname, param in sig.parameters.items():
            ann = param.annotation
            if isinstance(ann, str) and any(t in ann for t in FORBIDDEN_INPUT_TYPES):
                findings.append(f"{fn_name}({pname}) accepts an outcome type")

    return {"independent": not findings, "findings": tuple(findings),
            "imports": tuple(sorted(imported))}
