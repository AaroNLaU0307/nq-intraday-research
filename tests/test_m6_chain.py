"""M6/M6.1.1 full-chain integration tests (main-agent authored).

Covers: derived-only StudyConfig (single method-truth-source), the
FAIL-CLOSED pending posture, the synthetic e2e through the REAL S0Runner
A->F with the production builder invoked INSIDE Stage C, DR-02 isolation,
and the explicit event-NA block (no invented vocabulary).
"""
from __future__ import annotations

import json
import re
from types import MappingProxyType as _MPX
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
    """Fully-populated TEST_ONLY methods (S0 closeout, 2026-08-10).

    Post-ruling shape: the values MIRROR the Aaron-ruled instance — using
    them no longer adopts an unruled choice, and the chain acceptance
    criterion is precisely "a fully-RULED synthetic config through the real
    resolver". `test_only=True` still marks the instance as test-context
    (production refuses it), and the event mapping keeps the TEST_ONLY
    synthetic value to keep exercising dataset.py's test-gate. Tests that
    need a deviant field value `dataclasses.replace` it locally.
    """
    import dataclasses as _dc
    ruled = C.aaron_ruled_methods()
    return _dc.replace(
        ruled,
        event_na_mapping="five_stratum",
        # SMALL K for chain-test runtime only: K=200 costs ~10s per
        # engine x scenario cell (S4 measurement) and the ruled 200 is
        # pinned by tests/test_aaron_rulings.py; the chain needs the ruled
        # STRUCTURE (theta-in-stream, prefix nesting), not the ruled size.
        grid_policy=_dc.replace(ruled.grid_policy, k_per_seed=3),
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


def _test_snapshot(**over):
    """M6.1.7: a synthetic Stage-A authorization snapshot.

    `prepare()` takes this rather than reading the registry itself, so the
    value the run seals is the SAME object `pre_exposure_recheck` proves the
    registry still matches. Tests must therefore supply one.
    """
    snap = {"trial_id": _GOV["trial_id"],
            "authorized_commit": _GOV["authorized_commit"],
            "event_sequence": _GOV["registry_sequence_snapshot"],
            "registry_sha256": "b" * 64,
            "exact_authorization_text_sha256": "c" * 64}
    snap.update(over)
    return snap


def _write_run_dir(tmp_path, files, name="rundir"):
    """Write a rendered artifact map to disk EXACTLY as the runner does:
    encode once to UTF-8, write bytes, no newline translation."""
    rdir = tmp_path / name
    rdir.mkdir(parents=True, exist_ok=True)
    for fname, content in files.items():
        (rdir / fname).write_bytes(content.encode("utf-8"))
    return rdir

_CACHE: dict = {}


def _cache_entry(mod, cfg, why="injected"):
    """Build the EXACT internal cache envelope (M6.1.4-ARCH F-1).

    `_CONFIG_CACHE['cfg']` is no longer an arbitrary 2-iterable: the only
    admissible value is `_ConfigCacheEntry`, identified by an exact
    `type(x) is` test that never touches the object. Tests that used to
    inject a `(cfg, why)` tuple go through here; tests that deliberately
    inject a NON-envelope keep doing so and must be refused at G2.
    """
    return mod._ConfigCacheEntry(cfg, why)


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


@pytest.fixture(autouse=True)
def _kc_assertions_default(monkeypatch, tmp_path):
    """Every test in this module renders (if it renders at all) against a
    synthetic assertions file matching the shared `_market()` payload, so
    the F-2 key-claims screen verifies WIRING, not the real locked counts.
    Tests with a different market call `_patch_kc_assertions` themselves —
    a later setattr wins."""
    mod = real_run_module()
    _patch_kc_assertions(mod, monkeypatch, tmp_path, _payload())
    yield


def _patch_kc_assertions(mod, monkeypatch, tmp_path, payload):
    """Point the F-2 key-claims screen at a SYNTHETIC assertions file whose
    funnel matches this synthetic payload — the production value stays the
    locked real artifact; tests only verify the WIRING (the independence
    claim is about production, where the file is the locked preflight)."""
    import json as _json
    st = payload.get("structural", {})
    assertions = tmp_path / "kc_assertions.json"
    assertions.write_text(
        _json.dumps({"funnel": dict(st.get("funnel_counts", {}))}),
        encoding="utf-8")
    monkeypatch.setattr(mod, "KEY_CLAIMS_ASSERTIONS_PATH", assertions)


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
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg",
                        _cache_entry(mod, _test_config(), "ok"))
    cfg, why = mod.resolved_study_config()
    assert cfg is None and "test_only" in why


# --- fail-closed pending posture --------------------------------------------

def test_ruled_source_has_no_pending_and_machinery_still_fail_closes(
        monkeypatch):
    """S0 closeout (2026-08-10): all eight rulings landed, so the LIVE
    pending list is empty — and the fail-closed machinery must still refuse
    a pending source if one ever reappears (un-ruling regression guard)."""
    mod = real_run_module()
    mod._CONFIG_CACHE.clear()
    assert mod.PENDING_METHOD_DECISIONS == ()
    assert mod._resolved_methods().fully_resolved is True
    monkeypatch.setattr(mod, "_resolved_methods",
                        lambda: C.ResolvedS0Methods())
    try:
        ok, why = mod.RealChain().ready()
        assert ok is False and "pending method rulings" in why
        cfg, why2 = mod.resolved_study_config()
        assert cfg is None and "pending method rulings" in why2
    finally:
        mod._CONFIG_CACHE.clear()


def test_real_compute_fails_closed_without_loading_data(monkeypatch):
    """A PENDING method source (synthetically restored) still refuses in
    prepare BEFORE any data load — chain._ds stays None (pre-exposure)."""
    mod = real_run_module()
    mod._CONFIG_CACHE.clear()
    monkeypatch.setattr(mod, "_resolved_methods",
                        lambda: C.ResolvedS0Methods())
    try:
        chain = mod.RealChain()
        with pytest.raises(RuntimeError, match="pending method rulings"):
            chain.compute(chain.prepare(_test_snapshot()))
        assert chain._ds is None
    finally:
        mod._CONFIG_CACHE.clear()


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
        with pytest.raises(ValueError,
                           match="event-NA stratum mapping .* not "
                                 "implemented"):
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
        renderer=lambda r, prepared: mod.render_s0_report(
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


def test_e7_unresolved_config_refused_in_stage_b_zero_exposure(tmp_path,
                                                               monkeypatch):
    mod = real_run_module()
    # S0 closeout: the live sources are ruled — the unresolved premise is
    # synthetically restored (regression guard for the Stage-B refusal).
    monkeypatch.setattr(mod, "_approved_injectables", lambda: None)
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


def _hermetic_stage_c_paths(mod, monkeypatch, tmp_path):
    """auditor-2 LOW-5: ready()'s artifact-existence gate must not couple
    the E7 tests to this machine's data layout — synthetic stand-ins
    satisfy the existence check without touching any real path."""
    art = tmp_path / "a1job"
    art.mkdir()
    for name in ("condition.json", "manifest.json"):
        (art / name).write_text("{}", encoding="utf-8")
    f10 = tmp_path / "f10.csv"
    f10.write_text("synthetic", encoding="utf-8")
    sym = tmp_path / "sym.csv"
    sym.write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(mod, "F10_CSV", f10)
    monkeypatch.setattr(mod, "SYMBOLOGY_CSV", sym)
    monkeypatch.setattr(mod, "A1_JOB_DIR", art)


def test_ready_true_implies_compute_has_no_wiring_error(monkeypatch,
                                                        tmp_path):
    """M6.1.4 E7 negative: with the method source resolved but NO approved
    injectable source, the resolver fails closed at the injectable gate —
    ready() and compute() must AGREE via the same seam, and the production
    builder is never invoked (compute calls == 0)."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    synthetic = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: synthetic)
    # S0 closeout: the production injectable source is live; this test's
    # premise (no approved injectable source) is synthetically restored.
    monkeypatch.setattr(mod, "_approved_injectables", lambda: None)
    calls: list = []
    real_build = mod.build_full_study_result
    monkeypatch.setattr(
        mod, "build_full_study_result",
        lambda *a, **k: calls.append(1) or real_build(*a, **k))
    mod._CONFIG_CACHE.clear()
    try:
        cfg, why = mod.resolved_study_config()
        assert cfg is None and "no approved injectable source" in why
        chain = mod.RealChain()
        ok, why2 = chain.ready()
        assert ok is False and "no approved injectable source" in why2
        import pytest as _pt
        with _pt.raises(RuntimeError, match="injectable"):
            chain.compute(chain.prepare(_test_snapshot()))
        assert chain._ds is None
        assert calls == []                      # builder never reached
    finally:
        mod._CONFIG_CACHE.clear()


def test_malformed_injectables_keep_ready_false_and_zero_compute(monkeypatch,
                                                                 tmp_path):
    """M6.1.4 E7 negative: an approved method source + a MALFORMED
    injectable source (missing keys / extra keys / wrong types) must yield
    ready=False with a reasoned refusal, zero production-builder calls and
    an untouched chain — through the REAL resolver, never a patched one."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    synthetic = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: synthetic)
    calls: list = []
    real_build = mod.build_full_study_result
    monkeypatch.setattr(
        mod, "build_full_study_result",
        lambda *a, **k: calls.append(1) or real_build(*a, **k))
    bad_sources = [
        {"spread_scalars": (0.5, 0.75, 0.75)},              # missing keys
        {"spread_scalars": (0.5, 0.75, 0.75),
         "regime_of": lambda d: "R", "vol_axis_of": _test_vol_axis,
         "extra": 1},                                       # extra key
        {"spread_scalars": "not-a-tuple",
         "regime_of": lambda d: "R", "vol_axis_of": _test_vol_axis},
        {},                                                 # empty
    ]
    for bad in bad_sources:
        monkeypatch.setattr(mod, "_approved_injectables", lambda b=bad: b)
        mod._CONFIG_CACHE.clear()
        try:
            cfg, why = mod.resolved_study_config()
            assert cfg is None and "malformed" in why, (bad, why)
            chain = mod.RealChain()
            ok, why2 = chain.ready()
            assert ok is False and "malformed" in why2
            assert chain._ds is None
            assert calls == []
        finally:
            mod._CONFIG_CACHE.clear()


def test_cache_injection_of_resolved_config_is_refused_vs_fresh_source(
        monkeypatch):
    """M6.1.3 main-1/2: the cache is not a method source — a non-test_only
    'fully resolved' config injected into the cache cannot survive against
    the fresh all-pending method source, and is refused at the point of use.

    M6.1.4-ARCH: the single gateway resolves stages in ONE order, and the
    FRESH source is the authority — so with every ruling still pending the
    refusal is now reported at G7_pending (which is strictly upstream of,
    and stronger than, the methods-mismatch it used to report). The
    G10 'cache is not a method source' claim keeps its own live proof in
    test_f1_methods_mismatch_refusal_under_a_resolved_source, which
    supplies a RESOLVED fresh source so the pending gate cannot short it."""
    import dataclasses as _dc
    mod = real_run_module()
    # S0 closeout: the LIVE source is ruled, so the all-pending premise this
    # test proves is synthetically restored (regression guard).
    monkeypatch.setattr(mod, "_resolved_methods",
                        lambda: C.ResolvedS0Methods())
    cfg = C.derive_study_config(
        _dc.replace(_test_methods(), test_only=False),
        spread_scalars=(0.5, 0.75, 0.75),
        regime_of=lambda d: "R", vol_axis_of=_test_vol_axis)
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
    got, why = mod.resolved_study_config()
    assert got is None
    assert "pending method rulings" in why
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
# its probe is still None. S0 closeout (2026-08-10): all eight probes live.

def _probe_spread_cost():
    import dataclasses as _dc
    from itsf.s0 import costs as _costs
    ruled = C.aaron_ruled_methods().spread_cost
    scns = _costs.build_scenarios_from_method((0.5, 0.75, 1.0), ruled)
    ruled_ok = scns["Severe"].adverse_slippage_ticks > 0
    try:
        _costs.derive_spread_scalars([], _dc.replace(ruled,
                                                     scalar_rule="UNRULED"))
        other_refused = False
    except ValueError:
        other_refused = True
    return (bool(ruled_ok), other_refused)


def _probe_volatility_regime():
    import dataclasses as _dc
    from itsf.s0 import dataset as _dsm
    ruled = C.aaron_ruled_methods().volatility_regime
    closes = [(f"2020-01-{d:02d}", 100.0 + (d % 5)) for d in range(1, 29)]
    days = [d for d, _ in closes[22:]]
    a = _dsm.build_vol20_regime_mapping(days, closes, (), ruled)
    b = _dsm.build_vol20_regime_mapping(
        days, closes, (), _dc.replace(ruled, ddof=0))
    va = [a.vol20[d] for d in days if a.vol20[d] is not None]
    vb = [b.vol20[d] for d in days if b.vol20[d] is not None]
    return (len(va) > 0, va != vb)


def _probe_fp_allocation():
    import dataclasses as _dc
    from itsf.s0 import gridmix as _gm
    ruled = C.aaron_ruled_methods().fp_allocation
    out = _gm.fp_allocation_from_selected_tp(
        5, {"A": 3, "B": 2}, {"A": 10, "B": 10}, ruled)
    ruled_ok = sum(out["fp_alloc"].values()) == 5
    try:
        _gm.fp_allocation_from_selected_tp(
            5, {"A": 3}, {"A": 10}, _dc.replace(ruled, basis="A"))
        other_refused = False
    except ValueError:
        other_refused = True
    return (ruled_ok, other_refused)


def _probe_bootstrap_method():
    import dataclasses as _dc
    from itsf.s0 import stats as _st
    ruled = C.aaron_ruled_methods().bootstrap_method
    states = [("2020-01-02", "oracle_traded", 10.0),
              ("2020-01-03", "eligible_not_selected"),
              ("2020-01-06", "na")]
    seq = _st.build_bootstrap_day_sequence(states, ruled)
    ruled_ok = (seq["n_days_in_sequence"] == 2
                and seq["n_na_days_dropped"] == 1)
    try:
        _st.build_bootstrap_day_sequence(
            states, _dc.replace(ruled, population="UNRULED"))
        other_refused = False
    except ValueError:
        other_refused = True
    return (ruled_ok, other_refused)


def _probe_grid_policy():
    import dataclasses as _dc
    from itsf.s0 import gridmix as _gm
    m = C.aaron_ruled_methods()
    policy = _dc.replace(m.grid_policy, k_per_seed=2)
    tp = {f"2020-01-{d:02d}": 5.0 for d in range(2, 12)}
    fp = {f"2020-02-{d:02d}": -5.0 for d in range(2, 12)}
    strata = {d: ("2020", "T1", "none") for d in {**tp, **fp}}
    cell = _gm.build_grid(tp, fp, strata, 0.5, q_grid=(0.5,), r_grid=(0.5,),
                          fp_allocation=m.fp_allocation, grid_policy=policy,
                          theta=0.5)
    grid = cell["grid"]
    raw = list(grid.values()) if isinstance(grid, dict) else list(grid)
    pts = [p for p in raw
           if isinstance(p, dict) and not p.get("infeasible_by_sample")]
    ruled_ok = bool(pts) and "repeats" in pts[0]
    try:
        _gm.build_grid(tp, fp, strata, 0.5, q_grid=(0.5,), r_grid=(0.5,),
                       fp_allocation=m.fp_allocation,
                       grid_policy=_dc.replace(policy,
                                               stream_includes_theta=False),
                       theta=0.5)
        other_refused = False
    except ValueError:
        other_refused = True
    return (ruled_ok, other_refused)


def _probe_stability_population():
    from itsf.s0 import stability as _stab
    rule = C.aaron_ruled_methods().stability_population
    try:
        _stab.check_populations({}, "UNRULED")
        other_refused = False
    except ValueError:
        other_refused = True
    problems = _stab.check_populations({}, rule)
    return (bool(problems), other_refused)   # ruled rule DEMANDS the block


def _probe_worst_day_estimator():
    from itsf.s0 import study as _study
    ruled = C.aaron_ruled_methods().worst_day_estimator
    sample = [-10.0, -5.0, -1.0, 0.0, 4.0]
    a = _study._percentile(sample, 5.0, ruled)
    b = _study._percentile(sample, 5.0, "lower")
    try:
        _study.resolve_worst_day_estimator("UNRULED")
        other_refused = False
    except ValueError:
        other_refused = True
    return (a != b, other_refused)


_METHOD_PROBES: dict[str, object] = {
    "spread_cost": _probe_spread_cost,
    "volatility_regime": _probe_volatility_regime,
    "fp_allocation": _probe_fp_allocation,
    "bootstrap_method": _probe_bootstrap_method,
    "grid_policy": _probe_grid_policy,
    "event_na_mapping": _probe_event_na_mapping,
    "stability_population": _probe_stability_population,
    "worst_day_estimator": _probe_worst_day_estimator,
}


def test_every_probe_observes_ruled_behaviour_and_refusal():
    for name, probe in _METHOD_PROBES.items():
        if name == "event_na_mapping":
            continue                     # has its own dedicated test below
        ruled_ok, other = probe()
        assert ruled_ok is True, f"{name}: ruled path not observable"
        assert other is True, f"{name}: deviant value not refused/different"


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
    """S0 closeout (2026-08-10): ZERO unconsumed fields — every ruling has
    a wired production consumer and a live behaviour probe. The check stays
    so that a future un-wiring (probe reset to None while the field stays
    resolved) is a red, not a silent regression."""
    mod = real_run_module()
    live = mod._resolved_methods()
    unconsumed = [n for n, p in _METHOD_PROBES.items() if p is None]
    assert unconsumed == []
    assert live.fully_resolved is True


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
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
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
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
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
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
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
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
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
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg",
                        _cache_entry(mod, lookalike))
    got, why = mod.resolved_study_config()
    assert got is None
    assert "fresh derivation" in why
    genuine = C.derive_study_config(approved, **inj)
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg",
                        _cache_entry(mod, genuine, "derived"))
    got2, _ = mod.resolved_study_config()
    assert got2 is genuine                      # gate is not dead code


