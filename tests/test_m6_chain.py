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
        worst_day_estimator="TEST_ONLY",
        test_only=True)


def _test_vol_axis(date: str) -> str:
    """TEST_ONLY synthetic tercile assignment: deterministic 3-way split so
    the resolved vol axis carries the full frozen stratum set (three
    terciles + the NA bucket). Carries NO research meaning — the real
    definition is DR-M6-B-v2, unruled."""
    return ("T1", "T2", "T3")[int(date.replace("-", "")) % 3]


def _test_config() -> C.StudyConfig:
    return C.derive_study_config(
        _test_methods(), spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", vol_axis_of=_test_vol_axis)


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
    assert len(C.ResolvedS0Methods().pending_fields()) == 8


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
                                vol_axis_of=_test_vol_axis)
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
    # M6.1.2: formal_sealable is CONSUMED — a not-sealable artifact is
    # WITHHELD from the sealed set and its refusal is disclosed.
    assert "SEED_MANIFEST.json" not in sealed
    assert "HANDOFF_ADMISSION.json" in sealed
    adm = json.loads((out.runs_dir / "HANDOFF_ADMISSION.json")
                     .read_text("utf-8"))
    assert adm["admitted"] == []
    assert "SEED_MANIFEST.json" in adm["withheld"]
    assert adm["withheld"]["SEED_MANIFEST.json"]


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
    """M6.1.3 E7: monkeypatch ONLY the method SOURCE (never the resolver) —
    the real resolver, cache and point-of-use validation all run. Synthetic
    resolved methods must carry test_only=False to pass the production
    seam; the config still never touches real data (ensure is synthetic).
    """
    import dataclasses as _dc
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    synthetic = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: synthetic)
    mod._CONFIG_CACHE.clear()
    try:
        # derivation is unimplemented even when resolved -> resolver reports
        # fail-closed; ready() and compute() must AGREE via the same seam.
        cfg, why = mod.resolved_study_config()
        assert cfg is None and "not implemented" in why
        chain = mod.RealChain()
        ok, why2 = chain.ready()
        assert ok is False and "not implemented" in why2
        import pytest as _pt
        with _pt.raises(RuntimeError, match="not implemented"):
            chain.compute()
        assert chain._ds is None
    finally:
        mod._CONFIG_CACHE.clear()


