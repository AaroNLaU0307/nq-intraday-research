"""Shared synthetic fixtures (MAIN-AGENT OWNED, read-only for subagents).

Real market data is FORBIDDEN in this phase (G9 hard_run_blocker + second-copy
gate). All tests build days from these deterministic generators.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

ET = ZoneInfo("America/New_York")


# ---------------------------------------------------------------------------
# QROS-CF tiers (DEC-0006 I4). Markers, not directories: the tier map in
# tests/tiers.py decides, the run gate selects `-m "not governance"`, and
# an unmapped file is tier B by default (in the gate, fail-closed).
# ---------------------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "validity: tier A research-validity test (in the run gate)")
    config.addinivalue_line(
        "markers", "safety: tier B execution-safety test (in the run gate)")
    config.addinivalue_line(
        "markers", "governance: tier C document/index/packet guard "
                   "(runs in CI; NEVER in the run gate; a red one is backlog)")


def pytest_collection_modifyitems(config, items):
    import tiers as _tiers

    for item in items:
        name = Path(str(item.fspath)).name
        if item.get_closest_marker("governance") is not None:
            continue                       # an explicit per-test marker wins
        item.add_marker(getattr(pytest.mark, _tiers.tier_of(name)))


@pytest.fixture(autouse=True)
def _suite_guard_real_ruled_roots():
    """SUITE-WIDE (conformance F4.1): no test anywhere may add/remove
    top-level entries under the REAL L-5 ruled roots. Tolerant of
    pre-existing real content; intolerant of any change across a test."""
    from itsf.contracts import RULED_ARCHIVE_ROOT, RULED_RUNS_ROOT
    # R5 incident guard: <repo>/runs joined the watch list after a fixture
    # mkdir briefly created it (empty; removed; disclosed in the packet).
    roots = (Path(RULED_RUNS_ROOT), Path(RULED_ARCHIVE_ROOT),
             REPO / "runs")

    def snap():
        return {r: (frozenset(p.name for p in r.iterdir())
                    if r.exists() else None) for r in roots}

    before = snap()
    yield
    after = snap()
    for r in roots:
        assert after[r] == before[r], (
            f"a test touched the REAL ruled root {r} — pass explicit "
            "tmp_path-based runs_root/archive_root overrides")


@pytest.fixture(autouse=True)
def _block_real_archive_reads(monkeypatch):
    """S0-closeout incident guard (2026-08-10): NO test may load bars from
    the REAL data archive, ever.

    Incident being prevented from recurring: after the ruled config sources
    landed, `RealChain.prepare` proceeds past config resolution, so a chain
    test that forgot its hermetic patches silently reached
    `DevelopmentSignalLoader.load_real` against the real quant-data archive
    (caught mid-run, process killed, no outcome values were computed or
    viewed; disclosed in the closeout packet). This fixture makes that
    failure LOUD and immediate for every test, permanently.

    Narrow by design: synthetic `job_dir`s under tmp_path stay usable —
    only the real archive tree is fenced.
    """
    from itsf.data.dbn_loader import DevelopmentSignalLoader

    real = DevelopmentSignalLoader.load_real

    def guarded(self, filename, source_format="dbn"):
        p = str(self.job_dir).lower()
        if "databento-archive" in p or p.startswith(r"c:\users\aaron\quant-data"):
            raise RuntimeError(
                "BLOCKED: test attempted to load real archive data "
                f"({self.job_dir}) — patch RealChain._ensure or use "
                "load_synthetic; real reads are forbidden in the suite")
        return real(self, filename, source_format)

    monkeypatch.setattr(DevelopmentSignalLoader, "load_real", guarded)


def make_minute_bars(date: str, pattern: str = "trend_up",
                     start: str = "09:30", end: str = "16:00",
                     base_price: float = 20000.0, step: float = 1.0,
                     volume: int = 100) -> pd.DataFrame:
    """Deterministic 1-min bars, ET session. Patterns:
    trend_up   : close rises `step`/min, low=open-1t, high=close+1t
    trend_down : mirror of trend_up
    chop       : alternates +step/-step, net ~0
    spike_down : trend_up but one deep intraminute low at minute 61 (10:31)
    """
    d = datetime.fromisoformat(date)
    t0 = d.replace(hour=int(start[:2]), minute=int(start[3:]), tzinfo=ET)
    t1 = d.replace(hour=int(end[:2]), minute=int(end[3:]), tzinfo=ET)
    rows = []
    px = base_price
    i = 0
    t = t0
    while t < t1:
        if pattern == "trend_up":
            o, c = px, px + step
        elif pattern == "trend_down":
            o, c = px, px - step
        elif pattern == "chop":
            o, c = px, px + (step if i % 2 == 0 else -step)
        elif pattern == "spike_down":
            o, c = px, px + step
        else:
            raise ValueError(pattern)
        h, l = max(o, c) + 0.25, min(o, c) - 0.25
        if pattern == "spike_down" and i == 61:
            l = min(o, c) - 40 * step        # deep intraminute adverse spike
        rows.append({"ts": t, "open": o, "high": h, "low": l, "close": c,
                     "volume": volume})
        px = c
        i += 1
        t += timedelta(minutes=1)
    return pd.DataFrame(rows)


def make_overnight_bars(date: str, high: float = 20010.0, low: float = 19990.0,
                        base_price: float = 20000.0) -> pd.DataFrame:
    """Minimal overnight window (prev 18:00 -> 09:30) with a given range."""
    prev = datetime.fromisoformat(date) - timedelta(days=1)
    t = prev.replace(hour=18, minute=0, tzinfo=ET)
    rows = [
        {"ts": t, "open": base_price, "high": high, "low": low,
         "close": base_price, "volume": 10},
    ]
    return pd.DataFrame(rows)


def make_trade_path(pnl_per_min: list[float], adverse_extra: float = 0.0,
                    date: str = "2026-08-03", engine: str = "E1",
                    direction: int = 1, final: float | None = None):
    """Quick TradePathRecord for platform/MC tests."""
    from itsf.contracts import TradePathRecord
    close = list(pnl_per_min)
    adverse = [p - abs(adverse_extra) for p in close]
    return TradePathRecord(
        trade_date=date, engine=engine, cost_scenario="Conservative",
        direction=direction, entry_ts=f"{date}T10:00:00-04:00",
        exit_ts=f"{date}T15:44:00-04:00",
        entry_fill=20000.0, exit_fill=20000.0 + (close[-1] if close else 0.0) / 2.0,
        final_pnl_per_contract=final if final is not None else (close[-1] if close else 0.0),
        mtm_close_pnl_1m=close, mtm_adverse_pnl_1m=adverse,
        max_adverse_pnl=min(adverse) if adverse else 0.0,
        max_favourable_pnl=max(close) if close else 0.0,
        time_of_max_adverse="", planned_stop=None, actual_stop_fill=None,
        stop_triggered=False, sizing_anchor_usd=100.0)