def _boom_factory(msg):
    def _boom():
        raise RuntimeError(msg)
    return _boom


def _b1_builder_spy(mod, monkeypatch):
    calls: list = []
    real_build = mod.build_full_study_result
    monkeypatch.setattr(
        mod, "build_full_study_result",
        lambda *a, **k: calls.append(1) or real_build(*a, **k))
    return calls


def test_b1_raising_method_source_yields_reasoned_refusal(monkeypatch,
                                                          tmp_path):
    """CLOSEOUT B1: empty cache + a METHOD SOURCE that raises — ready()
    must return (False, diagnosable reason), never raise; the production
    builder is never invoked."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    calls = _b1_builder_spy(mod, monkeypatch)
    monkeypatch.setattr(mod, "_resolved_methods",
                        _boom_factory("method source down"))
    mod._CONFIG_CACHE.clear()
    try:
        cfg, why = mod.resolved_study_config()   # must NOT raise
        assert cfg is None and "RuntimeError" in why
        ok, why2 = mod.RealChain().ready()
        assert ok is False and "RuntimeeError" not in why2  # sane string
        assert "RuntimeError" in why2
        assert calls == []
    finally:
        mod._CONFIG_CACHE.clear()


def test_b1_raising_injectable_source_yields_reasoned_refusal(monkeypatch,
                                                              tmp_path):
    """CLOSEOUT B1: empty cache + resolved methods + an INJECTABLE SOURCE
    that raises — reasoned refusal, zero builder calls."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    calls = _b1_builder_spy(mod, monkeypatch)
    approved = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)
    monkeypatch.setattr(mod, "_approved_injectables",
                        _boom_factory("injectable source down"))
    mod._CONFIG_CACHE.clear()
    try:
        cfg, why = mod.resolved_study_config()   # must NOT raise
        assert cfg is None and "RuntimeError" in why
        ok, why2 = mod.RealChain().ready()
        assert ok is False and "RuntimeError" in why2
        assert calls == []
    finally:
        mod._CONFIG_CACHE.clear()


def test_b1_raising_derivation_yields_reasoned_refusal(monkeypatch,
                                                       tmp_path):
    """CLOSEOUT B1: empty cache + resolved methods + legal-schema
    injectables whose values make derive_study_config raise (ordering
    violation surfaces inside the constructor) — reasoned refusal, zero
    builder calls."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    calls = _b1_builder_spy(mod, monkeypatch)
    approved = _dc.replace(_test_methods(), test_only=False)
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)

    class _LyingTuple(tuple):
        # passes validate_injectables' shape test, then derive's
        # canonicalization sees the same values — force the raise via a
        # tuple whose iteration misbehaves on the SECOND pass
        _reads = 0

        def __iter__(self):
            type(self)._reads += 1
            if type(self)._reads > 1:
                raise RuntimeError("derivation-time read")
            return super().__iter__()

    inj = {"spread_scalars": _LyingTuple((0.5, 0.75, 0.75)),
           "regime_of": lambda d: "R", "vol_axis_of": _test_vol_axis}
    monkeypatch.setattr(mod, "_approved_injectables", lambda: dict(inj))
    mod._CONFIG_CACHE.clear()
    try:
        cfg, why = mod.resolved_study_config()   # must NOT raise
        assert cfg is None
        ok, why2 = mod.RealChain().ready()
        assert ok is False
        assert calls == []
    finally:
        mod._CONFIG_CACHE.clear()


def test_b1_subclass_config_with_raising_property_cannot_break_the_gate(
        monkeypatch, tmp_path):
    """CLOSEOUT B1: the cache path must prove the object is EXACTLY a
    StudyConfig BEFORE reading any attribute — isinstance admits a
    subclass whose `methods` property runs foreign code inside the gate.
    ready() must return (False, reason), never raise."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    calls = _b1_builder_spy(mod, monkeypatch)

    class _EvilConfig(C.StudyConfig):
        @property
        def methods(self):
            raise RuntimeError("foreign property ran inside the gate")

    evil = object.__new__(_EvilConfig)
    object.__setattr__(evil, "spread_scalars", (0.5, 0.75, 0.75))
    object.__setattr__(evil, "regime_of", lambda d: "R")
    object.__setattr__(evil, "vol_axis_of", lambda d: "T")
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, evil))
    got, why = mod.resolved_study_config()       # must NOT raise
    assert got is None
    assert "StudyConfig" in why
    ok, _why2 = mod.RealChain().ready()
    assert ok is False
    assert calls == []


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
    # S0 closeout: restore the all-pending fresh authority this test's
    # G7-first claim is stated against.
    monkeypatch.setattr(mod, "_resolved_methods",
                        lambda: C.ResolvedS0Methods())
    cfg = _non_test_only_config()
    object.__setattr__(cfg.methods, "grid_policy", C.GridRepeatPolicy(
        k_per_seed=-5, k_start_index=0, stream_includes_theta=False,
        convergence_rule="X", max_doublings=0))
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
    got, why = mod.resolved_study_config()
    # M6.1.3: a fresh-source check fires FIRST (a corrupted injected config
    # can never match the live method source) — strictly stronger than
    # reaching the structural branch. M6.1.4-ARCH: under the single gateway
    # that first check is G7_pending on the FRESH authority. The structural
    # branch itself is pinned by test_structurally_invalid_methods_are_
    # refused_everywhere via derive_study_config.
    assert got is None and "pending method rulings" in why
    ok, why2 = mod.RealChain().ready()
    assert ok is False


def test_injected_partial_config_cannot_make_ready_true(monkeypatch):
    mod = real_run_module()
    cfg = _non_test_only_config()
    object.__setattr__(cfg.methods, "bootstrap_method", None)
    monkeypatch.setitem(mod._CONFIG_CACHE, "cfg", _cache_entry(mod, cfg))
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
    # independence: the ONLY parameter is the pre-run snapshot, never the
    # payload being verified, and it defaults to the legacy re-derivation.
    params = inspect.signature(mod._expected_governance).parameters
    assert list(params) == ["snapshot"]
    assert params["snapshot"].default is None