def test_cache_injection_of_resolved_config_is_refused_vs_fresh_source(
        monkeypatch):
    """M6.1.3 main-1/2: the cache is not a method source — a non-test_only
    'fully resolved' config injected into the cache mismatches the fresh
    all-pending method source and is refused at the point of use."""
    import dataclasses as _dc
    mod = real_run_module()
    cfg = C.derive_study_config(
        _dc.replace(_test_methods(), test_only=False),
        spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", vol_axis_of=_test_vol_axis)
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()
    assert got is None
    assert "fresh approved method source" in why
    assert mod.RealChain().ready()[0] is False


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


# --- M6.1.2: BEHAVIOUR-level ruling->consumer probes (no source greps) ---

def _probe_event_na_mapping():
    """Observable behaviour difference when the ruled value changes: the
    ruled mapping classifies a None F10 flag; any other value refuses.
    Returns (ruled_ok: bool, other_refused: bool)."""
    import dataclasses as _dc
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    rec = next(r for r in ds.records if r.labels.d_open in (1, -1))
    original = rec.features.is_event_day
    setattr(rec.features, "is_event_day", None)
    try:
        ruled_ok = False
        try:
            mod.build_full_study_result(
                ds, bars, config=_test_config(),
                governance_meta=dict(_GOV), n_boot=40)
            ruled_ok = True
        except ValueError:
            ruled_ok = False
        other = _dc.replace(_test_methods(), event_na_mapping="OTHER_VALUE")
        cfg = C.derive_study_config(
            other, spread_scalars=(0.5, 0.75, 0.75),
            regime_of=lambda d: "R", vol_axis_of=_test_vol_axis)
        try:
            mod.build_full_study_result(ds, bars, config=cfg,
                                        governance_meta=dict(_GOV),
                                        n_boot=40)
            other_refused = False
        except ValueError:
            other_refused = True
        return (ruled_ok, other_refused)
    finally:
        setattr(rec.features, "is_event_day", original)


# field -> behaviour probe (None == NO consumer wired yet => PARTIAL).
# A probe must observe a REAL output/behaviour difference, never a source
# substring. Landing a ruling REQUIRES adding its probe here in the same
# commit: the test below fails if a field is resolved in production while
# its probe is still None.
_METHOD_PROBES: dict[str, object] = {
    "spread_cost": None,
    "volatility_regime": None,
    "fp_allocation": None,
    "bootstrap_method": None,
    "grid_policy": None,
    "event_na_mapping": _probe_event_na_mapping,
    "stability_population": None,
    "worst_day_estimator": None,
}


def test_method_probe_map_covers_every_field():
    import dataclasses as _dc
    names = {f.name for f in _dc.fields(C.ResolvedS0Methods)
             if f.name != "test_only"}
    assert set(_METHOD_PROBES) == names


def test_resolved_fields_must_have_a_behaviour_probe():
    """M6.1.2: a field RESOLVED in production with no behaviour probe is a
    red — ruling, consumer and probe must land in ONE commit."""
    mod = real_run_module()
    live = mod._resolved_methods()
    for name, probe in _METHOD_PROBES.items():
        if getattr(live, name) is not None:
            assert probe is not None, (
                f"{name} is RESOLVED but has no behaviour probe")


def test_event_na_mapping_consumer_is_behaviourally_observable():
    ruled_ok, other_refused = _probe_event_na_mapping()
    assert ruled_ok is True
    assert other_refused is True


def test_unconsumed_method_fields_are_declared_partial():
    """The SEVEN fields without consumers are UNRESOLVED in production, so
    no silently-wrong method can run today (the PARTIAL status Codex asked
    to be stated rather than claimed CLOSED). worst_day_estimator counts as
    unconsumed: today it only flips the estimator_status string (fail-closed
    gate) — it does not yet SELECT the estimator."""
    mod = real_run_module()
    live = mod._resolved_methods()
    unconsumed = [n for n, p in _METHOD_PROBES.items() if p is None]
    assert len(unconsumed) == 7
    for name in unconsumed:
        assert getattr(live, name) is None


# --- M6.1.2: an ILLEGAL structured config can never make ready() true -----

def _bad_methods(**over):
    import dataclasses as _dc
    return _dc.replace(_test_methods(), **over)


def test_structurally_invalid_methods_are_refused_everywhere():
    bad = _bad_methods(grid_policy=C.GridRepeatPolicy(
        k_per_seed=0, k_start_index=0, stream_includes_theta=False,
        convergence_rule="X", max_doublings=0))
    assert any("k_per_seed" in p for p in bad.structural_problems())
    with pytest.raises(ValueError, match="structurally invalid"):
        C.derive_study_config(bad, spread_scalars=(0.5, 0.75, 0.75),
                              regime_of=lambda d: "R",
                              vol_axis_of=lambda d: "T")


def test_worst_day_estimator_gets_the_same_structural_gate():
    """M6.1.3 fix-round (blind-audit F4): the 8th field is structurally
    validated like every other string ruling — '' / 42 / {} are refused;
    the VALUE semantics stay pending DR-M6-H."""
    for bad_value in ("", "   ", 42, {}):
        bad = _bad_methods(worst_day_estimator=bad_value)
        assert any("worst_day_estimator" in p
                   for p in bad.structural_problems()), repr(bad_value)
        with pytest.raises(ValueError, match="structurally invalid"):
            C.derive_study_config(bad, spread_scalars=(0.5, 0.75, 0.75),
                                  regime_of=lambda d: "R",
                                  vol_axis_of=lambda d: "T")


def test_duck_typed_methods_object_cannot_reach_ready(monkeypatch):
    """M6.1.3 fix-round (blind-audit E6): a StudyConfig smuggling a foreign
    methods object whose __eq__ always matches (and whose pending/structural
    probes lie) is refused by the TYPE PIN — `!=` dispatches to the left
    operand, so equality is never delegated to attacker code."""
    mod = real_run_module()

    class _Duck:
        test_only = False

        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        def __hash__(self):
            return 0

        def pending_fields(self):
            return ()

        def structural_problems(self):
            return []

    cfg = object.__new__(C.StudyConfig)
    object.__setattr__(cfg, "methods", _Duck())
    object.__setattr__(cfg, "spread_scalars", (0.5, 0.75, 0.75))
    object.__setattr__(cfg, "regime_of", lambda d: "R")
    object.__setattr__(cfg, "vol_axis_of", lambda d: "T")
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()
    assert got is None
    assert "ResolvedS0Methods" in why


def test_matching_methods_cannot_smuggle_foreign_injectables(monkeypatch):
    """M6.1.3 fix-round (blind-audit F3): even with every ruling landed
    (simulated approved source), a cache-injected config whose METHODS
    match cannot supply its own spread_scalars / regime / vol mappings —
    the injectables must come from an approved locked source, which does
    not exist yet (fail closed)."""
    import dataclasses as _dc
    mod = real_run_module()
    approved = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)
    cfg = C.derive_study_config(approved, spread_scalars=(0.0, 0.0, 0.0),
                                regime_of=lambda d: "R",
                                vol_axis_of=lambda d: "T")
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()
    assert got is None
    assert "injectable" in why


