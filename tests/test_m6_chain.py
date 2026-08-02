"""M6/M6.1.1 full-chain integration tests (main-agent authored).

Covers: derived-only StudyConfig (single method-truth-source), the
FAIL-CLOSED pending posture, the synthetic e2e through the REAL S0Runner
A->F with the production builder invoked INSIDE Stage C, DR-02 isolation,
and the explicit event-NA block (no invented vocabulary).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from test_s0_context import linear_closes, universe_of, weekdays
from test_s0_runner import make_deps, ok_gate, real_run_module

from itsf import contracts as C
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.s0.dataset import build_s0_dataset
from itsf.s0.runner import GateCheck, S0Runner

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
    spec = {d: {"closes": _fp_closes(20000.0)}
            for i, d in enumerate(dates) if i >= 14 and i % 2 == 1}
    bars, uni = universe_of(dates, spec)
    ds = build_s0_dataset(bars, uni)
    return bars, ds


def _test_methods() -> C.ResolvedS0Methods:
    """Fully-populated TEST_ONLY methods — every value is a synthetic
    stand-in explicitly marked, never a silently-adopted ruling."""
    return C.ResolvedS0Methods(
        spread_cost=C.SpreadCostMethod(
            scalar_rule="TEST_ONLY", adverse_slippage_ticks={"Base": 1.0},
            adverse_semantics="replaces_per_side"),
        volatility_regime=C.VolatilityRegimeMethod(
            close_source="TEST_ONLY", return_basis="simple", ddof=1,
            roll_crossing_rule="TEST_ONLY", tercile_reference="TEST_ONLY",
            na_rule="vol_na"),
        fp_allocation=C.FpAllocationMethod(
            basis="A", weight_source="self_pool",
            shortfall_rule="proportional"),
        bootstrap_method=C.BootstrapMethod(
            population="TEST_ONLY", na_day_rule="TEST_ONLY",
            statistic="mean", n_boot_per_seed=True,
            quoted_seed_rule="first_seed",
            percentile_interpolation="linear", crn_scope="TEST_ONLY"),
        grid_policy=C.GridRepeatPolicy(
            k_per_seed=1, k_start_index=0, stream_includes_theta=False,
            convergence_rule="TEST_ONLY", max_doublings=0),
        event_na_mapping="five_stratum",
        stability_population="TEST_ONLY",
        test_only=True)


def _test_config() -> C.StudyConfig:
    return C.derive_study_config(
        _test_methods(), spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", vol_axis_of=lambda d: "T2")


_GOV = {"trial_id": "S0-T001", "authorized_commit": "a" * 40,
        "engineering_seed": 20260731,
        "frozen_hashes": {f"f{i}.md": "0" * 64 for i in range(7)},
        "registry_sequence_snapshot": 13}

_CACHE: dict = {}


def _payload(n_boot=10_000):
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    ck = ("p", n_boot)
    if ck not in _CACHE:
        _CACHE[ck] = mod.build_full_study_result(
            ds, bars, config=_test_config(), governance_meta=dict(_GOV),
            n_boot=n_boot)
    return _CACHE[ck]


def _formal(payload):
    from itsf.s0 import report as rep
    _internal, formal = rep.split_envelope(payload)
    return formal


# --- single method-truth-source (M6.1.1 main-agent item 1) ------------------

def test_derive_config_refuses_pending_methods():
    with pytest.raises(ValueError, match="pending method rulings"):
        C.derive_study_config(C.ResolvedS0Methods(),
                              spread_scalars=(1, 1, 1),
                              regime_of=lambda d: "R",
                              vol_axis_of=lambda d: "T")
    assert len(C.ResolvedS0Methods().pending_fields()) == 7


def test_studyconfig_has_no_pending_field():
    assert "pending_decisions" not in {
        f.name for f in C.StudyConfig.__dataclass_fields__.values()}


def test_payload_pending_disclosure_is_derived_and_empty():
    p = _payload()
    d = p["disclosures"]
    assert d["pending_method_decisions"] == []
    assert d["methods_test_only"] is True


def test_production_path_refuses_test_only_config(monkeypatch):
    mod = real_run_module()
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (_test_config(), "ok"))
    cfg, why = mod.resolved_study_config()
    assert cfg is None and "test_only" in why


# --- fail-closed pending posture --------------------------------------------

def test_real_chain_not_ready_while_rulings_pend():
    mod = real_run_module()
    mod._CONFIG_CACHE.clear()
    assert mod.PENDING_METHOD_DECISIONS
    ok, why = mod.RealChain().ready()
    assert ok is False and "pending method rulings" in why
    cfg, why2 = mod.resolved_study_config()
    assert cfg is None and "pending method rulings" in why2


def test_real_compute_fails_closed_without_loading_data():
    mod = real_run_module()
    mod._CONFIG_CACHE.clear()
    chain = mod.RealChain()
    with pytest.raises(RuntimeError, match="pending method rulings"):
        chain.compute()
    assert chain._ds is None


def test_event_na_blocks_without_ruled_mapping():
    """M6.1.1 item 5: a None event flag under an unrecognized mapping rule
    raises explicitly — no invented vocabulary, ever."""
    mod = real_run_module()
    bars, ds = _CACHE.get("m") or _market()
    _CACHE["m"] = (bars, ds)
    import dataclasses as _dc
    m = _dc.replace(_test_methods(), event_na_mapping="UNRULED")
    cfg = C.derive_study_config(m, spread_scalars=(0.5, 0.75, 0.75),
                                regime_of=lambda d: "R",
                                vol_axis_of=lambda d: "T2")
    r0 = ds.records[20]
    object.__setattr__(r0.features, "is_event_day", None) \
        if getattr(type(r0.features), "__dataclass_params__").frozen \
        else setattr(r0.features, "is_event_day", None)
    try:
        with pytest.raises(ValueError, match="DR-M6-F"):
            mod.build_full_study_result(ds, bars, config=cfg,
                                        governance_meta=dict(_GOV),
                                        n_boot=40)
    finally:
        setattr(r0.features, "is_event_day", "none")


# --- E7: REAL S0Runner A->F with production builder inside Stage C ----------

def test_e7_runner_a_to_f_production_builder_inside_stage_c(tmp_path):
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    calls = {"n": 0}

    def compute():                        # runs INSIDE Stage C, not before
        calls["n"] += 1
        return mod.build_full_study_result(
            ds, bars, config=_test_config(), governance_meta=dict(_GOV),
            n_boot=10_000)

    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()], compute=compute,
        renderer=lambda r: mod.render_s0_report(
            r, expected_governance=dict(_GOV)),
        integrity=mod.build_integrity_checks())
    assert calls["n"] == 0                # nothing precomputed
    out = S0Runner(deps).run()
    assert calls["n"] == 1
    assert out.ok is True, (out.failure_kind, out.failed_gate)
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    sealed = sorted(x.name for x in out.runs_dir.iterdir())
    assert "S0_REPORT.json" in sealed
    assert sum(1 for n in sealed if n.startswith("MC_HANDOFF_")) == 8


def test_e7_unresolved_config_refused_in_stage_b_zero_exposure(tmp_path):
    mod = real_run_module()
    mod._CONFIG_CACHE.clear()
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        b_checks=[GateCheck("stage_c_wiring_activated",
                            mod.RealChain().ready)],
        compute=lambda: (_ for _ in ()).throw(AssertionError("unreachable")),
        renderer=mod.render_s0_report)
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]
    assert not Path(deps.config.runs_dir).exists()


def test_ready_true_implies_compute_has_no_wiring_error(monkeypatch):
    """M6.1.1 E7 invariant: with the SAME cached config instance, ready=True
    means compute cannot raise a wiring/config error (synthetic ensure)."""
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    cfg = _test_config()
    monkeypatch.setattr(mod, "resolved_study_config",
                        lambda: (cfg, "TEST_ONLY injected"))
    chain = mod.RealChain()
    monkeypatch.setattr(chain, "_ensure", lambda: (ds, None))
    chain._bars = bars
    payload = chain.compute()             # must not raise wiring/config
    assert payload["disclosures"]["methods_test_only"] is True


# --- DR-02: engineering-seed isolation --------------------------------------

@pytest.mark.parametrize("rel", RESEARCH_MODULES)
def test_research_module_never_references_the_engineering_seed(rel):
    src = (REPO / rel).read_text(encoding="utf-8")
    assert "20260731" not in src
    assert "engineering_seed" not in src
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


def test_frozen_boot_constants_pin():
    mod = real_run_module()
    assert mod.FROZEN_N_BOOT == 10_000        # frozen: S0 §9
    assert mod.FROZEN_BLOCKS == (5, 21)       # frozen: S0 §9


def test_no_invented_event_vocabulary_in_entrypoint():
    src = (REPO / "scripts" / "s0_real_run.py").read_text(encoding="utf-8")
    assert "none_or_na" not in src


# --- MED-1 (M6.1.1 audit): mechanical ruling->consumer link -----------------

# Field -> source patterns that must exist in the PRODUCTION sources the
# moment the field is resolved. Empty list == no consumer wired YET; the
# assertion below forces this map (and a real consumer) to be updated in
# the SAME commit that lands a ruling — a resolved field with no wired
# consumer turns the suite red.
_METHOD_CONSUMERS: dict[str, list[str]] = {
    "spread_cost": [],
    "volatility_regime": [],
    "fp_allocation": [],
    "bootstrap_method": [],
    "grid_policy": [],
    "event_na_mapping": ["config.methods.event_na_mapping"],
    "stability_population": [],
}


def test_every_resolved_method_field_has_a_wired_consumer():
    mod = real_run_module()
    import dataclasses as _dc
    field_names = {f.name for f in _dc.fields(C.ResolvedS0Methods)
                   if f.name != "test_only"}
    assert set(_METHOD_CONSUMERS) == field_names
    entry_src = (REPO / "scripts" / "s0_real_run.py").read_text(
        encoding="utf-8")
    live = mod._resolved_methods()
    for name, patterns in _METHOD_CONSUMERS.items():
        resolved = getattr(live, name) is not None
        if resolved:
            assert patterns, (
                f"{name} is RESOLVED but no consumer is wired/mapped — "
                "ruling, consumer and this map must land in ONE commit")
        for pat in patterns:
            assert pat in entry_src, (name, pat)


# --- LOW-2 (M6.1.1 audit): _expected_governance independence ----------------

def test_expected_governance_rederives_from_primary_sources():
    import inspect
    mod = real_run_module()
    from itsf import guards
    gov = mod._expected_governance()
    assert sorted(gov) == ["authorized_commit", "engineering_seed",
                           "frozen_hashes", "registry_sequence_snapshot",
                           "trial_id"]
    assert gov["frozen_hashes"] == dict(guards.FROZEN_HASHES)
    assert gov["engineering_seed"] == mod.ENGINEERING_SEED
    text = mod.REGISTRY.read_text(encoding="utf-8")
    assert gov["registry_sequence_snapshot"] == len(
        mod.parse_registry_events(text))
    _row, commit, _ = mod.find_authorization_event(text)
    assert gov["authorized_commit"] == commit
    # independence: takes NO payload argument
    assert len(inspect.signature(mod._expected_governance).parameters) == 0


def test_empty_day_strata_is_not_sealable():
    from itsf.s0 import handoff as ho
    out = ho.build_day_strata({}, thetas=(0.5, 0.3))
    assert out["formal_sealable"] is False
