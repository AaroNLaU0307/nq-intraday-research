"""Account-level sizing and one-account day loop for the MC simulator.

Frozen sources implemented here:
  - MC1 SS3 sizing policy set P1–P4, buffer definition (MLL-anchored),
    integer-contract formula, n=0 skip counting, one trade per day,
    close-path EOD settlement, adverse-path breach checking.
  - MC1 SS2.5: Primary sizing = P2 ($100 per trade).
  - platform_params lucidflex_50k funded.absolute_max_position.micros = 40
    (absolute micro cap used in the integer formula).
  - MC1 SS5 inner randomness source (1): start-phase offset ONLY — exposed
    here as the `start_offset` argument of run_account.

GUARD DISCIPLINE: the simulation helpers below run on SYNTHETIC paths only
(tests/conftest.py generators) and therefore do NOT call the real-run gate.
The single entry point for real market data is run_real_study(), which
calls itsf.guards.assert_real_run_allowed() and is blocked today
(G9 hard_run_blocker + second-copy attestation missing).
"""
from __future__ import annotations

import math
from typing import Mapping, Protocol, Sequence

from itsf.contracts import AccountEvent, TradePathRecord
from itsf.mc.platforms.base import TrailingFloorEngine

# Absolute position caps are PER-PLATFORM (ruling R2, ADJUDICATIONS.md):
# Lucid funded 40 micros / Topstep 50 micros. platform.max_contracts_today()
# MUST already embed its own absolute cap; n_micros only adds an optional
# extra clip when a caller passes one explicitly.
LUCID_ABSOLUTE_MAX_MICROS = 40    # frozen: platform_params lucidflex_50k funded
TOPSTEP_ABSOLUTE_MAX_MICROS = 50  # frozen: platform_params topstep_50k

# frozen: MC1 SS2.5 — Primary sizing policy
PRIMARY_POLICY = "P2"

SIZING_POLICIES = ("P1", "P2", "P3", "P4")


class PlatformLike(Protocol):
    """Minimal surface the account loop needs from a platform lifecycle.

    The full lifecycle state machines (evaluation/funded/XFA, payouts,
    fees, DLL) are owned elsewhere; this loop only consumes the mutable
    account state and the day's scaling-tier contract cap.
    """
    balance: float
    engine: TrailingFloorEngine

    def max_contracts_today(self) -> int:
        """Micro cap from the scaling tier fixed at the PREVIOUS session's
        close (frozen: MC1 SS3 — 档位取上一 session 收盘值, 盘中不变)."""
        ...


def buffer_at_entry(pre_entry_equity: float, current_floor: float) -> float:
    """buffer_at_entry = 10:00 pre-entry realtime equity − current MLL floor.

    Anchored to the MLL ONLY — DLL is not an account death line and never
    enters the buffer (frozen: MC1 SS3 buffer v0.4 唯一化). No pre-deduction
    of the coming trade's costs.
    """
    return pre_entry_equity - current_floor


def risk_budget_usd(policy: str, buffer: float) -> float:
    """Per-trade USD risk budget for the frozen sizing policy set.

    # frozen: MC1 SS3 — P1 $75; P2 $100 (Primary); P3 4% of buffer;
    # P4 ladder >$1500→$100 / $800–1500→$75 / <$800→$50
    """
    if policy == "P1":
        return 75.0
    if policy == "P2":
        return 100.0
    if policy == "P3":
        return 0.04 * buffer
    if policy == "P4":
        if buffer > 1500.0:
            return 100.0
        if buffer >= 800.0:
            return 75.0
        return 50.0
    raise ValueError(f"unknown sizing policy: {policy!r} (frozen set {SIZING_POLICIES})")


def n_micros(risk_budget: float, sizing_anchor_usd: float,
             scaling_cap_micros: int,
             absolute_max_micros: int | None = None) -> int:
    """Integer micro-contract count.

    # frozen: MC1 SS3 — n = min(floor(risk_budget ÷ sizing_anchor_usd),
    #                            当日 scaling 档位 micro 上限, absolute_max_micros)
    Ruling R2: the absolute cap is per-platform (Lucid 40 / Topstep 50) and is
    normally already embedded in the platform's scaling cap; pass
    absolute_max_micros only when the caller wants an explicit extra clip.
    n == 0 means the day is SKIPPED and the skip is counted upstream.
    """
    if sizing_anchor_usd <= 0:
        raise ValueError("sizing_anchor_usd must be positive")
    if risk_budget <= 0:
        return 0
    raw = math.floor(risk_budget / sizing_anchor_usd)
    n = min(raw, int(scaling_cap_micros))
    if absolute_max_micros is not None:
        n = min(n, int(absolute_max_micros))
    return max(0, n)