def test_methods_with_raising_test_only_property_cannot_break_the_gate(
        monkeypatch):
    """M6.1.3 fix-round-2 (blind-audit N3): the type pin runs before ANY
    read of cfg.methods — a foreign object whose test_only is a raising
    property must be REFUSED with a reason, never allowed to raise out of
    the validation gate."""
    mod = real_run_module()

    class _Bomb:
        @property
        def test_only(self):
            raise RuntimeError("attacker code ran inside the gate")

    cfg = object.__new__(C.StudyConfig)
    object.__setattr__(cfg, "methods", _Bomb())
    object.__setattr__(cfg, "spread_scalars", (0.5, 0.75, 0.75))
    object.__setattr__(cfg, "regime_of", lambda d: "R")
    object.__setattr__(cfg, "vol_axis_of", lambda d: "T")
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()      # must NOT raise
    assert got is None
    assert "ResolvedS0Methods" in why


def test_malformed_injectable_source_fails_closed(monkeypatch):
    """M6.1.3 fix-round-2 (blind-audit N4c): a non-mapping injectable
    source fails CLOSED with a reason — never a TypeError escaping the
    gate (fail-open-by-exception)."""
    import dataclasses as _dc
    mod = real_run_module()
    approved = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)
    monkeypatch.setattr(mod, "_approved_injectables", lambda: "nonsense")
    cfg = C.derive_study_config(approved, spread_scalars=(0.5, 0.75, 0.75),
                                regime_of=lambda d: "R",
                                vol_axis_of=lambda d: "T")
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()      # must NOT raise
    assert got is None
    assert "malformed" in why


def test_injectable_binding_compares_callables_by_identity(monkeypatch):
    """M6.1.3 fix-round-2 (blind-audit N4a/N4b pin): the derivation-
    equality gate is satisfiable ONLY by a config derived from the SAME
    callable objects the approved source hands out — equivalent-but-
    distinct callables are refused (StudyConfig compares functions by
    identity). Weakening this to semantic comparison would reopen F3, so
    this test pins the fail-closed behaviour AND documents that a future
    _approved_injectables must return stable callable objects."""
    import dataclasses as _dc
    mod = real_run_module()
    approved = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)
    inj = {"spread_scalars": (0.5, 0.75, 0.75),
           "regime_of": lambda d: "R", "vol_axis_of": lambda d: "T"}
    monkeypatch.setattr(mod, "_approved_injectables", lambda: dict(inj))
    lookalike = C.derive_study_config(
        approved, spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", vol_axis_of=lambda d: "T")
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (lookalike, "injected"))
    got, why = mod.resolved_study_config()
    assert got is None
    assert "fresh derivation" in why
    genuine = C.derive_study_config(approved, **inj)
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (genuine, "derived"))
    got2, _ = mod.resolved_study_config()
    assert got2 is genuine                      # gate is not dead code


def test_admission_attribution_delimiter_names_are_refused():
    """M6.1.3 fix-round-2 (blind-audit N1b): a candidate name embedding
    the ': ' delimiter would make the prefix attribution non-injective —
    another artifact's refusal reasons could be misattributed into the
    sealed admission record — so such names are refused outright."""
    mod = real_run_module()
    with pytest.raises(ValueError, match="attribution delimiter"):
        mod._partition_admission(
            {"SM.json": {}, "SM.json: shadow": {}}, [])


def test_admission_attribution_partitions_and_fails_closed_on_stray():
    mod = real_run_module()
    admitted, withheld = mod._partition_admission(
        {"A.json": {"x": 1}, "B.json": {"y": 2}},
        ["B.json: broken content"])
    assert admitted == {"A.json": {"x": 1}}
    assert withheld == {"B.json": ["B.json: broken content"]}
    with pytest.raises(ValueError, match="not attributable"):
        mod._partition_admission({"A.json": {}}, ["C.json: orphan problem"])


def test_wrong_type_method_value_is_refused():
    bad = _bad_methods(spread_cost="B-i")          # str, not the dataclass
    assert "spread_cost_not_a_SpreadCostMethod" in bad.structural_problems()
    with pytest.raises(ValueError, match="structurally invalid"):
        C.derive_study_config(bad, spread_scalars=(0.5, 0.75, 0.75),
                              regime_of=lambda d: "R",
                              vol_axis_of=lambda d: "T")


