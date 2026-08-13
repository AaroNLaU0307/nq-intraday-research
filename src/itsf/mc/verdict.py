"""Mechanical Checkpoint-0 verdict table application.

Frozen sources:
  - S0 SS10.4: mutually exclusive, exhaustive, ORDERED verdict table
    STOP → GO → beta → alpha (alpha is the fallback category).
  - MC1 SS0 + SS2.5: ALL quantifiers (STOP's universal, GO's existential,
    the beta combo ranges) act ONLY over the frozen Primary decision set
    (2 lifecycles × P2). Callers must pass ONLY Primary combos here;
    Sensitivity/Excluded combos may never flip a verdict and must not
    appear in `primary`.
  - platform_params gate2_cost_guard: if the GO condition is satisfied
    ONLY by Lucid combos (no Topstep combo satisfies it), the verdict is
    downgraded to boundary-zone alpha.

Statistics are epistemic-layer quantiles of monthly prop_operating_EV
(MC1 SS4.4 / SS5); this module performs no computation on them, it only
applies the frozen table.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerdictInput:
    """Epistemic-layer decision statistics for ONE Primary combo."""
    p5_cons: float          # Conservative epistemic P5
    median_cons: float      # Conservative epistemic median (reported)
    median_stress: float    # Stress epistemic median
    p95_cons: float         # Conservative epistemic P95
    feasible: bool          # integer sizing / frequency / payout path OK (MC-confirmed)
    platform: str           # 'lucid' | 'topstep'
    engine: str             # 'E1' | 'E2'
    # DR-5 R2: the oracle selection channel this combo's statistics were
    # computed on. Checkpoint-0 accepts ONLY the frozen primary channel
    # (S0 §7 L133: θ 主 0.5、副 0.3，不得事后升格) — enforced by the
    # consumer gate; carried here so the seal candidate binds it.
    channel: str            # e.g. 'theta_0.5'


@dataclass(frozen=True)
class VerdictResult:
    verdict: str            # 'STOP' | 'GO' | 'beta' | 'alpha'
    reason: str


def _go_ev_met(v: VerdictInput) -> bool:
    """GO EV evidence on ONE E1 combo: Conservative P5 > 0 AND Stress
    median >= 0 (same combo — frozen anti-cherry-pick patch, S0 SS10.4)."""
    return v.engine == "E1" and v.p5_cons > 0 and v.median_stress >= 0


def apply_verdict(primary: dict[str, VerdictInput]) -> VerdictResult:
    """Apply the frozen verdict table in order over the Primary set only.

    # frozen: S0 SS10.4 order STOP → GO → beta → alpha
    # frozen: MC1 SS0 quantifier scope = Primary set (MC1 SS2.5)
    # frozen: platform_params gate2_cost_guard (Lucid-only GO → alpha)
    """
    if not primary:
        raise ValueError("primary decision set is empty — cannot apply verdict "
                         "(quantifiers are scoped to MC1 SS2.5 Primary combos)")

    # 1) STOP: ALL Primary combos (E1 and E2) Conservative P95 <= 0
    #    # frozen: S0 SS10.4 row 1 (universal quantifier over Primary only)
    if all(v.p95_cons <= 0 for v in primary.values()):
        return VerdictResult(
            "STOP",
            "all Primary combos (E1+E2) have Conservative epistemic P95 <= 0 "
            "(S0 SS10.4 row 1, scope MC1 SS0)")

    # 2) GO: EXISTS one E1 combo with Conservative P5 > 0 AND Stress
    #    median >= 0 AND feasibility confirmed — same combo throughout.
    #    # frozen: S0 SS10.4 row 2
    go_ids = [cid for cid, v in primary.items() if _go_ev_met(v) and v.feasible]
    if go_ids:
        if all(primary[c].platform == "lucid" for c in go_ids):
            # frozen: platform_params gate2_cost_guard — Lucid execution
            # costs unconfirmed until Gate 2 PoC; Lucid cannot
            # independently trigger GO → downgrade to boundary-zone alpha.
            return VerdictResult(
                "alpha",
                "gate2_cost_guard: GO condition satisfied only via Lucid "
                f"combos {sorted(go_ids)} with no Topstep combo satisfying it; "
                "verdict downgraded to boundary-zone alpha "
                "(platform_params gate2_cost_guard)")
        return VerdictResult(
            "GO",
            f"E1 combo(s) {sorted(go_ids)} satisfy Conservative P5 > 0 AND "
            "Stress median >= 0 AND feasibility on the same combo "
            "(S0 SS10.4 row 2)")

    # 3) beta (not STOP, not GO):
    #    (a) some E2 combo has Conservative P5 > 0 while NO E1 combo does; or
    #    (b) some E1 combo meets the GO EV evidence but fails feasibility.
    #    # frozen: S0 SS10.4 row 3
    e1_p5_pos = any(v.engine == "E1" and v.p5_cons > 0 for v in primary.values())
    e2_p5_pos = sorted(cid for cid, v in primary.items()
                       if v.engine == "E2" and v.p5_cons > 0)
    if e2_p5_pos and not e1_p5_pos:
        return VerdictResult(
            "beta",
            f"E2 combo(s) {e2_p5_pos} have Conservative P5 > 0 while no E1 "
            "combo does (S0 SS10.4 row 3, first arm)")
    ev_not_feasible = sorted(cid for cid, v in primary.items()
                             if _go_ev_met(v) and not v.feasible)
    if ev_not_feasible:
        return VerdictResult(
            "beta",
            f"E1 combo(s) {ev_not_feasible} meet the GO EV evidence but fail "
            "feasibility (S0 SS10.4 row 3, second arm)")

    # 4) alpha: fallback category — everything else.
    #    # frozen: S0 SS10.4 row 4 (exhaustive by construction)
    return VerdictResult(
        "alpha",
        "no STOP/GO/beta condition met; boundary-zone alpha fallback "
        "(S0 SS10.4 row 4)")