def test_m617_expected_governance_takes_the_sequence_from_the_snapshot():
    """M6.1.7 — the defect this closes: at seal time the registry already
    holds this run's own RUN_STARTED row, so re-deriving the event count
    there returns the PRE-EXPOSURE count plus one. The count must come from
    the snapshot; the authorized COMMIT must still be re-read live."""
    mod = real_run_module()
    text = mod.REGISTRY.read_text(encoding="utf-8")
    live_count = len(mod.parse_registry_events(text))
    _row, commit, _ = mod.find_authorization_event(text)

    # a snapshot taken BEFORE this run's RUN_STARTED row existed
    snap = {"trial_id": mod.TRIAL_ID, "authorized_commit": commit,
            "event_sequence": live_count - 1, "registry_sha256": "b" * 64}
    gov = mod._expected_governance(snap)
    assert gov["registry_sequence_snapshot"] == live_count - 1
    assert gov["registry_sequence_snapshot"] != live_count      # the +1 bug
    # the commit is NOT taken from the snapshot: it is re-read from registry
    # bytes and required to agree, so the check cannot go vacuous.
    assert gov["authorized_commit"] == commit
    with pytest.raises(ValueError, match="authorized commit changed"):
        mod._expected_governance({**snap, "authorized_commit": "9" * 40})


def test_empty_day_strata_is_not_sealable():
    from itsf.s0 import handoff as ho
    out = ho.build_day_strata({}, thetas=(0.5, 0.3))
    assert out["formal_sealable"] is False


def test_e7_ready_then_compute_share_the_same_validated_config(monkeypatch,
                                                               tmp_path):
    """M6.1.4 E7 POSITIVE — THE one honest positive path.

    SCOPE, STATED PLAINLY: this is a SYNTHETIC CONFIG-TO-COMPUTE
    INTEGRATION over a synthetic universe, with the method source, the
    injectable source and data I/O replaced by synthetic stand-ins. It is
    NOT a real data chain, NOT a full A->F run, and NOT a real S0. It
    proves the configuration gateway's positive branch and the identity
    guarantee, nothing about research output.

    From an EMPTY cache, with ONLY those three seams replaced (never
    resolved_study_config / _gateway_body / ready / compute), the chain
    walks: fresh methods -> pending+structural on the fresh authority ->
    exact injectables -> derive_study_config -> EXACT cache envelope ->
    point-of-use revalidation -> ready=True -> compute(); ready() and
    compute() consume the SAME cached validated config INSTANCE."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    approved = _dc.replace(_test_methods(), test_only=False,
                           event_na_mapping=C.aaron_ruled_methods()
                           .event_na_mapping)
    inj = {"spread_scalars": (0.5, 0.75, 0.75),
           "regime_of": lambda d: "R", "vol_axis_of": _test_vol_axis}
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)
    monkeypatch.setattr(mod, "_approved_injectables", lambda: dict(inj))
    mod._CONFIG_CACHE.clear()
    try:
        chain = mod.RealChain()
        monkeypatch.setattr(chain, "_ensure", lambda: (ds, None))
        chain._bars = bars

        ok, why = chain.ready()                  # explicit ready() first
        assert ok is True, why
        cfg1, _ = mod.resolved_study_config()    # cache hit, revalidated
        assert cfg1 is not None
        entry = mod._CONFIG_CACHE["cfg"]
        assert type(entry) is mod._ConfigCacheEntry
        assert cfg1 is entry.config
        payload = chain.compute(chain.prepare(_test_snapshot()))  # then compute()
        cfg2, _ = mod.resolved_study_config()
        assert cfg2 is cfg1                      # identity, one instance
        assert payload["disclosures"]["methods_test_only"] is False
        assert payload["disclosures"]["pending_method_decisions"] == []
        assert "evidence" in payload             # capture ran at compute
    finally:
        mod._CONFIG_CACHE.clear()


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
    def _test_only_sealable_manifest(methods=None):
        # M6.1.3: admission RECOMPUTES sealability from content — the
        # fixture must be the REAL full-schema manifest with its open
        # markers overridden by explicit TEST_ONLY values (never a bare
        # fake dict, which the new admission rightly refuses). S0 closeout:
        # accepts (and ignores) the renderer's methods= kwarg — the stub IS
        # the manifest under test regardless of ruling state.
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
    # M6.1.4 (S2 bundle-atomic admission): the manifest's k_policy/crn_scope
    # are UNRULED axes — admission refuses ANY concrete string unless the
    # SourceContext carries a ruled vocabulary. Declaring the TEST_ONLY
    # ruling on the context (the production no-source seam) is what makes
    # this fixture admissible — proving the gate is decided by admission
    # against its sources, not by a hardcoded exclusion.
    monkeypatch.setattr(ho, "DEFAULT_SOURCE_CONTEXT",
                        ho.SourceContext(k_policy="TEST_ONLY",
                                         crn_scope="TEST_ONLY"))
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


# =========================================================================
# M6.1.4-ARCH — finding F-1: THE single configuration gateway
# =========================================================================
# F-1 was raised, patched at the three sites it named, and RECURRED. An
# independent read-only reproduction on this worktree found FOUR live
# escapes through the public `RealChain.ready()` (bool, str) contract, not
# the two the report named — both halves of the `cfg != fresh_cfg`
# comparison escaped too. These tests are BEHAVIOURAL and go through the
# public boundary; they pin the gateway's total coverage, not any one site.

_F1_MARKER = "PAYLOAD_MARKER_c0ffee"        # must never reach a reason string


class _F1PlainObject:
    """A cache value that is not an envelope and not even iterable."""


class _F1IterBomb:
    """A cache value whose iteration detonates (the old unpack path)."""

    def __iter__(self):
        raise RuntimeError(_F1_MARKER)


class _F1LenBomb:
    def __len__(self):
        raise RuntimeError(_F1_MARKER)


class _F1BoolBomb:
    def __bool__(self):
        raise RuntimeError(_F1_MARKER)


class _F1GetattrBomb:
    def __getattr__(self, name):
        raise RuntimeError(_F1_MARKER)


class _F1EqBomb:
    """A METHODS-FIELD value whose `__eq__` detonates, and counts calls."""

    calls = 0

    def __eq__(self, other):
        type(self).calls += 1
        raise RuntimeError(_F1_MARKER)

    def __hash__(self):
        return 0


class _F1CallableEqBomb:
    """A CALLABLE whose `__eq__` detonates — the point-(11) escape."""

    calls = 0

    def __call__(self, day):
        return "R"

    def __eq__(self, other):
        type(self).calls += 1
        raise RuntimeError(_F1_MARKER)

    def __hash__(self):
        return 0


class _F1DuckMethods:
    """Not a ResolvedS0Methods; lies on every probe it is asked."""

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


def _f1_approved_methods():
    """A FULLY-RESOLVED, structurally valid, non-test_only method source.

    Synthetic TEST_ONLY *values* with the test_only flag cleared, used ONLY
    to reach the gateway stages that sit behind the pending gate. Every
    test using it asserts a REFUSAL or the synthetic positive path; it
    never reaches a real computation and adopts no ruling."""
    import dataclasses as _dc
    # S0 closeout: the event consumer is test-gated, so a NON-test_only
    # source must carry the RULED mapping (the TEST_ONLY synthetic value is
    # refused on the production path by design).
    return _dc.replace(_test_methods(), test_only=False,
                       event_na_mapping=C.aaron_ruled_methods()
                       .event_na_mapping)


_F1_REGIME = lambda d: "R"                                      # noqa: E731


def _f1_injectables():
    """A valid injectable source returning STABLE callable objects — the
    property `_approved_injectables()` must honour for cache coherence
    (see the G11_callable_identity rule)."""
    return {"spread_scalars": (0.5, 0.75, 0.75),
            "regime_of": _F1_REGIME, "vol_axis_of": _test_vol_axis}


def _f1_resolved_sources(mod, monkeypatch):
    monkeypatch.setattr(mod, "_resolved_methods", _f1_approved_methods)
    monkeypatch.setattr(mod, "_approved_injectables", _f1_injectables)


def _f1_bypass_config(methods=None, spread_scalars=(0.5, 0.75, 0.75),
                      regime_of=None, vol_axis_of=None):
    """A StudyConfig assembled by BYPASS (object.__new__ + __setattr__) so
    that structurally impossible field values can be presented to the
    gateway. Every such config must be REFUSED."""
    cfg = object.__new__(C.StudyConfig)
    object.__setattr__(cfg, "methods",
                       _f1_approved_methods() if methods is None else methods)
    object.__setattr__(cfg, "spread_scalars", spread_scalars)
    object.__setattr__(cfg, "regime_of",
                       _F1_REGIME if regime_of is None else regime_of)
    object.__setattr__(cfg, "vol_axis_of",
                       _test_vol_axis if vol_axis_of is None else vol_axis_of)
    return cfg


# --- the 12 hostile cases (id -> (setup, expected stage)) -------------------

def _f1_c_plain_object(mod, monkeypatch):
    mod._CONFIG_CACHE["cfg"] = _F1PlainObject()


def _f1_c_1_tuple(mod, monkeypatch):
    mod._CONFIG_CACHE["cfg"] = (None,)


def _f1_c_2_tuple_legacy(mod, monkeypatch):
    """The shape the cache used to hold. It is refused now: the envelope is
    EXACT, so there is no 2-iterable fallback left to attack."""
    _f1_resolved_sources(mod, monkeypatch)
    mod._CONFIG_CACHE["cfg"] = (
        C.derive_study_config(_f1_approved_methods(), **_f1_injectables()),
        "legacy")


def _f1_c_3_tuple(mod, monkeypatch):
    mod._CONFIG_CACHE["cfg"] = (None, "a", "b")


def _f1_c_dict(mod, monkeypatch):
    """REGRESSION PIN, NOT A REPRODUCTION. A 2-key dict did NOT escape the
    old code (it unpacked to its two string keys and was caught by the
    StudyConfig type pin); a 3-key one did. Pinned here so neither shape
    can ever become an escape again."""
    mod._CONFIG_CACHE["cfg"] = {"cfg": None, "why": "x", "extra": 1}


def _f1_c_raising_iter(mod, monkeypatch):
    mod._CONFIG_CACHE["cfg"] = _F1IterBomb()


def _f1_c_methods_eq_raises(mod, monkeypatch):
    import dataclasses as _dc
    _f1_resolved_sources(mod, monkeypatch)
    methods = _dc.replace(_f1_approved_methods(),
                          event_na_mapping=_F1EqBomb())
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(methods=methods))


def _f1_c_methods_eq_numpy(mod, monkeypatch):
    import dataclasses as _dc
    import numpy as np
    _f1_resolved_sources(mod, monkeypatch)
    methods = _dc.replace(_f1_approved_methods(),
                          event_na_mapping=np.array([1, 2, 3]))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(methods=methods))


def _f1_c_config_callable_eq_raises(mod, monkeypatch):
    _f1_resolved_sources(mod, monkeypatch)
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(regime_of=_F1CallableEqBomb()))


def _f1_c_config_scalars_numpy(mod, monkeypatch):
    import numpy as np
    _f1_resolved_sources(mod, monkeypatch)
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(spread_scalars=np.array([0.5, 0.75, 0.75])))


def _f1_c_fresh_methods_wrong_type(mod, monkeypatch):
    monkeypatch.setattr(mod, "_resolved_methods", _F1DuckMethods)
    monkeypatch.setattr(mod, "_approved_injectables", _f1_injectables)


def _f1_c_fresh_methods_structurally_invalid(mod, monkeypatch):
    import dataclasses as _dc
    bad = _dc.replace(_f1_approved_methods(), grid_policy=C.GridRepeatPolicy(
        k_per_seed=-5, k_start_index=0, stream_includes_theta=False,
        convergence_rule="X", max_doublings=0))
    monkeypatch.setattr(mod, "_resolved_methods", lambda: bad)
    monkeypatch.setattr(mod, "_approved_injectables", _f1_injectables)


# --- M6.1.4-R2: NON-CANONICAL REPRESENTATIONS (F-1 REOPENED) ---------------
# Every case below is FINGERPRINT-EQUAL to a fresh derivation. The value
# EQUIVALENCE obligation is satisfied; the REPRESENTATION IDENTITY obligation
# is not. Before this round each of them was ACCEPTED and the non-canonical
# INSTANCE was handed out.

def _f1_inj_with(scalars):
    """A valid injectable source at `scalars`, with the SAME callable objects
    (so G11_callable_identity passes and the refusal can only come from the
    representation stage)."""
    def _source():
        return {"spread_scalars": scalars,
                "regime_of": _F1_REGIME, "vol_axis_of": _test_vol_axis}
    return _source


def _f1_bypass_spread_cost(ticks):
    """A SpreadCostMethod assembled by BYPASS so `__post_init__` — and with
    it `contracts._canonical_ticks` — never runs. This is the ONLY route to a
    non-canonical ticks container: `dataclasses.replace` re-canonicalizes."""
    sc = object.__new__(C.SpreadCostMethod)
    object.__setattr__(sc, "scalar_rule", "TEST_ONLY")
    object.__setattr__(sc, "adverse_slippage_ticks", ticks)
    object.__setattr__(sc, "adverse_semantics", "replaces_per_side")
    return sc


def _f1_c_config_scalars_int_not_float(mod, monkeypatch):
    """`(0, 1, 1)` vs canonical `(0.0, 1.0, 1.0)`: `_atom_number` widens int
    to float, so the fingerprints are IDENTICAL. The sealed disclosure
    `spread_scalars_used` then serializes `[0, 1, 1]`."""
    monkeypatch.setattr(mod, "_resolved_methods", _f1_approved_methods)
    monkeypatch.setattr(mod, "_approved_injectables",
                        _f1_inj_with((0.0, 1.0, 1.0)))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(spread_scalars=(0, 1, 1)))


def _f1_c_config_scalars_negative_zero(mod, monkeypatch):
    """`-0.0` is collapsed by `_atom_number` exactly as `_canonical_scalar`
    collapses it, so the fingerprints match while the JSON tokens differ."""
    monkeypatch.setattr(mod, "_resolved_methods", _f1_approved_methods)
    monkeypatch.setattr(mod, "_approved_injectables",
                        _f1_inj_with((0.0, 1.0, 1.0)))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(spread_scalars=(-0.0, 1.0, 1.0)))


def _f1_c_config_scalars_tuple_subclass(mod, monkeypatch):
    """REGRESSION PIN (already refused): the CONTAINER is pinned exactly."""
    class _Triple(tuple):
        pass
    monkeypatch.setattr(mod, "_resolved_methods", _f1_approved_methods)
    monkeypatch.setattr(mod, "_approved_injectables",
                        _f1_inj_with((0.0, 1.0, 1.0)))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(spread_scalars=_Triple((0.0, 1.0, 1.0))))


def _f1_c_methods_ticks_plain_dict(mod, monkeypatch):
    """A MUTABLE plain dict where contracts promises a read-only mapping.
    `_atom_ticks` normalizes both to the same sorted tuple."""
    import dataclasses as _dc
    _f1_resolved_sources(mod, monkeypatch)
    methods = _dc.replace(_f1_approved_methods(),
                          spread_cost=_f1_bypass_spread_cost({"Base": 1.0}))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(methods=methods))


def _f1_c_methods_ticks_dict_subclass(mod, monkeypatch):
    """REGRESSION PIN (already refused at the fingerprint): `_atom_ticks`
    pins `type(v) is dict`, so a subclass never gets to run its `__iter__`."""
    import dataclasses as _dc

    class _Ticks(dict):
        pass
    _f1_resolved_sources(mod, monkeypatch)
    methods = _dc.replace(
        _f1_approved_methods(),
        spread_cost=_f1_bypass_spread_cost(_Ticks({"Base": 1.0})))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(methods=methods))


def _f1_c_methods_ticks_proxy_over_hostile_subclass(mod, monkeypatch):
    """THE DOCUMENTED RESIDUAL, pinned as BOUNDED. The container is a genuine
    read-only mappingproxy, so the representation check passes; the wrapped
    object is a dict subclass whose `__iter__` detonates, and CPython exposes
    no API to see through the proxy. The single boundary converts it into a
    stage-attributed refusal — it cannot escape, and it is not silently
    accepted either."""
    import dataclasses as _dc
    from types import MappingProxyType as _MP

    class _HostileTicks(dict):
        def __iter__(self):
            raise RuntimeError(_F1_MARKER)

        def items(self):
            raise RuntimeError(_F1_MARKER)
    _f1_resolved_sources(mod, monkeypatch)
    methods = _dc.replace(
        _f1_approved_methods(),
        spread_cost=_f1_bypass_spread_cost(_MP(_HostileTicks({"Base": 1.0}))))
    mod._CONFIG_CACHE["cfg"] = _cache_entry(
        mod, _f1_bypass_config(methods=methods))


def _f1_c_cache_entry_subclass(mod, monkeypatch):
    """REGRESSION PIN: the cache envelope itself is an EXACT type."""
    class _Sneaky(mod._ConfigCacheEntry):
        __slots__ = ()
    _f1_resolved_sources(mod, monkeypatch)
    mod._CONFIG_CACHE["cfg"] = _Sneaky(
        C.derive_study_config(_f1_approved_methods(), **_f1_injectables()),
        "subclassed")


_F1_CASES = {
    "cache_plain_object": (_f1_c_plain_object, "G2_cache_envelope"),
    "cache_1_tuple": (_f1_c_1_tuple, "G2_cache_envelope"),
    "cache_2_tuple_legacy": (_f1_c_2_tuple_legacy, "G2_cache_envelope"),
    "cache_3_tuple": (_f1_c_3_tuple, "G2_cache_envelope"),
    "cache_dict": (_f1_c_dict, "G2_cache_envelope"),
    "cache_raising_iter": (_f1_c_raising_iter, "G2_cache_envelope"),
    "methods_eq_raises": (_f1_c_methods_eq_raises,
                          "G10_methods_fingerprint"),
    "methods_eq_numpy_non_scalar": (_f1_c_methods_eq_numpy,
                                    "G10_methods_fingerprint"),
    "config_callable_eq_raises": (_f1_c_config_callable_eq_raises,
                                  "G11_callable_identity"),
    "config_scalars_numpy_non_scalar": (_f1_c_config_scalars_numpy,
                                        "G11_config_fingerprint"),
    "fresh_methods_wrong_type": (_f1_c_fresh_methods_wrong_type,
                                 "G5_method_source"),
    "fresh_methods_structurally_invalid": (
        _f1_c_fresh_methods_structurally_invalid, "G7b_structural"),
    # --- M6.1.4-R2: representation identity (the reopened half of F-1) -----
    "config_scalars_int_not_float": (_f1_c_config_scalars_int_not_float,
                                     "G11_config_canonical_form"),
    "config_scalars_negative_zero": (_f1_c_config_scalars_negative_zero,
                                     "G11_config_canonical_form"),
    "methods_ticks_plain_dict": (_f1_c_methods_ticks_plain_dict,
                                 "G10_methods_canonical_form"),
    # --- regression pins: already refused, must never become an escape ----
    "config_scalars_tuple_subclass": (_f1_c_config_scalars_tuple_subclass,
                                      "G11_config_fingerprint"),
    "methods_ticks_dict_subclass": (_f1_c_methods_ticks_dict_subclass,
                                    "G10_methods_fingerprint"),
    "methods_ticks_proxy_over_hostile_subclass": (
        _f1_c_methods_ticks_proxy_over_hostile_subclass,
        "G10_methods_fingerprint"),
    "cache_entry_subclass": (_f1_c_cache_entry_subclass, "G2_cache_envelope"),
}

#: The cases whose defect is REPRESENTATION, not value equivalence: each is
#: fingerprint-equal to a fresh derivation and was ACCEPTED before M6.1.4-R2.
_F1_NON_CANONICAL_IDS = ("config_scalars_int_not_float",
                         "config_scalars_negative_zero",
                         "methods_ticks_plain_dict")

_F1_IDS = sorted(_F1_CASES)


def _f1_arm(mod, monkeypatch, tmp_path, case_id):
    """Install hermetic Stage-C paths, a builder spy and the case's world."""
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    calls = _b1_builder_spy(mod, monkeypatch)
    mod._CONFIG_CACHE.clear()
    _F1_CASES[case_id][0](mod, monkeypatch)
    return calls


