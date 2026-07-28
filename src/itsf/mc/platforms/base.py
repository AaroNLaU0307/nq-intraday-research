"""Shared trailing-floor engine (MAIN-AGENT OWNED, read-only for subagents).

Both platforms share the drawdown GEOMETRY but not lifecycle parameters
(frozen review conclusion): floor rises with end-of-day balance, locks at a
cap; breach is evaluated in REAL TIME against equity including unrealized
P&L (Topstep: official; Lucid: frozen conservative assumption V-A).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrailingFloorEngine:
    floor: float                # current MLL threshold (account-balance units)
    trail_distance: float       # e.g. 2000
    lock_at: float              # Lucid 50100 / Topstep combine 50000 / XFA 0

    def eod_update(self, eod_balance: float) -> float:
        """floor_next = min(lock_at, max(floor, eod_balance - trail_distance))"""
        self.floor = min(self.lock_at, max(self.floor, eod_balance - self.trail_distance))
        return self.floor

    def set_floor(self, value: float) -> None:
        """Payout effects (Lucid -> 50100; Topstep XFA -> 0) — frozen semantics."""
        self.floor = value

    def breached_intraday(self, equity_path: list[float]) -> int | None:
        """Return first index where equity (incl. unrealized, adverse path)
        touches/crosses the floor, else None. Frozen: touch == breach."""
        for i, eq in enumerate(equity_path):
            if eq <= self.floor:
                return i
        return None


# Unified breach-loss settlement (main-agent ruling R1, ADJUDICATIONS.md
# 2026-07-28). Frozen MC SS2.2: "损失按触发价 ± adverse slippage". Convention:
# settle at the WORSE of (floor, trigger minute's adverse-extreme equity),
# minus per-contract adverse slippage. Interim slip = Conservative scenario
# 2 ticks x $0.50 = $1.00 per micro; finalized at cost-model lock pre-run.
BREACH_ADVERSE_SLIP_USD_PER_MICRO = 1.0


def breach_settlement(floor: float, adverse_equity_at_trigger: float,
                      n_micros: int,
                      slip_usd_per_micro: float = BREACH_ADVERSE_SLIP_USD_PER_MICRO,
                      ) -> float:
    """Post-breach account balance — single convention for ALL engines."""
    return min(floor, adverse_equity_at_trigger) - n_micros * slip_usd_per_micro