def _non_test_only_config():
    """A synthetic config with test_only=False, used ONLY to exercise the
    structural/pending refusal branches that sit BEHIND the test_only
    refusal in the production predicate. Every test using it asserts the
    config is REFUSED — it never reaches a real computation."""
    import dataclasses as _dc
    return C.derive_study_config(
        _dc.replace(_test_methods(), test_only=False),
        spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", vol_axis_of=_test_vol_axis)


def test_injected_illegal_config_cannot_make_ready_true(monkeypatch):
    """Defence in depth: even if an illegal config reached the cache (frozen
    -dataclass bypass), revalidation at the point of use refuses it."""
    mod = real_run_module()
    cfg = _non_test_only_config()
    object.__setattr__(cfg.methods, "grid_policy", C.GridRepeatPolicy(
        k_per_seed=-5, k_start_index=0, stream_includes_theta=False,
        convergence_rule="X", max_doublings=0))
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()
    # M6.1.3: the fresh-source identity check fires FIRST (a corrupted
    # injected config can never match the live method source) — strictly
    # stronger than reaching the structural branch. The structural branch
    # itself is pinned by test_structurally_invalid_methods_are_refused_
    # everywhere via derive_study_config.
    assert got is None and "fresh approved method source" in why
    ok, why2 = mod.RealChain().ready()
    assert ok is False


def test_injected_partial_config_cannot_make_ready_true(monkeypatch):
    mod = real_run_module()
    cfg = _non_test_only_config()
    object.__setattr__(cfg.methods, "bootstrap_method", None)
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", (cfg, "injected"))
    got, why = mod.resolved_study_config()
    assert got is None and ("fresh approved method source" in why
                            or "pending method rulings" in why)
    assert mod.RealChain().ready()[0] is False


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


def test_e7_ready_then_compute_share_the_same_validated_config(monkeypatch):
    """M6.1.2 E7: call ready() FIRST, then compute(), and prove both read
    the SAME validated config instance (identity, not equality)."""
    mod = real_run_module()
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    cfg = _test_config()
    seen: list = []

    def fake_resolved():
        seen.append(cfg)
        return (cfg, "TEST_ONLY injected")

    monkeypatch.setattr(mod, "resolved_study_config", fake_resolved)
    chain = mod.RealChain()
    monkeypatch.setattr(chain, "_ensure", lambda: (ds, None))
    chain._bars = bars

    ok, why = chain.ready()                      # explicit ready() first
    assert ok is True, why
    payload = chain.compute()                    # then compute()
    assert len(seen) >= 2                        # both consulted the source
    assert all(c is cfg for c in seen)           # identity, one instance
    assert payload["disclosures"]["methods_test_only"] is True


def test_a11_na_conservation_restatement_is_present_and_arithmetic():
    """A11 (contract): the sealed report restates the NA conservation
    evidence — totals, itemized reasons and the checker's verdict — and the
    restated arithmetic must actually add up."""
    d = _payload()["disclosures"]["na_conservation"]
    assert d["conserved"] is True
    assert d["reported_total_na"]
    assert d["unregistered_reasons"] == [] and d["miscounted_columns"] == []
    for col, total in d["reported_total_na"].items():
        assert sum(d["itemized_reason_counts"][col].values()) == total
    assert all(d["per_column_ok"].values())


def test_formal_seal_admission_is_on_the_wire(monkeypatch):
    """M6.1.2: if an artifact WERE sealable, it would be admitted — proving
    the gate decides admission rather than a hardcoded exclusion."""
    from itsf.s0 import handoff as ho
    mod = real_run_module()
    def _test_only_sealable_manifest():
        # M6.1.3: admission RECOMPUTES sealability from content — the
        # fixture must be the REAL full-schema manifest with its open
        # markers overridden by explicit TEST_ONLY values (never a bare
        # fake dict, which the new admission rightly refuses).
        import copy
        m = copy.deepcopy(_REAL_MANIFEST)
        def _resolve(obj):
            if isinstance(obj, dict):
                return {k: _resolve(v) for k, v in obj.items()}
            if isinstance(obj, str) and ("UNRESOLVED" in obj
                                         or "PARTIAL" in obj):
                return "TEST_ONLY"
            return obj
        m = _resolve(m)
        m["formal_sealable"] = True
        return m

    _REAL_MANIFEST = ho.build_seed_manifest()
    monkeypatch.setattr(ho, "build_seed_manifest",
                        _test_only_sealable_manifest)
    # M6.1.3 fix-round (blind-audit D44/F9): admission must be ONE call
    # over the WHOLE candidate set — per-file calls make the cross-artifact
    # checks (grid seeds vs seed manifest) unreachable in production.
    calls: list[list[str]] = []
    _real_admission = ho.formal_seal_admission

    def _spy(artifacts):
        calls.append(sorted(artifacts))
        return _real_admission(artifacts)

    monkeypatch.setattr(ho, "formal_seal_admission", _spy)
    files = mod.render_s0_report(_payload(), expected_governance=dict(_GOV))
    assert "SEED_MANIFEST.json" in files
    adm = json.loads(files["HANDOFF_ADMISSION.json"])
    assert adm["admitted"] == ["SEED_MANIFEST.json"]
    assert adm["withheld"] == {}
    assert calls == [["SEED_MANIFEST.json"]]