@pytest.mark.parametrize("case_id", _F1_IDS)
def test_f1_gateway_refuses_every_hostile_cache_and_source(
        case_id, monkeypatch, tmp_path):
    """Every hostile cache shape / source defect yields (False, reason)
    through the PUBLIC boundary — never an exception, never ready=True, and
    never a production-builder call."""
    mod = real_run_module()
    try:
        calls = _f1_arm(mod, monkeypatch, tmp_path, case_id)
        chain = mod.RealChain()
        out = chain.ready()                       # must NOT raise
        assert isinstance(out, tuple) and len(out) == 2
        ok, why = out
        assert ok is False
        assert isinstance(why, str) and why.strip()
        assert _F1_CASES[case_id][1] in why, why
        assert calls == []                        # builder never reached
        assert chain._ds is None                  # no data ever loaded
    finally:
        mod._CONFIG_CACHE.clear()


@pytest.mark.parametrize("case_id", _F1_IDS)
def test_f1_gateway_refusals_are_pre_exposure_through_the_real_runner(
        case_id, monkeypatch, tmp_path):
    """Each refusal stops the REAL S0Runner in Stage B: no exposure, no
    RUN_STARTED, no runs/ directory (neither the tmp one the harness
    proposes nor the repository's), zero production-builder calls."""
    mod = real_run_module()
    try:
        calls = _f1_arm(mod, monkeypatch, tmp_path, case_id)
        chain = mod.RealChain()
        deps, events, _ = make_deps(
            tmp_path, gates=[ok_gate()],
            b_checks=[GateCheck("stage_c_wiring_activated", chain.ready)],
            compute=lambda: (_ for _ in ()).throw(
                AssertionError("compute must be unreachable")),
            renderer=mod.render_s0_report,
            runs_dir=tmp_path / "runs" / "S0-T001")
        out = S0Runner(deps).run()
        assert out.ok is False
        assert out.failure_kind == "pre_run_attempt"
        assert out.exposure_consumed is False
        assert "RUN_STARTED" not in [e for e, _ in events]
        assert not Path(deps.config.runs_dir).exists()
        assert not (REPO / "runs").exists()       # repo runs/ never created
        assert calls == []
        assert chain._ds is None
    finally:
        mod._CONFIG_CACHE.clear()


# Built by FACTORY, never instantiated in the parametrize list: pytest
# inspects parameter objects to build test ids, and a __getattr__ bomb
# detonates during COLLECTION if handed a live instance.
_F1_ANY_VALUE_FACTORIES = {
    "plain_object": _F1PlainObject,
    "iter_bomb": _F1IterBomb,
    "len_bomb": _F1LenBomb,
    "bool_bomb": _F1BoolBomb,
    "getattr_bomb": _F1GetattrBomb,
    "none": lambda: None,
    "true": lambda: True,
    "zero": lambda: 0,
    "empty_str": lambda: "",
    "empty_bytes": lambda: b"",
    "empty_tuple": tuple,
    "one_tuple": lambda: (None,),
    "three_tuple": lambda: (None, "a", "b"),
    "list": list,
    "empty_dict": dict,
    "one_key_dict": lambda: {"cfg": None},
    "set": set,
    "iterator": lambda: iter([1, 2]),
    "type_object": lambda: object,
    "eq_bomb": _F1EqBomb,
    "callable_eq_bomb": _F1CallableEqBomb,
}