def run_account(world_days: Sequence[str], platform: PlatformLike,
                paths_by_day: Mapping[str, TradePathRecord], policy: str,
                start_offset: int = 0) -> tuple[list[AccountEvent], dict]:
    """Simulate one account over a bootstrap world's day-id sequence.

    SYNTHETIC-ONLY helper: callers feed paths built from tests/conftest.py
    generators; this function intentionally does NOT call the real-run
    guard (see run_real_study).

    - `start_offset` skips the first `start_offset` template days — the ONLY
      inner randomness source for the Oracle primary config
      (frozen: MC1 SS5 内层随机源 (1) start-phase offset).
    - At most one trade per day, no overnight (frozen: MC1 SS3), so
      pre-entry equity == balance.
    - Breach check per minute on the ADVERSE path scaled by n; touch ==
      breach == immediate account death, loss taken at the trigger minute's
      adverse mark (frozen: MC1 SS3 / SS2.2 adverse-path violation).
    - Non-breach days settle on the CLOSE path final P&L and then run the
      EOD floor update (frozen: MC1 SS3 close-path 日终结算;
      platform_params lucidflex_50k.mll_engine eod_update geometry).
    """
    if start_offset < 0:
        raise ValueError("start_offset must be >= 0")
    events: list[AccountEvent] = []
    summary = {"days": 0, "trades": 0, "skips": 0, "no_path_days": 0,
               "breached": False, "final_balance": platform.balance,
               "final_floor": platform.engine.floor}
    phase = getattr(platform, "phase", "funded")

    for day in list(world_days)[start_offset:]:
        summary["days"] += 1
        path = paths_by_day.get(day)
        if path is None:                       # no-trade template day
            summary["no_path_days"] += 1
            platform.engine.eod_update(platform.balance)
            events.append(AccountEvent(day=day, phase=phase,
                                       balance=platform.balance,
                                       floor=platform.engine.floor,
                                       notes="no_trade"))
            continue

        buf = buffer_at_entry(platform.balance, platform.engine.floor)
        budget = risk_budget_usd(policy, buf)
        n = n_micros(budget, path.sizing_anchor_usd, platform.max_contracts_today())
        if n == 0:                             # frozen: MC1 SS3 n=0 → 跳过并计数
            summary["skips"] += 1
            platform.engine.eod_update(platform.balance)
            events.append(AccountEvent(day=day, phase=phase,
                                       balance=platform.balance,
                                       floor=platform.engine.floor,
                                       notes="skip_n0"))
            continue

        summary["trades"] += 1
        # adverse-path realtime equity incl. unrealized, scaled by n
        equity_path = [platform.balance + n * pnl for pnl in path.mtm_adverse_pnl_1m]
        hit = platform.engine.breached_intraday(equity_path)
        if hit is not None:                    # immediate death, unified R1
            from itsf.mc.platforms.base import breach_settlement
            platform.balance = breach_settlement(
                platform.engine.floor, equity_path[hit], n)
            summary["breached"] = True
            events.append(AccountEvent(day=day, phase="dead",
                                       balance=platform.balance,
                                       floor=platform.engine.floor,
                                       breached=True,
                                       notes=f"mll_breach_minute_{hit}_n_{n}"))
            break

        platform.balance += n * path.final_pnl_per_contract   # close-path settle
        platform.engine.eod_update(platform.balance)
        events.append(AccountEvent(day=day, phase=phase,
                                   balance=platform.balance,
                                   floor=platform.engine.floor,
                                   notes=f"traded_n_{n}"))

    summary["final_balance"] = platform.balance
    summary["final_floor"] = platform.engine.floor
    return events, summary


def run_real_study(*args, g9_flag=None, second_copy_flag=None, **kwargs):
    """SOLE entry point for any real-market-data study computation.

    Calls the frozen run gate first; flag paths injectable so gate tests
    stay hermetic (defaults = production flags, both attested 2026-07-29).
    # frozen: platform_params execution_costs.s0_cost_handoff.hard_run_blocker
    # frozen: charter data-governance second-copy clause (see itsf.guards)
    """
    from itsf import guards
    guards.assert_real_run_allowed(g9_flag or guards.G9_FLAG,
                                   second_copy_flag or guards.SECOND_COPY_FLAG)
    raise NotImplementedError(
        "real study runner is not implemented; all current simulation "
        "helpers are synthetic-only and must not reach this path")
