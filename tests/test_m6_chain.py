"""M6 full-chain integration tests (main-agent authored).

Covers: the synthetic end-to-end chain (build_full_study_result ->
validate_report_contract -> render_s0_report), the FAIL-CLOSED pending-
decision posture of the real chain (DR-M6-A/B/C), DR-02 engineering-seed
isolation of every research module, and purity checks mirroring the house
PURE_MODULES discipline for the M6 research modules.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from test_s0_context import linear_closes, universe_of, weekdays
from test_s0_runner import real_run_module

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.s0.dataset import build_s0_dataset

REPO = Path(__file__).resolve().parents[1]

RESEARCH_MODULES = (
    "src/itsf/s0/study.py", "src/itsf/s0/stats.py", "src/itsf/s0/gridmix.py",
    "src/itsf/s0/oracle.py", "src/itsf/s0/paths.py", "src/itsf/s0/costs.py")


# --- synthetic market with BOTH continuation (TP) and failed (FP) days ------

def _fp_closes(base: float) -> list[float]:
    """Morning rises (d_open=+1), afternoon gives it all back (Y_cont < 0)."""
    closes = []
    for i in range(390):
        if i < 30:
            closes.append(base + i * 1.0)
        else:
            closes.append(base + 29.0 - (i - 29) * 0.05)
    return closes


def _market(n_days: int = 46):
    dates = weekdays("2020-01-02", n_days)
    # ADR14 warm-up needs 14 prior complete days; alternate strong
    # continuation days (linear rise -> Y_cont >> 0.5) with failed days
    # (_fp_closes -> Y_cont < 0) afterwards.
    spec = {d: {"closes": _fp_closes(20000.0)}
            for i, d in enumerate(dates) if i >= 14 and i % 2 == 1}
    bars, uni = universe_of(dates, spec)
    ds = build_s0_dataset(bars, uni)
    return bars, ds


_CACHE: dict = {}


_LIVE = object()          # sentinel: use the module's live PENDING default


def _payload(pending=_LIVE, n_boot=40):
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    kw = {} if pending is _LIVE else {"pending_decisions": pending}
    return mod.build_full_study_result(
        ds, bars, spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", n_boot=n_boot, **kw)


# --- e2e + contract ---------------------------------------------------------

def test_e2e_contract_green_when_no_pending_decisions():
    mod = real_run_module()
    payload = _payload(pending=())
    assert mod.validate_report_contract(payload) == []


def test_pending_decisions_refuse_sealing():
    mod = real_run_module()
    payload = _payload()          # default = the live PENDING tuple
    problems = mod.validate_report_contract(payload)
    assert "pending_method_decisions_unresolved" in problems
    with pytest.raises(ValueError, match="contract violations"):
        mod.render_s0_report(payload)


def test_missing_ci_cell_is_flagged():
    mod = real_run_module()
    payload = _payload(pending=())
    key = next(iter(payload["bootstrap_ci"]))
    del payload["bootstrap_ci"][key]
    assert any(p.startswith("missing_ci:") for p in
               mod.validate_report_contract(payload))


def test_records_conservation_is_checked():
    mod = real_run_module()
    payload = _payload(pending=())
    payload["mc_handoff_manifest"]["E1"]["Base"]["n_records"] += 1
    assert any(p.startswith("records_conservation:") for p in
               mod.validate_report_contract(payload))


def test_ci_cells_carry_all_three_frozen_seeds():
    payload = _payload(pending=())
    for cell in payload["bootstrap_ci"].values():
        assert sorted(cell["per_seed"]) == [7, 13, 31]
        assert cell["quoted_seed"] == 7


def test_renderer_seals_full_payload_with_record_files():
    mod = real_run_module()
    files = mod.render_s0_report(_payload(pending=()))
    assert "S0_REPORT.json" in files and "S0_REPORT.md" in files
    jsonl = [n for n in files if n.startswith("MC_HANDOFF_")]
    assert len(jsonl) == 8                      # 2 engines x 4 scenarios
    payload = json.loads(files["S0_REPORT.json"])
    assert "records" not in payload["study"]    # records live in JSONL only
    for meta in payload["mc_handoff_manifest"]["files"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", meta["sha256"])
        body = files[meta["file"]]
        n_lines = len(body.splitlines()) if body else 0
        assert n_lines == meta["n_records"]


def test_grid_present_for_every_theta_engine_scenario():
    payload = _payload(pending=())
    cells = payload["feasibility_grid"]["cells"]
    assert len(cells) == 2 * 2 * 4
    assert payload["feasibility_grid"]["regions"]["status"] == "pending_mc"


# --- real-chain fail-closed posture (DR-M6) ---------------------------------

def test_real_chain_not_ready_while_rulings_pend():
    mod = real_run_module()
    assert mod.PENDING_METHOD_DECISIONS       # M6 state: three open rulings
    ok, why = mod.RealChain().ready()
    assert ok is False
    assert "DR-M6" in why


def test_real_compute_fails_closed_without_loading_data():
    mod = real_run_module()
    chain = mod.RealChain()
    with pytest.raises(RuntimeError, match="pending method rulings"):
        chain.compute()
    assert chain._ds is None                  # raised BEFORE any data load


# --- DR-02: engineering-seed isolation of the research path -----------------

@pytest.mark.parametrize("rel", RESEARCH_MODULES)
def test_research_module_never_references_the_engineering_seed(rel):
    src = (REPO / rel).read_text(encoding="utf-8")
    assert "20260731" not in src
    assert "engineering_seed" not in src
    # RunConfig must never be IMPORTED/used by the research layer (a prose
    # mention in an isolation docstring is allowed).
    for line in src.splitlines():
        if re.match(r"\s*(from|import)\s", line):
            assert "RunConfig" not in line, line


@pytest.mark.parametrize("rel", ("src/itsf/s0/study.py",
                                 "src/itsf/s0/oracle.py",
                                 "src/itsf/s0/paths.py",
                                 "src/itsf/s0/costs.py"))
def test_deterministic_research_modules_have_no_rng(rel):
    src = (REPO / rel).read_text(encoding="utf-8")
    assert "default_rng" not in src
    assert not re.search(r"^import random|^from random", src, re.M)


def test_frozen_research_seeds_pin():
    assert RESEARCH_BOOTSTRAP_SEEDS == (7, 13, 31)
    mod = real_run_module()
    import inspect
    src = inspect.getsource(mod.build_full_study_result)
    assert "bootstrap_mean_ci" in src and "build_grid" in src


def test_frozen_boot_constants_pin():
    mod = real_run_module()
    assert mod.FROZEN_N_BOOT == 10_000        # frozen: S0 §9
    assert mod.FROZEN_BLOCKS == (5, 21)       # frozen: S0 §9