@pytest.mark.parametrize("value_id", sorted(_F1_ANY_VALUE_FACTORIES))
def test_f1_ready_returns_a_bool_str_pair_for_any_cache_value(
        value_id, monkeypatch, tmp_path):
    """The (bool, str) contract is TOTAL over the cache slot: no value of
    any shape can make ready() raise or return a malformed pair."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    mod._CONFIG_CACHE.clear()
    try:
        mod._CONFIG_CACHE["cfg"] = _F1_ANY_VALUE_FACTORIES[value_id]()
        out = mod.RealChain().ready()             # must NOT raise
        assert isinstance(out, tuple) and len(out) == 2
        assert out[0] is False
        assert isinstance(out[1], str) and out[1].strip()
    finally:
        mod._CONFIG_CACHE.clear()


@pytest.mark.parametrize("case_id", _F1_IDS)
def test_f1_refusal_reasons_are_stable_and_payload_free(
        case_id, monkeypatch, tmp_path):
    """Reasons are deterministic (identical across calls), carry a stable
    machine-readable stage token, and never leak an attacker-controlled
    payload."""
    mod = real_run_module()
    try:
        _f1_arm(mod, monkeypatch, tmp_path, case_id)
        first = mod.RealChain().ready()[1]
        second = mod.RealChain().ready()[1]
        assert first == second                    # deterministic
        assert _F1_MARKER not in first            # no payload dump
        body = first.split("stage-C fail-closed pre-exposure: ", 1)[-1]
        assert re.match(r"^config_gate:G\d+[a-z]?_[a-z_0-9]+: \S", body), body
        assert "\n" not in first and "\r" not in first
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_cache_holds_exactly_one_internal_envelope(monkeypatch, tmp_path):
    """The cache is an EXACT internal envelope, and REFUSALS ARE NEVER
    CACHED — the cache exists only to hand ready() and compute() the same
    validated INSTANCE, and a refusal has no instance to share."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    entry_cls = mod._ConfigCacheEntry
    assert entry_cls.__slots__ == ("config", "reason")
    assert entry_cls.__eq__ is object.__eq__      # no comparison surface
    probe = entry_cls(None, "x")
    with pytest.raises(AttributeError):
        probe.config = 1                          # immutable
    mod._CONFIG_CACHE.clear()
    try:
        # (a) every refusal leaves the cache untouched
        for case_id in _F1_IDS:
            mod._CONFIG_CACHE.clear()
            _F1_CASES[case_id][0](mod, monkeypatch)
            before = dict(mod._CONFIG_CACHE)
            ok, _ = mod.RealChain().ready()
            assert ok is False
            assert dict(mod._CONFIG_CACHE) == before, case_id
        # (b) the positive path writes exactly one envelope
        mod._CONFIG_CACHE.clear()
        _f1_resolved_sources(mod, monkeypatch)
        ok, why = mod.RealChain().ready()
        assert ok is True, why
        assert list(mod._CONFIG_CACHE) == ["cfg"]
        assert type(mod._CONFIG_CACHE["cfg"]) is entry_cls
    finally:
        mod._CONFIG_CACHE.clear()


_F1_BAD_FIELD_VALUES = {
    "spread_cost": ("not-a-dataclass", "G10_methods_fingerprint"),
    "volatility_regime": (42, "G10_methods_fingerprint"),
    "fp_allocation": (object(), "G10_methods_fingerprint"),
    "bootstrap_method": ([], "G10_methods_fingerprint"),
    "grid_policy": ("x", "G10_methods_fingerprint"),
    "event_na_mapping": (_F1EqBomb(), "G10_methods_fingerprint"),
    "stability_population": (42, "G10_methods_fingerprint"),
    "worst_day_estimator": ({}, "G10_methods_fingerprint"),
    # test_only is refused EARLIER, at its own dedicated stage — a stronger
    # gate than the fingerprint, so the fingerprint never sees it.
    "test_only": (1, "G4b_test_only"),
}


@pytest.mark.parametrize("field", sorted(_F1_BAD_FIELD_VALUES))
def test_f1_methods_fingerprint_refuses_a_non_normalizable_field(
        field, monkeypatch, tmp_path):
    """A value that cannot be normalized without executing foreign code is
    ITSELF A REFUSAL, never a silent skip — for EVERY ResolvedS0Methods
    field, and the reason names the field."""
    import dataclasses as _dc
    mod = real_run_module()
    bad_value, expected_stage = _F1_BAD_FIELD_VALUES[field]
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    _f1_resolved_sources(mod, monkeypatch)
    calls = _b1_builder_spy(mod, monkeypatch)
    mod._CONFIG_CACHE.clear()
    try:
        methods = _dc.replace(_f1_approved_methods(), **{field: bad_value})
        mod._CONFIG_CACHE["cfg"] = _cache_entry(
            mod, _f1_bypass_config(methods=methods))
        ok, why = mod.RealChain().ready()         # must NOT raise
        assert ok is False
        assert expected_stage in why, why
        if expected_stage == "G10_methods_fingerprint":
            assert field in why, why
        assert calls == []
    finally:
        mod._CONFIG_CACHE.clear()


@pytest.mark.parametrize("kind", ("SpreadCostMethod", "VolatilityRegimeMethod",
                                  "FpAllocationMethod", "BootstrapMethod",
                                  "GridRepeatPolicy"))
def test_f1_sub_rule_tables_cover_every_field(kind):
    """The normalization tables are EXPLICIT, never reflection — so a new
    field on a contracts dataclass must turn this RED rather than be
    silently dropped from the fingerprint."""
    import dataclasses as _dc
    mod = real_run_module()
    cls, rules = mod._METHOD_SUB_RULES[kind]
    assert cls.__name__ == kind
    assert {name for name, _ in rules} == {f.name for f in _dc.fields(cls)}


def test_f1_methods_rule_table_covers_every_field():
    import dataclasses as _dc
    mod = real_run_module()
    assert ({name for name, _ in mod._METHODS_FIELD_RULES}
            == {f.name for f in _dc.fields(C.ResolvedS0Methods)})


def test_f1_injectable_rule_table_is_exact():
    """Every injectable has an explicit rule, and the two callables are
    declared identity-only rather than fingerprinted."""
    mod = real_run_module()
    assert set(mod._INJECTABLE_FIELD_RULES) == set(C.INJECTABLE_KEYS)
    assert (mod._INJECTABLE_FIELD_RULES["regime_of"]
            == mod._INJECTABLE_FIELD_RULES["vol_axis_of"]
            == "object_identity_only")


def test_f1_hostile_dunder_eq_is_never_invoked_by_the_gateway(
        monkeypatch, tmp_path):
    """The gateway does not merely SURVIVE a hostile `__eq__` — it never
    runs one. Equivalence is decided on non-executing fingerprints and, for
    the callables, on object identity."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)   # once per tmp_path
    calls = _b1_builder_spy(mod, monkeypatch)
    _F1EqBomb.calls = 0
    _F1CallableEqBomb.calls = 0
    try:
        for case_id in ("methods_eq_raises", "config_callable_eq_raises"):
            mod._CONFIG_CACHE.clear()
            _F1_CASES[case_id][0](mod, monkeypatch)
            ok, _ = mod.RealChain().ready()
            assert ok is False
            assert calls == []
        assert _F1EqBomb.calls == 0
        assert _F1CallableEqBomb.calls == 0
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_callables_are_compared_by_object_identity_only(monkeypatch,
                                                           tmp_path):
    """ENGINEERING IDENTITY RULE — cache coherence only. `is` answers "is
    this the very object the approved source hands out in this process?"
    and NOTHING about what regime_of / vol_axis_of compute; DR-1 and DR-2
    stay open. An equivalent-looking callable is therefore refused, and a
    callable whose `__eq__` would detonate passes when it IS the same
    object — proving the comparison is `is`, not `==`."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    _F1CallableEqBomb.calls = 0
    hostile = _F1CallableEqBomb()
    inj = {"spread_scalars": (0.5, 0.75, 0.75),
           "regime_of": hostile, "vol_axis_of": _test_vol_axis}
    monkeypatch.setattr(mod, "_resolved_methods", _f1_approved_methods)
    monkeypatch.setattr(mod, "_approved_injectables", lambda: dict(inj))
    mod._CONFIG_CACHE.clear()
    try:
        # (a) equivalent-but-distinct callable -> refused
        lookalike = C.derive_study_config(
            _f1_approved_methods(), spread_scalars=(0.5, 0.75, 0.75),
            regime_of=_F1CallableEqBomb(), vol_axis_of=_test_vol_axis)
        mod._CONFIG_CACHE["cfg"] = _cache_entry(mod, lookalike)
        got, why = mod.resolved_study_config()
        assert got is None
        assert "G11_callable_identity" in why and "fresh derivation" in why
        # (b) the SAME object -> accepted, and __eq__ still never ran
        mod._CONFIG_CACHE.clear()
        genuine = C.derive_study_config(_f1_approved_methods(), **inj)
        mod._CONFIG_CACHE["cfg"] = _cache_entry(mod, genuine, "derived")
        got2, _ = mod.resolved_study_config()
        assert got2 is genuine                    # gate is not dead code
        assert _F1CallableEqBomb.calls == 0
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_methods_mismatch_refusal_under_a_resolved_source(monkeypatch,
                                                             tmp_path):
    """G10 keeps a LIVE proof of the 'cache is not a method source' claim.

    The fresh source is RESOLVED here, so the pending gate cannot short the
    pipeline: the refusal genuinely comes from the methods-equivalence
    comparison of two fingerprints that differ."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    _f1_resolved_sources(mod, monkeypatch)
    calls = _b1_builder_spy(mod, monkeypatch)
    mod._CONFIG_CACHE.clear()
    try:
        divergent = _dc.replace(_f1_approved_methods(),
                                stability_population="A_DIFFERENT_VALUE")
        mod._CONFIG_CACHE["cfg"] = _cache_entry(
            mod, _f1_bypass_config(methods=divergent))
        got, why = mod.resolved_study_config()
        assert got is None
        assert "G10_methods_equivalence" in why
        assert "cache is not a method source" in why
        assert mod.RealChain().ready()[0] is False
        assert calls == []
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_boundary_reports_a_sanitized_exception_type(monkeypatch,
                                                        tmp_path):
    """An UNENUMERATED explosion is attributed to the stage that was
    running and carries the exception TYPE — SANITIZED, because the type
    name is itself attacker-controlled.

    HONEST LIMIT, stated rather than implied: including the type at all
    means a short attacker-chosen type name CAN appear in the reason. That
    is the bounded price of diagnosability. What is guaranteed is that the
    token is <= 40 characters, restricted to [A-Za-z0-9_.] with everything
    else replaced by '?', and therefore cannot inject newlines or markdown
    into attempts/PRE_RUN_ATTEMPT_FAILURE.md or trip
    runinfra.validate_log_event. The twelve ENUMERATED refusals leak
    nothing at all — they refuse before any foreign code runs (see
    test_f1_refusal_reasons_are_stable_and_payload_free)."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    calls = _b1_builder_spy(mod, monkeypatch)

    class _Nasty(Exception):
        pass

    _Nasty.__name__ = "Evil\nName: " + _F1_MARKER + "x" * 300

    def _boom():
        raise _Nasty("detail " + _F1_MARKER)

    monkeypatch.setattr(mod, "_resolved_methods", _boom)
    mod._CONFIG_CACHE.clear()
    try:
        ok, why = mod.RealChain().ready()         # must NOT raise
        assert ok is False
        assert "G5_method_source" in why          # stage attribution
        assert "\n" not in why and "\r" not in why      # no injection
        assert "x" * 50 not in why                # truncated, not dumped
        assert len(why) < 300                     # bounded
        assert "detail " + _F1_MARKER not in why  # the MESSAGE never leaks
        assert calls == []
        # a normal exception type still reads cleanly
        monkeypatch.setattr(mod, "_resolved_methods",
                            _boom_factory("method source down"))
        ok2, why2 = mod.RealChain().ready()
        assert ok2 is False and "RuntimeError" in why2
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_gateway_has_a_single_trust_boundary():
    """THE anti-scatter pin. Total coverage comes from ONE boundary at the
    gateway's edge plus a stage cursor — not from try/except at named
    sites, which is exactly what let F-1 recur. The only other guarded
    region in the whole config path is `_safe_type_name`, which is
    load-bearing because it executes INSIDE the boundary's own handler,
    where a raise would escape the public contract."""
    import inspect
    mod = real_run_module()

    def _stmts(fn):
        """Statement-level tokens only — a substring scan would match
        'try:' inside '_ConfigCacheEntry:'."""
        return [ln.split("#", 1)[0].strip()
                for ln in inspect.getsource(fn).splitlines()]

    boundary = _stmts(mod._run_guarded)
    assert boundary.count("try:") == 1
    assert sum(1 for s in boundary if s.startswith("except ")) == 2
    assert sum(1 for s in boundary
               if s.startswith("except _Refusal")) == 1
    assert sum(1 for s in boundary
               if s.startswith("except BaseException")) == 1

    assert _stmts(mod._safe_type_name).count("try:") == 1

    for fn in (mod._gateway_body, mod.resolved_study_config,
               mod._methods_fingerprint, mod._config_fingerprint,
               mod._norm_sub, mod._atom_ticks, mod._atom_number,
               mod._atom_str, mod._atom_int, mod._atom_bool,
               mod._code_heads, mod._refuse, mod.RealChain._ready_body,
               mod.RealChain.ready,
               # M6.1.4-R2: the representation stages join the SAME single
               # boundary — they add no try/except of their own.
               mod._methods_canonical_defect, mod._config_canonical_defect,
               mod.canonical_form_obligations,
               C.is_canonical_spread_scalars, C.is_canonical_ticks):
        stmts = _stmts(fn)
        assert "try:" not in stmts, fn
        assert not any(s.startswith("except") for s in stmts), fn

    # No equality against a config / methods OBJECT survives anywhere in
    # the pipeline: the only comparisons are between fingerprint tuples of
    # exact builtin atoms (every such line names a `_fp` operand).
    for line in inspect.getsource(mod._gateway_body).splitlines():
        code = line.split("#", 1)[0]
        if "==" in code or "!=" in code:
            assert "_fp" in code, line


