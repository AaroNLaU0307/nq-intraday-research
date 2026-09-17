"""TASK 5 -- the sealed primary trade and its P&L.

    enter  O(08:33) in direction d_event
    exit   O(09:29), a PRE-SCHEDULED timed exit that requires no observation
    size   one MNQ,  no stop,  never overnight,  56 minutes

    Y_net  = USD P&L per 1 MNQ under a cost scenario      (sealed F.1)
    Y_norm = d * (O(09:29) - O(08:33)) / ADR14            (descriptive only)

L-4 is structural: everything here reads through a `TradeWindow`, which refuses
any bar before 08:33:00. Perturbing C(08:29), O(08:30), C(08:31) or any 08:32
field cannot change `Y_net`, because the P&L path cannot see them.

The Primary has **no stop**, deliberately (sealed C.1 / R.2): a stop would add a
parameter and an optimisation surface. So this module has no stop-fill path at
all -- not a disabled one, an absent one.

For the future prop assessment (sealed R.2) each trade also emits its
minute-level CLOSE PATH and ADVERSE PATH (long uses the minute low, short the
minute high), because Topstep and Lucid breach on real-time equity including
unrealized P&L -- a day that closes green can still be a breach.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .bars import BarSource, TradeWindow
from .contract import SealedContract
from .costs import entry_fill, points_to_usd, scenario, timed_exit_fill
from .errors import R1Error


@dataclass(frozen=True)
class TradeResult:
    date_et: str
    direction: int
    cost_scenario: str
    entry_ref: float
    exit_ref: float
    entry_fill: float
    exit_fill: float
    gross_points: float          # d * (exit_ref - entry_ref), before costs
    net_points: float            # d * (exit_fill - entry_fill), after friction
    y_net_usd: float             # net_points -> USD, minus the platform fee
    close_path_usd: tuple[float, ...] = field(default=())
    adverse_path_usd: tuple[float, ...] = field(default=())
    mae_usd: float = 0.0         # max adverse excursion, USD per 1 MNQ
    mfe_usd: float = 0.0         # max favourable excursion
    y_norm: float | None = None  # gross points / ADR14, descriptive only

    @property
    def holding_minutes(self) -> int:
        return len(self.close_path_usd)


def execute_trade(source: BarSource, date_et: str, direction: int,
                  contract: SealedContract, *,
                  cost_scenario: str = "Base",
                  adr14: float | None = None,
                  emit_paths: bool = True) -> TradeResult:
    """One event, one trade, one scenario. Reads nothing before O(08:33)."""
    if direction not in (1, -1):
        raise R1Error(f"direction must be +1 or -1 (E4 removes 0), got {direction!r}")
    scn = scenario(contract, cost_scenario)

    window = TradeWindow(source, date_et, contract)
    entry_bar = window.require(contract.entry_minute)
    exit_bar = window.require(contract.exit_minute)

    e_ref, x_ref = entry_bar.open, exit_bar.open
    e_fill = entry_fill(e_ref, direction, contract, cost_scenario)
    x_fill = timed_exit_fill(x_ref, direction, contract, cost_scenario)

    gross_points = direction * (x_ref - e_ref)
    net_points = direction * (x_fill - e_fill)
    y_net = points_to_usd(net_points, contract) - scn.platform_fee_rt_usd

    close_path: tuple[float, ...] = ()
    adverse_path: tuple[float, ...] = ()
    mae = mfe = 0.0
    if emit_paths:
        closes: list[float] = []
        adverses: list[float] = []
        for minute in range(contract.entry_minute, contract.exit_minute):
            bar = window.get(minute)
            if bar is None:
                continue
            # mark to market from the ENTRY FILL, so the path is what the
            # account would actually have shown (unrealized, fee not yet paid)
            closes.append(points_to_usd(direction * (bar.close - e_fill),
                                        contract))
            worst = bar.low if direction == 1 else bar.high
            adverses.append(points_to_usd(direction * (worst - e_fill),
                                          contract))
        close_path = tuple(closes)
        adverse_path = tuple(adverses)
        if adverses:
            mae = min(0.0, min(adverses))
            mfe = max(0.0, max(closes)) if closes else 0.0

    return TradeResult(
        date_et=date_et, direction=direction, cost_scenario=cost_scenario,
        entry_ref=e_ref, exit_ref=x_ref, entry_fill=e_fill, exit_fill=x_fill,
        gross_points=gross_points, net_points=net_points, y_net_usd=y_net,
        close_path_usd=close_path, adverse_path_usd=adverse_path,
        mae_usd=mae, mfe_usd=mfe,
        y_norm=(gross_points / adr14 if adr14 else None),
    )


def run_arm(source: BarSource, directed_events, contract: SealedContract, *,
            cost_scenario: str = "Base",
            emit_paths: bool = False) -> tuple[TradeResult, ...]:
    """Run one ARM: the Primary, C1 or C2 -- the same code path for all three.

    Sealed R.1 S2-5: controls are built in the SAME path as the Primary, so a
    divergence between them is impossible by construction.

    `directed_events` is an iterable of (date_et, direction).
    """
    return tuple(
        execute_trade(source, d, direction, contract,
                      cost_scenario=cost_scenario, emit_paths=emit_paths)
        for d, direction in directed_events)


def mean_y_net(results) -> float:
    vals = [r.y_net_usd for r in results]
    if not vals:
        raise R1Error("cannot take the mean of an empty arm")
    return sum(vals) / len(vals)