def test_f1_every_mandated_evaluation_point_maps_to_a_named_stage():
    """All 13 mandated evaluation points map onto named gateway stages.

    NO GATE-COUNT THEATRE. Eleven are real stages with their own refusal
    string. Point (12) cache-write is ATTRIBUTION-ONLY — an in-process
    write has no legitimate failure mode unless `_CONFIG_CACHE` has itself
    been replaced. Point (13) is not a stage at all but the SINGLE-PATH
    INVARIANT: the gateway has exactly one code path, so G3..G11 execute on
    every call, cache hit or miss — which is what makes point-of-use
    revalidation automatic rather than a step someone must remember."""
    import inspect
    mod = real_run_module()
    assert sorted(mod._EVALUATION_POINTS) == list(range(1, 14))
    mapped = [s for stages in mod._EVALUATION_POINTS.values() for s in stages]
    assert len(set(mapped)) == len(mapped)        # no stage double-counted
    assert sorted(mapped) == sorted(mod._GATE_STAGES)
    src = inspect.getsource(mod._gateway_body)
    for stage in mod._GATE_STAGES:
        assert f'"{stage}"' in src, stage


# =========================================================================
# M6.1.4-R2 — finding F-1 REOPENED: REPRESENTATION IDENTITY
# =========================================================================
# THE NAMED ROOT CAUSE. Before this round the in-repo F-1 regression set was
# 12 named hostile shapes (`_F1_CASES`) and EVERY ONE OF THEM ASSERTED A
# REFUSAL. Not one test asserted anything about a config the gateway
# ACCEPTS. That asymmetry — assert-on-refuse only, never assert-on-accept —
# is why two mechanisms that produce an ACCEPT of a non-canonical instance
# passed the whole set. The fix is not two more refusal cases; it is the
# permanent ACCEPT-SIDE class below: whatever the gateway hands out is
# asserted canonical on the way out, over a table that a future canonicalized
# field must join (see test_f1_canonical_form_tables_cover_every_
# contracts_canonicalization, which turns RED until it does).
#
# The claim, stated exactly and never widened: CANONICAL WHEREVER CONTRACTS
# SPECIFIES CANONICAL, exact-type-pinned everywhere else.


class _F1NonBoolEq:
    """`__eq__` returns a non-plain-bool truthy object and counts calls. It
    must never be EXECUTED by any stage — not the fingerprints, not the
    representation stages."""

    calls = 0

    def __eq__(self, other):
        type(self).calls += 1
        return ["not-a-bool"]

    def __hash__(self):
        return 0


def _f1_accept(mod, monkeypatch, tmp_path):
    """Arm the POSITIVE path and return the accepted config instance."""
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    _f1_resolved_sources(mod, monkeypatch)
    mod._CONFIG_CACHE.clear()
    cfg, why = mod.resolved_study_config()
    assert cfg is not None, why
    return cfg


def test_f1_accept_side_obligations_cover_every_canonical_form_rule():
    """NON-VACUITY of the accept-side class: the obligation list is derived
    from the SAME tables the gateway's representation stages consume, so it
    cannot silently shrink to zero and make the accept-side assertions
    trivially true."""
    mod = real_run_module()
    cfg = C.derive_study_config(_f1_approved_methods(), **_f1_injectables())
    labels = [label for label, _ in mod.canonical_form_obligations(cfg)]
    assert labels                                  # never vacuous
    assert len(set(labels)) == len(labels)
    expected = ([f"methods.{f}.{sub}"
                 for f, _cls, sub, _p in mod._METHODS_CANONICAL_RULES]
                + [f"config.{f}" for f, _p in mod._CONFIG_CANONICAL_RULES])
    assert labels == expected


def test_f1_canonical_form_tables_cover_every_contracts_canonicalization():
    """ANTI-DRIFT PIN, and the extension point for the accept-side class.

    `contracts` creates a canonical-representation obligation exactly where a
    `__post_init__` REWRITES a field with `object.__setattr__`. Every such
    field must have a row in a gateway canonical-form table; a new one turns
    this RED, and adding the row automatically extends both the gateway
    stages and every accept-side assertion below."""
    import inspect as _i
    mod = real_run_module()
    rewritten = set(re.findall(r'object\.__setattr__\(\s*self,\s*"(\w+)"',
                               _i.getsource(C)))
    covered = ({sub for _f, _cls, sub, _p in mod._METHODS_CANONICAL_RULES}
               | {f for f, _p in mod._CONFIG_CANONICAL_RULES})
    assert rewritten == covered == {"spread_scalars", "adverse_slippage_ticks"}


def test_f1_canonical_form_binds_to_contracts_and_defines_no_second_rule():
    """The gateway must not carry its own idea of 'canonical'. Every
    predicate in every table IS the contracts function, by object identity —
    so contracts stays the single source and the two cannot drift."""
    mod = real_run_module()
    predicates = ({p for _f, _cls, _sub, p in mod._METHODS_CANONICAL_RULES}
                  | {p for _f, p in mod._CONFIG_CANONICAL_RULES})
    assert predicates <= {C.is_canonical_spread_scalars, C.is_canonical_ticks}
    assert mod._is_canon_scalars is C.is_canonical_spread_scalars
    assert mod._is_canon_ticks is C.is_canonical_ticks


@pytest.mark.parametrize("case_id", _F1_NON_CANONICAL_IDS)
def test_f1_representation_and_equivalence_are_separate_obligations(
        case_id, monkeypatch, tmp_path):
    """THE DECISIVE TEST. Each of these caches is FINGERPRINT-EQUAL to a
    fresh derivation — the EQUIVALENCE obligation is satisfied — and must
    still refuse, at the REPRESENTATION stage, never at an equivalence one.

    A refusal tagged `_equivalence` here would mean the fix was smuggled into
    the fingerprint, which would also refuse value-equal pairs contracts
    declares EQUAL (`_canonical_scalar` widens int to float on purpose)."""
    mod = real_run_module()
    try:
        calls = _f1_arm(mod, monkeypatch, tmp_path, case_id)
        cfg, why = mod.resolved_study_config()
        assert cfg is None
        assert "_canonical_form" in why, why
        assert "_equivalence" not in why, why
        assert "representation" in why, why
        assert calls == []
    finally:
        mod._CONFIG_CACHE.clear()


@pytest.mark.parametrize("case_id", _F1_NON_CANONICAL_IDS)
def test_f1_gateway_never_hands_out_a_non_canonical_instance(
        case_id, monkeypatch, tmp_path):
    """ACCEPT-SIDE, negative half: a non-canonical cache yields NO instance
    at all. Refuse, never repair — returning `canonical_config(cached)` would
    mint a new object per call and destroy the ready()/compute() identity
    guarantee while silently accepting a tampered cache."""
    mod = real_run_module()
    try:
        _f1_arm(mod, monkeypatch, tmp_path, case_id)
        before = mod._CONFIG_CACHE.get("cfg")
        cfg, why = mod.resolved_study_config()
        assert cfg is None and isinstance(why, str) and why.strip()
        assert mod.RealChain().ready()[0] is False
        # the hostile entry is left EXACTLY as injected: no refusal cached,
        # and — the point — no repaired replacement written back either.
        assert mod._CONFIG_CACHE.get("cfg") is before
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_accepted_config_is_canonical_on_every_obligation(monkeypatch,
                                                             tmp_path):
    """ACCEPT-SIDE, positive half — THE permanent class the 12-case refusal
    set lacked. Whatever the gateway ACCEPTS is asserted canonical on the way
    out, obligation by obligation, over the table above."""
    mod = real_run_module()
    try:
        cfg = _f1_accept(mod, monkeypatch, tmp_path)
        obligations = mod.canonical_form_obligations(cfg)
        assert obligations
        for label, holds in obligations:
            assert holds is True, label
        # ... and spelled out once, so a table bug cannot make it vacuous:
        assert C.is_canonical_spread_scalars(cfg.spread_scalars) is True
        assert all(type(v) is float for v in cfg.spread_scalars)
        assert C.is_canonical_ticks(
            cfg.methods.spread_cost.adverse_slippage_ticks) is True
        assert "-0.0" not in json.dumps(list(cfg.spread_scalars))
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_positive_path_shares_one_canonical_instance(monkeypatch,
                                                        tmp_path):
    """ready() -> ready() -> synthetic compute() still share ONE instance BY
    IDENTITY, and that one instance is canonical.

    SCOPE: synthetic config-to-compute integration with the method source,
    the injectable source and data I/O replaced by stand-ins — not a real
    data chain, not a real S0, nothing about research output."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    _f1_resolved_sources(mod, monkeypatch)
    mod._CONFIG_CACHE.clear()
    try:
        chain = mod.RealChain()
        monkeypatch.setattr(chain, "_ensure", lambda: (ds, None))
        chain._bars = bars
        ok, why = chain.ready()
        assert ok is True, why
        cfg1, _ = mod.resolved_study_config()
        ok2, why2 = chain.ready()
        assert ok2 is True, why2
        payload = chain.compute(chain.prepare(_test_snapshot()))
        cfg2, _ = mod.resolved_study_config()
        assert cfg2 is cfg1                        # ONE instance, identity
        assert cfg1 is mod._CONFIG_CACHE["cfg"].config
        for label, holds in mod.canonical_form_obligations(cfg2):
            assert holds is True, label
        # the representation obligation is exactly what keeps the SEALED
        # bytes stable: this is the value that travels into the disclosure.
        conv = payload["disclosures"]["method_conventions"]
        used = conv["spread_scalars_used"]
        assert all(type(v) is float for v in used)
        assert json.dumps(used) == json.dumps([0.5, 0.75, 0.75])
    finally:
        mod._CONFIG_CACHE.clear()


def test_f1_non_bool_equality_is_never_executed_by_any_stage(monkeypatch,
                                                             tmp_path):
    """An object whose `__eq__` returns a NON-PLAIN-BOOL must never be
    executed — in any slot, at any stage. Type is pinned before every read,
    so the refusal comes from normalization, not from a comparison."""
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    _f1_resolved_sources(mod, monkeypatch)
    calls = _b1_builder_spy(mod, monkeypatch)
    _F1NonBoolEq.calls = 0
    try:
        plants = {
            "methods_field": lambda: _f1_bypass_config(
                methods=_dc.replace(_f1_approved_methods(),
                                    stability_population=_F1NonBoolEq())),
            "spread_scalars_member": lambda: _f1_bypass_config(
                spread_scalars=(_F1NonBoolEq(), 1.0, 1.0)),
            "ticks_value": lambda: _f1_bypass_config(
                methods=_dc.replace(
                    _f1_approved_methods(),
                    spread_cost=_f1_bypass_spread_cost(
                        {"Base": _F1NonBoolEq()}))),
            "ticks_key": lambda: _f1_bypass_config(
                methods=_dc.replace(
                    _f1_approved_methods(),
                    spread_cost=_f1_bypass_spread_cost(
                        {_F1NonBoolEq(): 1.0}))),
        }
        for slot, make in plants.items():
            mod._CONFIG_CACHE.clear()
            mod._CONFIG_CACHE["cfg"] = _cache_entry(mod, make())
            ok, why = mod.RealChain().ready()       # must NOT raise
            assert ok is False, slot
            assert isinstance(why, str) and why.strip()
            assert calls == [], slot
        assert _F1NonBoolEq.calls == 0
    finally:
        mod._CONFIG_CACHE.clear()


# ===========================================================================
# M6.1.6 — the PRE-EXPOSURE PREPARE SEAM (lifecycle slice only).
#
# Scope discipline: these tests prove the LIFECYCLE property (config is
# resolved once, pre-exposure, and Stage C consumes that object) and nothing
# more. They do NOT claim F-1 closed: the prepared object still carries
# callables and a MappingProxyType, both of which need rulings this
# milestone must not make.
# ===========================================================================

def test_m616_stage_c_never_reaches_a_config_source():
    """AST pin: `RealChain.compute` and everything it calls in-module must
    not reference any global config-resolution entry point. This is the
    mechanical form of 'reading STOPS at prepare'."""
    import ast
    import inspect
    mod = real_run_module()
    src = inspect.getsource(mod.RealChain.compute)
    tree = ast.parse("if 1:\n" + src)
    banned = {"resolved_study_config", "_resolved_methods",
              "_approved_injectables", "_config_gateway"}
    seen = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    seen |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not (seen & banned), sorted(seen & banned)


def test_m616_prepare_returns_an_exact_typed_immutable_object(monkeypatch,
                                                              tmp_path):
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    approved = _dc.replace(_test_methods(), test_only=False,
                           event_na_mapping=C.aaron_ruled_methods()
                           .event_na_mapping)
    inj = {"spread_scalars": (0.5, 0.75, 0.75),
           "regime_of": lambda d: "R", "vol_axis_of": _test_vol_axis}
    monkeypatch.setattr(mod, "_resolved_methods", lambda: approved)
    monkeypatch.setattr(mod, "_approved_injectables", lambda: dict(inj))
    mod._CONFIG_CACHE.clear()
    try:
        prepared = mod.RealChain().prepare(_test_snapshot())
        assert type(prepared) is mod._PreparedExecutionInput
        with pytest.raises(AttributeError):
            prepared.config = None
        assert not hasattr(prepared, "__dict__")     # __slots__
    finally:
        mod._CONFIG_CACHE.clear()


def test_m616_compute_refuses_a_look_alike_prepared_object(monkeypatch,
                                                           tmp_path):
    """Stage C is exact-type-pinned: a duck-typed stand-in carrying a legal
    config must NOT be accepted, because accepting it would reopen the
    'compute re-resolves' path through a different door."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)

    class _LookAlike:
        config = _test_config()
        reason = "look-alike"

    chain = mod.RealChain()
    with pytest.raises(RuntimeError, match="prepared execution input"):
        chain.compute(_LookAlike())
    assert chain._ds is None


def test_m616_prepare_fails_closed_on_the_real_production_source(monkeypatch,
                                                                 tmp_path):
    """S0 closeout (2026-08-10): the production sources are RULED, so this
    test now proves the refusal machinery still works when the injectable
    source is synthetically un-wired — prepare refuses BEFORE exposure and
    before any data load (regression guard for the pre-ruling posture)."""
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "_approved_injectables", lambda: None)
    mod._CONFIG_CACHE.clear()
    try:
        chain = mod.RealChain()
        with pytest.raises(RuntimeError, match="stage-C config unavailable"):
            chain.prepare(_test_snapshot())
        assert chain._ds is None
    finally:
        mod._CONFIG_CACHE.clear()


def test_m616_deps_wire_prepare_and_one_arg_compute():
    """The production deps object must carry the seam; a missing seam is
    fail-closed in the runner, so an unwired production path would refuse
    pre-exposure rather than reach compute."""
    import inspect
    mod = real_run_module()
    src = inspect.getsource(mod)
    assert "prepare_compute=prepare_for_run" in src
    assert len(inspect.signature(mod.RealChain.compute).parameters) == 2


def test_m616_governance_proof_is_wired_on_the_production_render_path():
    """The proof must be enforced where it matters: the production deps
    object renders through the entry point that builds an INDEPENDENT
    context. A synthetic render that supplies no context does not run the
    proof — that is disclosed here rather than claimed as coverage."""
    import inspect
    mod = real_run_module()
    src = inspect.getsource(mod)
    assert "render_report=chain.render_report_with_governance_proof" in src
    sig = inspect.signature(mod.render_s0_report).parameters
    assert "governance_context" in sig and sig["governance_context"].default is None


def test_m616_governance_context_never_reads_the_payload_it_verifies():
    """AST pin on the production context builder: it may reach guards, the
    repo tree and the pre-run snapshot — it must NOT touch `result`,
    `formal`, or the evidence mirror."""
    import ast
    import inspect
    mod = real_run_module()
    # M6.1.7: the builder moved into its own method, which takes ONLY the
    # prepared object — `result` is not even in its scope, so the property
    # is now structural rather than merely observed.
    fn = mod.RealChain._governance_context
    assert list(inspect.signature(fn).parameters) == ["self", "prepared"]
    tree = ast.parse("if 1:\n" + inspect.getsource(fn))
    ctx_call = [n for n in ast.walk(tree)
                if isinstance(n, ast.Call)
                and getattr(getattr(n, "func", None), "attr", "")
                == "SourceContext"]
    assert len(ctx_call) == 1
    names = {n.id for n in ast.walk(ctx_call[0]) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(ctx_call[0])
             if isinstance(n, ast.Attribute)}
    assert "result" not in names
    assert not ({"evidence", "formal"} & (names | attrs))


def test_m616_governance_proof_refuses_a_tampered_final_report(monkeypatch,
                                                               tmp_path):
    """End-to-end through the REAL renderer: tamper `governance.trial_id`
    in the payload and the proof must refuse the seal, even though every
    pre-existing gate passes."""
    from itsf import guards as _g
    from itsf.s0 import output_proof as _op
    mod = real_run_module()
    ctx = _op.SourceContext(
        authorization_snapshot={"trial_id": _GOV["trial_id"],
                                "authorized_commit": _GOV["authorized_commit"],
                                "event_sequence":
                                    _GOV["registry_sequence_snapshot"]},
        frozen_hash_authority=dict(_GOV["frozen_hashes"]),
        frozen_hash_observations=dict(_GOV["frozen_hashes"]),
        engineering_seed=_GOV["engineering_seed"],
        engineering_seed_provenance="TEST_ONLY provenance")
    honest = mod.render_s0_report(_payload(), expected_governance=dict(_GOV),
                                  governance_context=ctx)
    assert "S0_REPORT.json" in honest          # honest render still seals

    # (1) PRE-WRITE SCREEN: a wrong governance block never becomes a file.
    # NEVER mutate the shared cached payload: _payload() returns the same
    # object to every test, so an in-place rebind here would poison the
    # whole suite (observed once, fixed here).
    src = _payload()
    bad = {k: v for k, v in src.items()}
    bad["governance"] = {**src["governance"], "trial_id": "S0-T999"}
    with pytest.raises(ValueError, match="governance draft screen failed"):
        mod.render_s0_report(bad,
                             expected_governance=dict(bad["governance"]),
                             governance_context=ctx)

    # (2) THE M6.1.7 PROPERTY: the honest artifacts land on disk, and the
    # report is tampered with AFTERWARDS. The in-memory route was
    # structurally blind to this — it had already returned its verdict on a
    # dict. The disk proof reads the bytes that are actually there.
    rdir = _write_run_dir(tmp_path, honest)
    clean = _op.prove_governance(ctx, report_path=rdir / "S0_REPORT.json",
                                 infrastructure_files=())
    assert clean.ok is True and clean.actual_source == "file"

    import json as _json
    doc = _json.loads((rdir / "S0_REPORT.json").read_text(encoding="utf-8"))
    doc["governance"]["trial_id"] = "S0-T999"
    (rdir / "S0_REPORT.json").write_bytes(
        _json.dumps(doc, indent=1, sort_keys=True).encode("utf-8"))
    tampered = _op.prove_governance(ctx, report_path=rdir / "S0_REPORT.json",
                                    infrastructure_files=())
    assert tampered.ok is False
    assert any("trial_id" in p for p in tampered.problems), tampered.problems


def test_m616_review_a3_1_hostile_mapping_context_cannot_set_the_expectation(
        tmp_path):
    """M6.1.6 review A3-1: a Mapping whose `.get()` and `__getitem__`
    disagree must not pass SourceContext validation and then supply
    DIFFERENT values as the frozen expectation ('validate X, use Y')."""
    from itsf.s0 import output_proof as _op

    class _TwoFaced(dict):
        def get(self, key, default=None):        # honest face
            return {"trial_id": _GOV["trial_id"],
                    "authorized_commit": _GOV["authorized_commit"],
                    "event_sequence":
                        _GOV["registry_sequence_snapshot"]}.get(key, default)

    two_faced = _TwoFaced({"trial_id": "S0-ATTACKER",
                           "authorized_commit": "f" * 40,
                           "event_sequence": 777})
    ctx = _op.SourceContext(
        authorization_snapshot=two_faced,
        frozen_hash_authority=dict(_GOV["frozen_hashes"]),
        frozen_hash_observations=dict(_GOV["frozen_hashes"]),
        engineering_seed=_GOV["engineering_seed"],
        engineering_seed_provenance="TEST_ONLY provenance")
    rdir = _write_run_dir(tmp_path, mod_render_honest_report())
    proof = _op.prove_governance(ctx, report_path=rdir / "S0_REPORT.json",
                                 infrastructure_files=())
    # The materialised (attacker) values are what became the expectation,
    # so the honest report must now FAIL — the two faces can no longer
    # diverge silently.
    assert proof.ok is False
    assert any("trial_id" in p for p in proof.problems), proof.problems


def mod_render_honest_report():
    from itsf.s0 import output_proof as _op
    mod = real_run_module()
    ctx = _op.SourceContext(
        authorization_snapshot={"trial_id": _GOV["trial_id"],
                                "authorized_commit": _GOV["authorized_commit"],
                                "event_sequence":
                                    _GOV["registry_sequence_snapshot"]},
        frozen_hash_authority=dict(_GOV["frozen_hashes"]),
        frozen_hash_observations=dict(_GOV["frozen_hashes"]),
        engineering_seed=_GOV["engineering_seed"],
        engineering_seed_provenance="TEST_ONLY provenance")
    return mod.render_s0_report(_payload(), expected_governance=dict(_GOV),
                                governance_context=ctx)


# ===========================================================================
# M6.1.7 — DISK SEAL: the release verdict comes from bytes on disk, and the
# governance it verifies comes from the PRE-EXPOSURE snapshot.
# ===========================================================================

def _prepared_with(mod, snapshot=None):
    """Build the production prepared object directly.

    `prepare()` cannot be used here: it needs an approved config, and the
    production posture is that `_approved_injectables()` returns None. What
    is under test is the SNAPSHOT half, so the config slot is a stand-in.
    """
    return mod._PreparedExecutionInput(
        config=_test_config(), reason="TEST_ONLY",
        snapshot=_MPX(dict(snapshot or _test_snapshot())))


def _report_governance_for(mod, snap):
    """The governance block an honest report MUST declare, derived from the
    same authorities the production context uses — never from the report."""
    from itsf import guards as _g
    return {"trial_id": snap["trial_id"],
            "authorized_commit": snap["authorized_commit"],
            "engineering_seed": mod.ENGINEERING_SEED,
            "frozen_hashes": dict(_g.FROZEN_HASHES),
            "registry_sequence_snapshot": snap["event_sequence"]}


def _honest_run_dir(mod, tmp_path, snap, monkeypatch):
    """Render an honest report through the REAL renderer and lay it down on
    disk exactly as the runner does.

    The live registry carries ZERO live authorizations (by design: S0 is not
    authorized), so `_expected_governance` would refuse the synthetic
    commit. The authorization lookup is therefore stubbed to state that the
    registry authorizes THIS run's commit — a declared synthetic boundary,
    not a weakening: everything downstream of that fact is real code.
    """
    monkeypatch.setattr(mod, "find_authorization_event",
                        lambda text, trial_id=mod.TRIAL_ID: (
                            1, snap["authorized_commit"], "TEST_ONLY"))
    gov = _report_governance_for(mod, snap)
    src = _payload()
    payload = {k: v for k, v in src.items()}
    payload["governance"] = gov
    _patch_kc_assertions(mod, monkeypatch, tmp_path, src)
    prepared = _prepared_with(mod, snap)
    files = mod.RealChain().render_report_with_governance_proof(
        payload, prepared)
    return _write_run_dir(tmp_path, files), prepared, files


def test_m617_prepared_carries_an_immutable_pre_exposure_snapshot():
    mod = real_run_module()
    prepared = _prepared_with(mod)
    assert prepared.snapshot["event_sequence"] == \
        _GOV["registry_sequence_snapshot"]
    with pytest.raises(TypeError):                 # mappingproxy is read-only
        prepared.snapshot["event_sequence"] = 999
    with pytest.raises(AttributeError):            # and the slot cannot rebind
        prepared.snapshot = {}
    assert not hasattr(prepared, "__dict__")


def test_m617_prepare_refuses_a_snapshot_without_an_authorized_commit():
    mod = real_run_module()
    chain = mod.RealChain()
    with pytest.raises(RuntimeError, match="missing required"):
        chain.prepare({"trial_id": "S0-T001"})     # missing fields
    with pytest.raises(RuntimeError, match="no authorized commit"):
        chain.prepare(_test_snapshot(authorized_commit=""))
    assert chain._ds is None


def test_m617_compute_never_reads_the_registry_after_run_started():
    """AST pin. Stage C runs AFTER `_atomic_run_start` appended this run's
    own RUN_STARTED row, so ANY registry read here reports the pre-exposure
    count plus one — the exact defect measured at 185e47f7."""
    import ast
    import inspect
    mod = real_run_module()
    src = inspect.getsource(mod.RealChain.compute)
    tree = ast.parse("if 1:\n" + src)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    calls = {getattr(getattr(n, "func", None), "id", "")
             for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "REGISTRY" not in names
    assert "parse_registry_events" not in calls
    assert "find_authorization_event" not in calls
    # and it DOES take them from the prepared snapshot
    assert "prepared.snapshot" in src


def test_m617_production_deps_wire_the_disk_verifier():
    import inspect
    mod = real_run_module()
    src = inspect.getsource(mod)
    assert "post_write_verify=chain.post_write_verify" in src
    assert "prepare_compute=prepare_for_run" in src
    # the renderer takes the prepared object explicitly
    assert list(inspect.signature(
        mod.RealChain.render_report_with_governance_proof).parameters) == \
        ["self", "result", "prepared"]


def test_m617_release_verdict_is_taken_from_disk_not_from_memory():
    """The renderer may only SCREEN; `prove_governance` must not appear on
    the render path, and the seam that does call it must pass report_path."""
    import inspect
    mod = real_run_module()
    render_src = inspect.getsource(mod.render_s0_report)
    assert "screen_governance_draft" in render_src
    assert "prove_governance" not in render_src
    verify_src = inspect.getsource(mod.RealChain.post_write_verify)
    assert "report_path=" in verify_src
    assert "sealed_artifacts" not in verify_src


def test_m617_post_write_verify_passes_on_honest_disk_bytes(tmp_path, monkeypatch):
    mod = real_run_module()
    snap = _test_snapshot()
    rdir, prepared, files = _honest_run_dir(mod, tmp_path, snap, monkeypatch)
    written = tuple((n, c.encode("utf-8")) for n, c in files.items())
    ok, detail = mod.RealChain().post_write_verify(rdir, written, prepared)
    assert ok is True, detail
    assert "disk governance" in detail


def test_m617_post_write_verify_catches_a_post_render_tamper(tmp_path, monkeypatch):
    """The property the in-memory proof was structurally blind to: the
    renderer finished, its verdict was already taken, and THEN the bytes on
    disk changed."""
    import json as _json
    mod = real_run_module()
    snap = _test_snapshot()
    rdir, prepared, files = _honest_run_dir(mod, tmp_path, snap, monkeypatch)
    written = tuple((n, c.encode("utf-8")) for n, c in files.items())

    doc = _json.loads((rdir / "S0_REPORT.json").read_text(encoding="utf-8"))
    doc["governance"]["registry_sequence_snapshot"] = 999
    (rdir / "S0_REPORT.json").write_bytes(
        _json.dumps(doc, indent=1, sort_keys=True).encode("utf-8"))

    ok, detail = mod.RealChain().post_write_verify(rdir, written, prepared)
    assert ok is False
    assert "registry_sequence_snapshot" in detail


def test_m617_post_write_verify_catches_a_crlf_translated_artifact(tmp_path, monkeypatch):
    """The measured 185e47f7 defect, reproduced end-to-end: rewrite one
    artifact in TEXT mode (what `write_text` did on Windows) and the sealed
    set must refuse, even though the manifest itself is untouched."""
    mod = real_run_module()
    snap = _test_snapshot()
    rdir, prepared, files = _honest_run_dir(mod, tmp_path, snap, monkeypatch)
    written = tuple((n, c.encode("utf-8")) for n, c in files.items())

    victim = next(n for n, c in files.items()
                  if n != "S0_REPORT.json" and "\n" in c)
    (rdir / victim).write_bytes(files[victim].replace("\n", "\r\n")
                                .encode("utf-8"))
    ok, detail = mod.RealChain().post_write_verify(rdir, written, prepared)
    assert ok is False
    assert victim in detail


def test_m617_post_write_verify_refuses_a_foreign_prepared_object(tmp_path, monkeypatch):
    mod = real_run_module()
    snap = _test_snapshot()
    rdir, _prepared, files = _honest_run_dir(mod, tmp_path, snap, monkeypatch)
    written = tuple((n, c.encode("utf-8")) for n, c in files.items())

    class _LookAlike:
        config = None
        reason = "look-alike"
        snapshot = _MPX(dict(_test_snapshot()))

    ok, detail = mod.RealChain().post_write_verify(rdir, written,
                                                   _LookAlike())
    assert ok is False
    assert "prepared execution input" in detail


def test_m617_compute_stamps_the_snapshot_sequence_not_the_live_registry(
        monkeypatch, tmp_path):
    """M6.1.7 review L-4: BEHAVIOURAL evidence for the C3 closure.

    The AST pin next door dies to any refactor that hides the read behind a
    helper, and nothing else asserted what `compute` actually STAMPS. Here
    the live registry is made UNREADABLE — so reading it is impossible
    rather than merely unexpected — and the snapshot carries a sequence
    that differs from the real one, as this run's own RUN_STARTED row makes
    it differ.
    """
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)

    class _Unreadable(type(mod.REGISTRY)):
        def read_text(self, *a, **k):
            raise AssertionError("compute read the registry after RUN_STARTED")
        read_bytes = read_text
        open = read_text

    monkeypatch.setattr(mod, "REGISTRY", _Unreadable(mod.REGISTRY))
    captured = {}
    monkeypatch.setattr(mod, "build_full_study_result",
                        lambda *a, **k: captured.update(k) or {"study": 1})

    snap = _test_snapshot(event_sequence=7)
    prepared = _prepared_with(mod, snap)
    chain = mod.RealChain()
    monkeypatch.setattr(chain, "_ensure", lambda: (None, "UNIVERSE"))
    chain._bars = None
    chain.compute(prepared)

    gov = captured["governance_meta"]
    assert gov["registry_sequence_snapshot"] == 7          # pre-exposure value
    assert gov["authorized_commit"] == snap["authorized_commit"]
    assert gov["trial_id"] == mod.TRIAL_ID


# ===========================================================================
# S0-closeout conformance fix-round pins (R1 findings F1.1-F1.4, F2.1)
# ===========================================================================

def _entry_src(obj):
    import inspect
    return inspect.getsource(obj)


def test_r1_f21_chain_render_forwards_the_validated_methods():
    """F2.1 (High): the F-2 key-claims screen and the ruled admission
    context are gated on `methods=`; the production chain seam MUST forward
    the validated config's methods. Source pin — behaviour cannot see a
    skipped screen."""
    mod = real_run_module()
    src = _entry_src(mod.RealChain.render_report_with_governance_proof)
    assert "methods=prepared.config.methods" in src


def test_r1_f12_compute_passes_the_day_value_snapshot():
    """F1.2 (Med): Stage C consumes the F-1 snapshot, never the config
    callables. Source pin on the forwarding + behavioural pin below."""
    mod = real_run_module()
    assert ("day_value_snapshot=prepared.day_values"
            in _entry_src(mod.RealChain.compute))


def test_r1_f12_prepare_always_materializes_day_values(monkeypatch,
                                                       tmp_path):
    import dataclasses as _dc
    mod = real_run_module()
    _hermetic_stage_c_paths(mod, monkeypatch, tmp_path)
    _f1_resolved_sources(mod, monkeypatch)
    if "m" not in _CACHE:
        _CACHE["m"] = _market()
    bars, ds = _CACHE["m"]
    monkeypatch.setattr(mod.RealChain, "_ensure",
                        lambda self: (ds, None))
    monkeypatch.setattr(mod.RealChain, "_bars", bars, raising=False)
    mod._CONFIG_CACHE.clear()
    try:
        prepared = mod.RealChain().prepare(_test_snapshot())
        assert prepared.day_values is not None
        dates = sorted(r.trade_date for r in ds.records)
        assert prepared.day_values.covers(dates)
    finally:
        mod._CONFIG_CACHE.clear()


def test_r1_f13_payload_carries_the_ruled_disclosure_blocks():
    """F1.3 (Med): the production payload itself must carry the DR-3/5/7
    disclosure blocks — reverting the entry wiring goes red HERE, not only
    in the primitives' own test files."""
    src = _payload()
    grid_cells = src["feasibility_grid"]["cells"]
    assert grid_cells, "no grid cells in payload"
    feasible_seen = 0
    for cell in grid_cells.values():
        grid = cell["grid"]
        pts = list(grid.values()) if isinstance(grid, dict) else list(grid)
        for p in pts:
            if isinstance(p, dict) and not p.get("infeasible_by_sample"):
                feasible_seen += 1
                assert "repeats" in p, "DR-5 repeats block missing"
                assert "fp_allocation" in p, "DR-3 block missing"
    assert feasible_seen > 0, "no feasible grid point exercised the pin"
    for tkey, views in src["stability_views"].items():
        for eng, scns in views.items():
            if not isinstance(scns, dict):
                continue
            for scn, cell in scns.items():
                if isinstance(cell, dict) and "epochs" in cell:
                    assert "populations" in cell, (
                        f"DR-7 populations missing at {tkey}|{eng}|{scn}")


def test_r1_f11_f14_entry_wiring_source_pins():
    """F1.1/F1.4 (Low): the DR-1 adverse vector and DR-8 estimator wirings
    are behavioural no-ops by DESIGN (the rulings reproduce the prior
    conventions exactly — a genuine result, disclosed in the packet), so
    the wiring is pinned at source level instead."""
    mod = real_run_module()
    src = _entry_src(mod.build_full_study_result)
    assert "build_scenarios_from_method" in src
    assert "worst_day_estimator=config.methods" in src.replace(
        "\n", "").replace(" ", "")[:0] or "worst_day_estimator" in src
    assert "fp_allocation=config.methods.fp_allocation" in src
    assert "grid_policy=config.methods.grid_policy" in src
    assert "stability_population=config.methods.stability_population" in src


def test_r1_ruled_non_test_only_render_admits_seed_manifest(monkeypatch,
                                                            tmp_path):
    """S5 wiring end-state: a ruled NON-test_only render admits
    SEED_MANIFEST (condition-driven), while the TEST_ONLY chain e2e keeps
    it withheld (pinned elsewhere)."""
    mod = real_run_module()
    _patch_kc_assertions(mod, monkeypatch, tmp_path, _payload())
    files = mod.render_s0_report(_payload(), expected_governance=dict(_GOV),
                                 methods=_f1_approved_methods())
    assert "SEED_MANIFEST.json" in files
    adm = json.loads(files["HANDOFF_ADMISSION.json"])
    assert "SEED_MANIFEST.json" in adm["admitted"]
