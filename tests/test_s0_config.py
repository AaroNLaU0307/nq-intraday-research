"""M6.1.4 lane S3 - dedicated S0 CONFIG-CONTRACT tests.

Scope: the `itsf.contracts` config surface ONLY - the injectable schema
gate, deep immutability of the resolved-method tree, canonical form of the
spread-scalar triple, and the structural (never semantic) gates on the
DR-M6-D / DR-M6-H fields.

NOTHING here approves, ranks or narrows an unruled research choice. Every
assertion is about TYPE, STRUCTURE, IMMUTABILITY or CANONICAL FORM. The
`TEST_ONLY` values below are synthetic stand-ins, never adopted rulings; the
value semantics of DR-1/DR-2/DR-4/DR-8 remain open.

Companion file: tests/test_m6_chain.py (main-agent owned, not touched here).
"""
from __future__ import annotations

import dataclasses as dc
import inspect
import json
import math
import re
from types import MappingProxyType

import numpy as np
import pytest

from itsf import contracts as C

_NAN = float("nan")
_INF = float("inf")


# --- synthetic TEST_ONLY builders -------------------------------------------

def _regime(date: str) -> str:                 # stable module-level identity
    return "TEST_ONLY_R"


def _regime_other(date: str) -> str:
    return "TEST_ONLY_R"                       # same behaviour, other object


def _vol(date: str) -> str:
    return "TEST_ONLY_T1"


def _spread_cost(**over):
    kw = dict(scalar_rule="TEST_ONLY",
              adverse_slippage_ticks={"Base": 1.0, "Conservative": 2.0},
              adverse_semantics="replaces_per_side")
    kw.update(over)
    return C.SpreadCostMethod(**kw)


def _bootstrap(**over):
    kw = dict(population="TEST_ONLY", na_day_rule="TEST_ONLY",
              statistic="mean", n_boot_per_seed=True,
              quoted_seed_rule="first_seed",
              percentile_interpolation="linear", crn_scope="TEST_ONLY")
    kw.update(over)
    return C.BootstrapMethod(**kw)


def _methods(**over):
    """A fully-populated TEST_ONLY ResolvedS0Methods (no ruling adopted)."""
    base = C.ResolvedS0Methods(
        spread_cost=_spread_cost(),
        volatility_regime=C.VolatilityRegimeMethod(
            close_source="TEST_ONLY", return_basis="simple", ddof=1,
            roll_crossing_rule="TEST_ONLY", tercile_reference="TEST_ONLY",
            na_rule="vol_na"),
        fp_allocation=C.FpAllocationMethod(
            basis="A", weight_source="self_pool",
            shortfall_rule="proportional"),
        bootstrap_method=_bootstrap(),
        grid_policy=C.GridRepeatPolicy(
            k_per_seed=1, k_start_index=0, stream_includes_theta=False,
            convergence_rule="TEST_ONLY", max_doublings=0),
        event_na_mapping="five_stratum",
        stability_population="TEST_ONLY",
        worst_day_estimator="TEST_ONLY",
        test_only=True)
    return dc.replace(base, **over) if over else base


def _config(scalars=(0.5, 0.75, 0.75), methods=None,
            regime_of=None, vol_axis_of=None):
    return C.derive_study_config(
        methods if methods is not None else _methods(),
        spread_scalars=scalars,
        regime_of=regime_of if regime_of is not None else _regime,
        vol_axis_of=vol_axis_of if vol_axis_of is not None else _vol)


def _good_inj():
    return {"spread_scalars": (0.5, 0.75, 0.75),
            "regime_of": _regime, "vol_axis_of": _vol}


# --- pathological inputs shared by the never-raises suites -------------------

class _RaisingGetattr:
    """Raises on any NON-dunder attribute read. The dunder exemption exists
    only so pytest's own collection/id machinery can introspect the object;
    every attribute a validation gate would plausibly read (`keys`,
    `spread_scalars`, `items`, ...) still detonates. The unconditional
    variant is exercised in `test_totally_hostile_object_is_refused`."""

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        raise RuntimeError("attacker __getattr__ ran inside the gate")


class _RaisingEq:
    def __eq__(self, other):
        raise RuntimeError("attacker __eq__ ran inside the gate")

    def __ne__(self, other):
        raise RuntimeError("attacker __ne__ ran inside the gate")

    def __hash__(self):
        return 7


class _KeysBomb(dict):
    def keys(self):
        raise RuntimeError("attacker keys() ran inside the gate")


class _GetItemBomb(dict):
    def __getitem__(self, key):
        raise RuntimeError("attacker __getitem__ ran inside the gate")


class _LenBomb(tuple):
    def __len__(self):
        raise RuntimeError("attacker __len__ ran inside the gate")


def _call_bomb(date):
    raise RuntimeError("the gate CALLED an injectable callable")


_PATHOLOGICAL = [
    None, True, False, 0, 1, -1, 1.5, _NAN, _INF, -_INF,
    "", "spread_scalars", b"spread_scalars", [], (), {1, 2},
    [("spread_scalars", (0.5, 0.75, 0.75))],
    object(), _RaisingGetattr(), _RaisingEq(), type, len,
    _KeysBomb({"spread_scalars": (0.5, 0.75, 0.75)}),
    _GetItemBomb(_good_inj()),
    {_RaisingEq(): 1},
    {"spread_scalars": _RaisingEq(), "regime_of": _RaisingEq(),
     "vol_axis_of": _RaisingEq()},
    {"spread_scalars": _LenBomb((0.5, 0.75, 0.75)),
     "regime_of": _regime, "vol_axis_of": _vol},
]


# === 1. validate_injectables - EXACT-KEY schema =============================

def test_injectable_keys_are_exactly_derive_study_config_keywords():
    """The gate's key set is not a hand-copied list: it must equal the
    keyword-only parameters of the ONLY StudyConfig constructor."""
    sig = inspect.signature(C.derive_study_config)
    kwonly = {n for n, p in sig.parameters.items()
              if p.kind is inspect.Parameter.KEYWORD_ONLY}
    assert kwonly == set(C.INJECTABLE_KEYS)
    assert C.INJECTABLE_KEYS == frozenset(
        {"spread_scalars", "regime_of", "vol_axis_of"})


def test_valid_injectables_produce_no_problems():
    assert C.validate_injectables(_good_inj()) == []


def test_valid_injectables_accept_any_mapping_not_just_dict():
    assert C.validate_injectables(MappingProxyType(_good_inj())) == []


def test_problem_list_is_a_sorted_deduplicated_list_of_str():
    out = C.validate_injectables({"regime_of": 1, "vol_axis_of": 2, "z": 3})
    assert isinstance(out, list)
    assert all(isinstance(p, str) for p in out)
    assert all(p.startswith("injectables.") for p in out)
    assert out == sorted(set(out))


def test_validation_is_deterministic_across_repeated_calls():
    payload = {"vol_axis_of": 1, "regime_of": 2, "zz": 3, "aa": 4}
    runs = [C.validate_injectables(dict(payload)) for _ in range(20)]
    assert all(r == runs[0] for r in runs)


@pytest.mark.parametrize("missing", sorted(
    {"spread_scalars", "regime_of", "vol_axis_of"}))
def test_missing_key_is_reported(missing):
    inj = _good_inj()
    del inj[missing]
    out = C.validate_injectables(inj)
    assert f"injectables.missing_key:{missing}" in out


def test_extra_key_is_reported_exact_key_schema_not_minimal():
    inj = _good_inj()
    inj["n_boot"] = 10_000
    out = C.validate_injectables(inj)
    assert out == ["injectables.extra_key:n_boot"]


def test_non_str_extra_key_is_reported_without_raising():
    out = C.validate_injectables({7: 1, **_good_inj()})
    assert "injectables.extra_key:7" in out


def test_empty_dict_reports_empty_and_all_three_missing_keys():
    out = C.validate_injectables({})
    assert "injectables.empty" in out
    for k in ("spread_scalars", "regime_of", "vol_axis_of"):
        assert f"injectables.missing_key:{k}" in out


@pytest.mark.parametrize(
    "bad", [None, True, False, 0, 1.5, "", "abc", b"abc", [], (),
            (("spread_scalars", (0.5, 0.75, 0.75)),), {1, 2}, object(),
            _RaisingGetattr(), len])
def test_non_mapping_is_refused_without_touching_it(bad):
    assert C.validate_injectables(bad) == ["injectables.not_a_mapping"]


def test_mapping_whose_keys_raises_fails_closed():
    out = C.validate_injectables(
        _KeysBomb({"spread_scalars": (0.5, 0.75, 0.75)}))
    assert out == ["injectables.keys_unreadable"]


def test_mapping_whose_getitem_raises_fails_closed():
    out = C.validate_injectables(_GetItemBomb(_good_inj()))
    for k in ("spread_scalars", "regime_of", "vol_axis_of"):
        assert f"injectables.unreadable:{k}" in out


@pytest.mark.parametrize("name", ["regime_of", "vol_axis_of"])
@pytest.mark.parametrize("bad", [None, 1, "f", (), [], {}, True,
                                 _RaisingEq()])
def test_non_callable_mapping_is_refused(name, bad):
    inj = _good_inj()
    inj[name] = bad
    assert f"injectables.{name}_not_callable" in C.validate_injectables(inj)


def test_the_gate_never_calls_the_injectable_callables():
    """N3 defect class: a validation gate must not execute attacker code.
    Call-time failure is the compute path's try/except concern."""
    inj = {"spread_scalars": (0.5, 0.75, 0.75),
           "regime_of": _call_bomb, "vol_axis_of": _call_bomb}
    assert C.validate_injectables(inj) == []      # would raise if called


def test_totally_hostile_object_is_refused():
    """No dunder exemption at all: every attribute read raises, including
    the ones Python itself consults. The gate must still fail closed."""

    class _TotalBomb:
        def __getattr__(self, name):
            raise RuntimeError("attacker __getattr__ ran inside the gate")

    assert C.validate_injectables(_TotalBomb()) == [
        "injectables.not_a_mapping"]


def test_a_hostile_mapping_subclass_cannot_escape_the_gate():
    """Registered as a Mapping, but every access path is armed."""

    class _HostileMapping(dict):
        def __getattr__(self, name):
            raise RuntimeError("attacker __getattr__ ran inside the gate")

        def __getitem__(self, key):
            raise RuntimeError("attacker __getitem__ ran inside the gate")

    out = C.validate_injectables(_HostileMapping(_good_inj()))
    assert out and all(p.startswith("injectables.") for p in out)


@pytest.mark.parametrize("bad", _PATHOLOGICAL)
def test_validate_injectables_never_raises(bad):
    out = C.validate_injectables(bad)
    assert isinstance(out, list)
    assert all(isinstance(p, str) for p in out)


@pytest.mark.parametrize("bad", _PATHOLOGICAL)
def test_pathological_values_still_yield_a_nonempty_problem_list(bad):
    """A hostile payload must FAIL CLOSED - never silently validate."""
    assert C.validate_injectables(bad)


def test_len_bomb_on_spread_scalars_is_reported_not_raised():
    out = C.validate_injectables(
        {"spread_scalars": _LenBomb((0.5, 0.75, 0.75)),
         "regime_of": _regime, "vol_axis_of": _vol})
    assert out == ["injectables.spread_scalars_wrong_length:-1"]


# === 2. spread-scalar triple - exhaustive parametrization ===================

_LEGAL_TRIPLES = [
    (0.0, 0.0, 0.0),                    # zero triple, legal by ordering
    (1.0, 1.0, 1.0),                    # m == p90 == p95
    (0.5, 0.75, 0.75),                  # p90 == p95 boundary
    (0.5, 0.5, 0.75),                   # m == p90 boundary
    (0.5, 0.75, 1.25),                  # strictly increasing
    (0, 1, 2),                          # ints, canonicalized to floats
    (0.0, 1e-12, 1e-12),                # tiny but ordered
    (-0.0, 0.0, 0.0),                   # LOW-2: negative zero, normalized
    (-0.0, -0.0, 0.75),
]

_ILLEGAL_TRIPLES = [
    # --- non-finite, each position
    (_NAN, 1.0, 2.0), (1.0, _NAN, 2.0), (1.0, 2.0, _NAN),
    (_INF, 1.0, 2.0), (1.0, _INF, 2.0), (1.0, 2.0, _INF),
    (-_INF, 1.0, 2.0), (1.0, -_INF, 2.0), (1.0, 2.0, -_INF),
    # --- negative, each position
    (-1.0, 1.0, 2.0), (0.5, -1.0, 2.0), (0.5, 0.75, -1.0),
    # --- bool, each position (True is an int; must NOT become 1.0)
    (True, 1.0, 2.0), (0.5, True, 2.0), (0.5, 0.75, True),
    (False, 1.0, 2.0), (0.5, False, 2.0), (0.5, 0.75, False),
    # --- wrong length
    (), (1.0,), (1.0, 2.0), (1.0, 2.0, 3.0, 4.0),
    # --- ordering violations
    (2.0, 1.0, 3.0),                    # median > P90
    (1.0, 3.0, 2.0),                    # P90 > P95
    (3.0, 2.0, 1.0),                    # both
    # --- non-numeric members
    ("0.5", 0.75, 1.0), (None, 0.75, 1.0), (0.5, (), 1.0),
    (0.5, 0.75, np.bool_(True)),
]


@pytest.mark.parametrize("triple", _LEGAL_TRIPLES)
def test_legal_triples_are_accepted_and_canonicalized(triple):
    canon = C.canonical_spread_scalars(triple)
    assert canon is not None
    assert isinstance(canon, tuple) and len(canon) == 3
    assert all(type(v) is float for v in canon)
    cfg = _config(scalars=triple)
    assert cfg.spread_scalars == canon
    assert all(type(v) is float for v in cfg.spread_scalars)


@pytest.mark.parametrize("triple", _ILLEGAL_TRIPLES)
def test_illegal_triples_are_refused_by_every_entry_point(triple):
    assert C.canonical_spread_scalars(triple) is None
    with pytest.raises(ValueError, match="spread_scalars"):
        _config(scalars=triple)
    with pytest.raises(ValueError, match="spread_scalars"):
        C.StudyConfig(methods=_methods(), spread_scalars=triple,
                      regime_of=_regime, vol_axis_of=_vol)
    inj = _good_inj()
    inj["spread_scalars"] = triple
    problems = C.validate_injectables(inj)
    assert any(p.startswith("injectables.spread_scalars") for p in problems), \
        (triple, problems)


@pytest.mark.parametrize("bad", [[0.5, 0.75, 1.0], "abc", None, 1.0,
                                 {"m": 0.5}, (v for v in (0.5, 0.75, 1.0))])
def test_non_tuple_spread_scalars_is_refused_by_canonicalizer(bad):
    assert C.canonical_spread_scalars(bad) is None


def test_injectable_spread_scalars_must_be_a_tuple_not_a_list():
    """The injectable gate is stricter than derive_study_config on purpose:
    the approved source must hand out the CANONICAL container so equality
    against a fresh derivation is a canonical-form comparison."""
    inj = _good_inj()
    inj["spread_scalars"] = [0.5, 0.75, 0.75]
    assert ("injectables.spread_scalars_not_a_tuple"
            in C.validate_injectables(inj))


@pytest.mark.parametrize("n,triple", [(0, ()), (1, (1.0,)), (2, (1.0, 2.0)),
                                      (4, (1.0, 2.0, 3.0, 4.0))])
def test_wrong_length_reports_the_length(n, triple):
    inj = _good_inj()
    inj["spread_scalars"] = triple
    assert (f"injectables.spread_scalars_wrong_length:{n}"
            in C.validate_injectables(inj))


@pytest.mark.parametrize("triple,idx", [
    ((_NAN, 1.0, 2.0), 0), ((1.0, _NAN, 2.0), 1), ((1.0, 2.0, _NAN), 2),
    ((True, 1.0, 2.0), 0), ((0.5, True, 2.0), 1), ((0.5, 0.75, True), 2),
    ((-1.0, 1.0, 2.0), 0), ((0.5, -1.0, 2.0), 1), ((0.5, 0.75, -1.0), 2),
])
def test_bad_member_reports_its_index(triple, idx):
    inj = _good_inj()
    inj["spread_scalars"] = triple
    assert (f"injectables.spread_scalars_value_invalid:{idx}"
            in C.validate_injectables(inj))


@pytest.mark.parametrize("triple", [(2.0, 1.0, 3.0), (1.0, 3.0, 2.0),
                                    (3.0, 2.0, 1.0)])
def test_ordering_violation_has_its_own_problem_code(triple):
    inj = _good_inj()
    inj["spread_scalars"] = triple
    assert ("injectables.spread_scalars_not_ordered_median_le_p90_le_p95"
            in C.validate_injectables(inj))


# --- numpy: CANONICALIZED (documented decision), np.bool_ REFUSED ----------

@pytest.mark.parametrize("triple", [
    (np.float64(0.5), np.float64(0.75), np.float64(0.75)),
    (np.float32(0.5), np.float32(0.75), np.float32(0.75)),
    (np.int64(0), np.int64(1), np.int64(2)),
    (np.float64(0.5), 0.75, np.int32(1)),
])
def test_numpy_scalars_are_canonicalized_not_refused(triple):
    cfg = _config(scalars=triple)
    assert all(type(v) is float for v in cfg.spread_scalars)
    assert C.validate_injectables(
        {**_good_inj(), "spread_scalars": triple}) == []


def test_numpy_triple_equals_the_plain_float_triple():
    a = _config(scalars=(np.float64(0.5), np.float32(0.75), np.int64(1)))
    b = _config(scalars=(0.5, 0.75, 1.0))
    assert a.spread_scalars == b.spread_scalars
    assert a == b


# --- LOW-2 (Phase-E blind audit #2): negative zero collapses to +0.0 -------
#
# `-0.0` is finite, passes `>= 0.0`, and `-0.0 == 0.0` is True, so it slips
# through every equality-based gate — but it serializes as a DIFFERENT JSON
# token in `disclosures.method_conventions.spread_scalars_used`. Canonical
# equality and sealed-byte identity must not disagree.

_NEG_ZERO_TRIPLES = [
    (-0.0, 0.75, 0.75),
    (0.0, -0.0, 0.75),
    (-0.0, -0.0, -0.0),
    (-0.0, -0.0, 0.75),
    (np.float64(-0.0), 0.75, 0.75),
    (np.float32(-0.0), np.float32(0.75), np.float32(0.75)),
    (-0.0, np.float64(-0.0), np.float32(0.75)),
]


@pytest.mark.parametrize("triple", _NEG_ZERO_TRIPLES)
def test_negative_zero_is_collapsed_to_positive_zero(triple):
    canon = C.canonical_spread_scalars(triple)
    assert canon is not None
    for i, v in enumerate(canon):
        assert type(v) is float
        if v == 0.0:
            assert math.copysign(1.0, v) == 1.0, (i, repr(v))
    cfg = _config(scalars=triple)
    for v in cfg.spread_scalars:
        if v == 0.0:
            assert math.copysign(1.0, v) == 1.0


@pytest.mark.parametrize("triple", _NEG_ZERO_TRIPLES)
def test_negative_zero_never_reaches_the_serialized_form(triple):
    """The actual defect: identical-by-== configs whose SEALED BYTES differ.
    `spread_scalars_used` is copied verbatim into the formal payload."""
    canon = C.canonical_spread_scalars(triple)
    assert "-0.0" not in repr(canon)
    assert "-0.0" not in json.dumps(list(canon), sort_keys=True,
                                    allow_nan=False)
    cfg = _config(scalars=triple)
    assert "-0.0" not in repr(cfg.spread_scalars)
    assert "-0.0" not in json.dumps(list(cfg.spread_scalars),
                                    sort_keys=True, allow_nan=False)


def test_negative_zero_config_equals_the_positive_zero_config():
    neg = _config(scalars=(-0.0, 0.75, 0.75))
    pos = _config(scalars=(0.0, 0.75, 0.75))
    assert neg == pos
    assert neg.spread_scalars == pos.spread_scalars
    # ... and now, unlike before the LOW-2 fix, byte-identically so.
    assert repr(neg.spread_scalars) == repr(pos.spread_scalars)
    assert (json.dumps(list(neg.spread_scalars))
            == json.dumps(list(pos.spread_scalars)))


def test_numpy_negative_zero_matches_the_python_float_case():
    a = _config(scalars=(np.float64(-0.0), np.float32(0.75), 0.75))
    b = _config(scalars=(0.0, 0.75, 0.75))
    assert a == b
    assert repr(a.spread_scalars) == repr(b.spread_scalars) == \
        repr((0.0, 0.75, 0.75))


@pytest.mark.parametrize("zero", [-0.0, np.float64(-0.0), np.float32(-0.0),
                                  0.0, 0, np.int64(0)])
def test_canonical_scalar_returns_positive_zero_for_every_zero(zero):
    out = C._canonical_scalar(zero)
    assert out == 0.0
    assert type(out) is float
    assert math.copysign(1.0, out) == 1.0
    assert repr(out) == "0.0"


def test_negative_zero_is_admissible_to_the_injectable_gate():
    """`-0.0` is a LEGAL scalar (it is zero), not a refusal — the fix is
    normalization, never rejection. The zero triple stays legal by ordering."""
    assert C.validate_injectables(
        {**_good_inj(), "spread_scalars": (-0.0, -0.0, -0.0)}) == []
    assert C.canonical_spread_scalars((-0.0, -0.0, -0.0)) == (0.0, 0.0, 0.0)


@pytest.mark.parametrize("bad", [np.bool_(True), np.bool_(False)])
def test_numpy_bool_is_refused_like_python_bool(bad):
    assert C._canonical_scalar(bad) is None
    with pytest.raises(ValueError, match="spread_scalars"):
        _config(scalars=(0.5, 0.75, bad))


# === 3. canonical form + equality ==========================================

def test_equal_inputs_produce_equal_configs():
    assert _config() == _config()


def test_int_and_float_triples_canonicalize_to_the_same_config():
    assert _config(scalars=(0, 1, 2)) == _config(scalars=(0.0, 1.0, 2.0))


def test_different_scalars_produce_unequal_configs():
    assert _config(scalars=(0.5, 0.75, 0.75)) != _config(
        scalars=(0.5, 0.75, 1.0))


def test_different_methods_produce_unequal_configs():
    other = _methods(stability_population="TEST_ONLY_OTHER")
    assert _config() != _config(methods=other)


def test_equivalent_but_distinct_callables_produce_unequal_configs():
    """Pins the M6.1.3 N4a/N4b behaviour from the contracts side: callables
    compare by IDENTITY, so a look-alike config can never satisfy the
    production derivation-equality gate."""
    assert _config() != _config(regime_of=_regime_other)


def test_canonical_config_is_idempotent():
    cfg = _config()
    once = C.canonical_config(cfg)
    assert once == cfg
    assert C.canonical_config(once) == once
    assert once.spread_scalars == cfg.spread_scalars


def test_canonical_config_repairs_a_bypass_built_config():
    """A config assembled by object.__new__/__setattr__ skips __post_init__
    (the route the defence-in-depth tests use). canonical_config re-runs the
    full validation and restores the canonical float triple."""
    cfg = object.__new__(C.StudyConfig)
    object.__setattr__(cfg, "methods", _methods())
    object.__setattr__(cfg, "spread_scalars", (np.float64(0.5), 1, 2))
    object.__setattr__(cfg, "regime_of", _regime)
    object.__setattr__(cfg, "vol_axis_of", _vol)
    assert not all(type(v) is float for v in cfg.spread_scalars)
    fixed = C.canonical_config(cfg)
    assert fixed.spread_scalars == (0.5, 1.0, 2.0)
    assert all(type(v) is float for v in fixed.spread_scalars)
    assert fixed == _config(scalars=(0.5, 1.0, 2.0))


def test_canonical_config_refuses_a_non_studyconfig():
    for bad in (None, 1, "cfg", object(), _methods()):
        with pytest.raises(TypeError):
            C.canonical_config(bad)


def test_canonical_config_fails_closed_on_an_invalid_bypass_config():
    cfg = object.__new__(C.StudyConfig)
    object.__setattr__(cfg, "methods", _methods())
    object.__setattr__(cfg, "spread_scalars", (2.0, 1.0, 0.0))
    object.__setattr__(cfg, "regime_of", _regime)
    object.__setattr__(cfg, "vol_axis_of", _vol)
    with pytest.raises(ValueError, match="spread_scalars"):
        C.canonical_config(cfg)


def test_post_init_still_enforces_every_pre_existing_invariant():
    """frozen + object.__setattr__ canonicalization must not have weakened
    any M6.1.1/M6.1.2/M6.1.3 refusal."""
    with pytest.raises(ValueError, match="pending method rulings"):
        C.StudyConfig(methods=C.ResolvedS0Methods(),
                      spread_scalars=(0.5, 0.75, 0.75),
                      regime_of=_regime, vol_axis_of=_vol)
    bad = _methods(grid_policy=C.GridRepeatPolicy(
        k_per_seed=0, k_start_index=0, stream_includes_theta=False,
        convergence_rule="X", max_doublings=0))
    with pytest.raises(ValueError, match="structurally invalid"):
        C.StudyConfig(methods=bad, spread_scalars=(0.5, 0.75, 0.75),
                      regime_of=_regime, vol_axis_of=_vol)
    for name in ("regime_of", "vol_axis_of"):
        kw = {"regime_of": _regime, "vol_axis_of": _vol}
        kw[name] = "not callable"
        with pytest.raises(ValueError, match="must be callable"):
            C.StudyConfig(methods=_methods(),
                          spread_scalars=(0.5, 0.75, 0.75), **kw)


# === 4. deep immutability ===================================================

_FROZEN_CLASSES = [
    C.SpreadCostMethod, C.VolatilityRegimeMethod, C.FpAllocationMethod,
    C.BootstrapMethod, C.GridRepeatPolicy, C.ResolvedS0Methods, C.StudyConfig,
]


@pytest.mark.parametrize("cls", _FROZEN_CLASSES)
def test_config_dataclasses_are_frozen(cls):
    assert cls.__dataclass_params__.frozen is True


def test_setattr_is_refused_on_the_whole_resolved_method_tree():
    cfg = _config()
    with pytest.raises(dc.FrozenInstanceError):
        cfg.spread_scalars = (1.0, 1.0, 1.0)
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods = _methods()
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods.worst_day_estimator = "linear"
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods.spread_cost.scalar_rule = "B-i"
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods.bootstrap_method.n_boot_per_seed = False
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods.grid_policy.k_per_seed = 99
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods.volatility_regime.ddof = 0
    with pytest.raises(dc.FrozenInstanceError):
        cfg.methods.fp_allocation.basis = "C"


def test_adverse_slippage_ticks_is_canonicalized_to_a_read_only_mapping():
    ticks = _config().methods.spread_cost.adverse_slippage_ticks
    assert isinstance(ticks, MappingProxyType)
    assert isinstance(ticks, C.Mapping)
    assert ticks["Base"] == 1.0                   # read access unchanged
    assert sorted(ticks) == ["Base", "Conservative"]
    assert len(ticks) == 2
    assert "Base" in ticks
    assert dict(ticks) == {"Base": 1.0, "Conservative": 2.0}


@pytest.mark.parametrize("mutate", [
    lambda m: m.__setitem__("Base", 99.0),
    lambda m: m.__delitem__("Base"),
    lambda m: m.clear(),
    lambda m: m.pop("Base"),
    lambda m: m.update({"Base": 99.0}),
    lambda m: m.setdefault("New", 1.0),
])
def test_adverse_slippage_ticks_cannot_be_mutated_in_place(mutate):
    """Mutate-after-validate was only caught by the NEXT revalidation; the
    canonical read-only form closes the window at the source."""
    ticks = _config().methods.spread_cost.adverse_slippage_ticks
    with pytest.raises((TypeError, AttributeError)):
        mutate(ticks)


def test_canonical_ticks_is_a_copy_not_a_live_view_of_the_caller_dict():
    src = {"Base": 1.0}
    method = _spread_cost(adverse_slippage_ticks=src)
    src["Base"] = 99.0
    src["Injected"] = 5.0
    assert dict(method.adverse_slippage_ticks) == {"Base": 1.0}


def test_canonicalized_ticks_preserve_equality_and_replace():
    a = _spread_cost(adverse_slippage_ticks={"Base": 1.0})
    b = _spread_cost(adverse_slippage_ticks=MappingProxyType({"Base": 1.0}))
    assert a == b
    assert a.adverse_slippage_ticks == {"Base": 1.0}      # proxy == dict
    replaced = dc.replace(a, scalar_rule="B-i")
    assert isinstance(replaced.adverse_slippage_ticks, MappingProxyType)
    assert replaced.adverse_slippage_ticks == a.adverse_slippage_ticks


@pytest.mark.parametrize("bad", [42, "ticks", None, [], (), object()])
def test_non_mapping_ticks_are_left_alone_for_structural_problems_to_report(
        bad):
    """The canonicalizer must NEVER raise inside a constructor - a bad value
    has to survive to structural_problems() so it is REPORTED, not thrown."""
    m = _spread_cost(adverse_slippage_ticks=bad)
    assert m.adverse_slippage_ticks is bad
    problems = _methods(spread_cost=m).structural_problems()
    assert any("adverse_slippage_ticks" in p for p in problems)
    with pytest.raises(ValueError, match="structurally invalid"):
        _config(methods=_methods(spread_cost=m))


def test_empty_ticks_mapping_is_still_refused_after_canonicalization():
    m = _spread_cost(adverse_slippage_ticks={})
    assert isinstance(m.adverse_slippage_ticks, MappingProxyType)
    assert ("spread_cost.adverse_slippage_ticks_not_a_nonempty_mapping"
            in _methods(spread_cost=m).structural_problems())


@pytest.mark.parametrize("bad_value", [_NAN, _INF, -_INF, -1.0, True, "1.0",
                                       None])
def test_bad_tick_values_are_still_reported_after_canonicalization(bad_value):
    m = _spread_cost(adverse_slippage_ticks={"Base": bad_value})
    problems = _methods(spread_cost=m).structural_problems()
    assert "spread_cost.adverse_slippage_ticks_value_invalid:Base" in problems


# === 5. BootstrapMethod.n_boot_per_seed - flag, never a count ==============

@pytest.mark.parametrize("flag", [True, False])
def test_unambiguous_alias_mirrors_the_field(flag):
    b = _bootstrap(n_boot_per_seed=flag)
    assert b.n_boot_applies_per_seed is flag
    assert b.n_boot_applies_per_seed is b.n_boot_per_seed


def test_the_alias_is_a_read_only_property():
    b = _bootstrap()
    assert isinstance(type(b).__dict__["n_boot_applies_per_seed"], property)
    with pytest.raises(AttributeError):
        b.n_boot_applies_per_seed = False


@pytest.mark.parametrize("count", [10_000, 1, 0, 30_000, 10_000.0,
                                   np.int64(10_000)])
def test_a_resample_count_can_never_reach_a_studyconfig(count):
    """The one misread the name invites: `n_boot_per_seed=10_000`. It gets a
    dedicated problem code on top of the generic bool refusal, and
    derive_study_config fails closed."""
    methods = _methods(bootstrap_method=_bootstrap(n_boot_per_seed=count))
    problems = methods.structural_problems()
    assert "bootstrap_method.n_boot_per_seed_not_an_int" not in problems
    assert "bootstrap_method.n_boot_per_seed_not_a_bool" in problems
    assert ("bootstrap_method.n_boot_per_seed_is_a_flag_not_a_resample_count"
            in problems)
    with pytest.raises(ValueError, match="structurally invalid"):
        _config(methods=methods)


@pytest.mark.parametrize("bad", ["yes", None, [], {}, (), object()])
def test_non_numeric_non_bool_flag_gets_only_the_generic_refusal(bad):
    methods = _methods(bootstrap_method=_bootstrap(n_boot_per_seed=bad))
    problems = methods.structural_problems()
    assert "bootstrap_method.n_boot_per_seed_not_a_bool" in problems
    assert ("bootstrap_method.n_boot_per_seed_is_a_flag_not_a_resample_count"
            not in problems)
    with pytest.raises(ValueError, match="structurally invalid"):
        _config(methods=methods)


def test_the_flag_semantics_are_documented_decisively():
    """M6.1.4 S3 item 5: the name is retained, so the docstring must be the
    decisive artifact. It must say FLAG, name the frozen 10,000 budget, and
    point at the field that actually carries the count."""
    doc = C.BootstrapMethod.__doc__ or ""
    assert "FLAG" in doc
    assert "NEVER A RESAMPLE COUNT" in doc
    assert "10,000" in doc
    assert "FROZEN_N_BOOT" in doc
    assert "DR-4.4" in doc


def test_the_flag_carries_no_adopted_ruling():
    """Both attributions stay structurally legal - DR-4.4 is NOT ruled here."""
    for flag in (True, False):
        methods = _methods(bootstrap_method=_bootstrap(n_boot_per_seed=flag))
        assert not [p for p in methods.structural_problems()
                    if "n_boot_per_seed" in p]
        assert _config(methods=methods).methods.bootstrap_method \
            .n_boot_applies_per_seed is flag


# === 6. worst_day_estimator - structure only, DR-M6-H untouched ============

@pytest.mark.parametrize("bad", ["", "   ", "\t\n", 42, {}, True, [], 0.0,
                                 object()])
def test_worst_day_estimator_is_structurally_refused(bad):
    methods = _methods(worst_day_estimator=bad)
    assert any("worst_day_estimator" in p
               for p in methods.structural_problems()), repr(bad)
    with pytest.raises(ValueError, match="structurally invalid"):
        _config(methods=methods)


def test_worst_day_estimator_none_is_pending_not_structurally_invalid():
    methods = _methods(worst_day_estimator=None)
    assert "worst_day_estimator" in methods.pending_fields()
    assert not [p for p in methods.structural_problems()
                if "worst_day_estimator" in p]
    with pytest.raises(ValueError, match="pending method rulings"):
        _config(methods=methods)


@pytest.mark.parametrize("value", ["TEST_ONLY", "linear", "lower", "higher",
                                   "midpoint", "nearest", "anything_at_all"])
def test_the_gate_is_structural_and_ranks_no_estimator(value):
    """DR-M6-H stays open: ANY non-empty str passes STRUCTURE. If this test
    ever fails because one name is privileged, an unruled research choice has
    been adopted in the contracts layer."""
    methods = _methods(worst_day_estimator=value)
    assert not [p for p in methods.structural_problems()
                if "worst_day_estimator" in p]
    assert _config(methods=methods).methods.worst_day_estimator == value


def test_test_only_passes_structure_without_approving_semantics():
    cfg = _config(methods=_methods(worst_day_estimator="TEST_ONLY"))
    assert cfg.methods.worst_day_estimator == "TEST_ONLY"
    assert cfg.methods.fully_resolved is True
    assert cfg.methods.test_only is True


# === 7. cross-cutting invariants ===========================================

def test_pending_field_count_and_membership_are_unchanged():
    pend = C.ResolvedS0Methods().pending_fields()
    assert len(pend) == 8
    assert "test_only" not in pend
    assert pend == tuple(sorted(pend))


def test_a_fully_resolved_config_reports_no_structural_problems():
    assert _methods().structural_problems() == []
    assert _methods().fully_resolved is True


# === 8. REPRESENTATION IDENTITY vs VALUE EQUIVALENCE (M6.1.4-R2 F-1) =======
# Two SEPARATE obligations, and the reason this round exists:
#
#   EQUIVALENCE  (binary)  "do these two objects carry the same VALUES?"
#                          -> `canonical_spread_scalars` / `==`
#   REPRESENTATION (unary) "is THIS object in the exact canonical form
#                          contracts specifies, on its own?"
#                          -> `is_canonical_spread_scalars`
#                             / `is_canonical_ticks`
#
# The first cannot imply the second, BY DESIGN: `_canonical_scalar` widens
# `int` to `float` precisely so `(0, 1, 1)` and `(0.0, 1.0, 1.0)` compare
# EQUAL, and collapses `-0.0` to `+0.0`. Anything that decides
# interchangeability on VALUES alone therefore cannot see the two
# representation properties that reach the SEALED BYTES.
#
# SCOPE OF THE CLAIM, stated once and never widened: canonical WHEREVER
# CONTRACTS SPECIFIES CANONICAL (exactly the two `__post_init__` rewrites
# below), exact-type-pinned everywhere else. There is no third rule.


class _FloatBomb:
    """Detonates on numeric coercion. A representation predicate must decide
    by TYPE and never invoke `__float__`/`__index__`."""

    def __float__(self):
        raise RuntimeError("attacker __float__ ran inside the predicate")

    def __index__(self):
        raise RuntimeError("attacker __index__ ran inside the predicate")


class _CountingDict(dict):
    """A dict SUBCLASS that counts every content read. Used to prove the
    ticks predicate is a container check, not a traversal."""

    reads = 0

    def __iter__(self):
        type(self).reads += 1
        return super().__iter__()

    def items(self):
        type(self).reads += 1
        return super().items()

    def keys(self):
        type(self).reads += 1
        return super().keys()


#: Non-canonical REPRESENTATIONS that are VALUE-EQUAL to a canonical triple.
#: Each is the exact shape a bypass-built cached config can carry.
_NON_CANONICAL_TRIPLES = [
    ((0, 1, 1), (0.0, 1.0, 1.0)),                   # int, not float
    ((0.0, 1, 1.0), (0.0, 1.0, 1.0)),               # one int member
    ((0.5, 0.75, 1), (0.5, 0.75, 1.0)),             # trailing int
    ((-0.0, 1.0, 1.0), (0.0, 1.0, 1.0)),            # negative zero
    ((0.0, -0.0, 1.0), (0.0, 0.0, 1.0)),            # negative zero, middle
    ((-0.0, -0.0, -0.0), (0.0, 0.0, 0.0)),          # all negative zeros
    ((np.float64(0.5), 0.75, 0.75), (0.5, 0.75, 0.75)),   # numpy scalar
    ((np.int64(0), 1.0, 1.0), (0.0, 1.0, 1.0)),           # numpy int
    (True, None),                                   # not a tuple at all
    ([0.0, 1.0, 1.0], None),                        # list container
    ((0.0, 1.0), None),                             # wrong length
    (_LenBomb((0.0, 1.0, 1.0)), None),              # tuple SUBCLASS
]


@pytest.mark.parametrize("triple", _LEGAL_TRIPLES)
def test_is_canonical_spread_scalars_accepts_exactly_canonicalizer_output(
        triple):
    """THE BINDING: the predicate accepts exactly what the canonicalizer
    produces. One rule, two readers — the predicate can never drift into a
    second, differently-worded canonical form."""
    canon = C.canonical_spread_scalars(triple)
    assert canon is not None
    assert C.is_canonical_spread_scalars(canon) is True
    # ... and every legitimately constructed config is already canonical.
    assert C.is_canonical_spread_scalars(_config(scalars=triple)
                                         .spread_scalars) is True


@pytest.mark.parametrize("bad,equal_to", _NON_CANONICAL_TRIPLES)
def test_is_canonical_spread_scalars_rejects_non_canonical_representations(
        bad, equal_to):
    """The exposure: every one of these is refused as a REPRESENTATION even
    when it is value-equal to the canonical triple."""
    assert C.is_canonical_spread_scalars(bad) is False
    if equal_to is not None:
        assert tuple(bad) == equal_to           # value-equal ...
        assert C.is_canonical_spread_scalars(equal_to) is True   # ... yet only
        #                                        one of the two is canonical


@pytest.mark.parametrize("triple", _ILLEGAL_TRIPLES)
def test_is_canonical_spread_scalars_refuses_every_illegal_triple(triple):
    """Finiteness / non-negativity / ordering / length are DELEGATED to
    `canonical_spread_scalars`; the predicate must agree with it on every
    triple the canonicalizer rejects."""
    assert C.canonical_spread_scalars(triple) is None
    assert C.is_canonical_spread_scalars(triple) is False


@pytest.mark.parametrize("bad", _PATHOLOGICAL + [
    (_FloatBomb(), 0.75, 0.75), (0.5, _FloatBomb(), 0.75),
    (0.5, 0.75, _FloatBomb()), (_RaisingEq(), 0.75, 0.75),
    (_RaisingGetattr(), 0.75, 0.75)])
def test_is_canonical_spread_scalars_never_raises_and_never_coerces(bad):
    """A predicate that raises is a gate that fails open. Type is pinned
    BEFORE anything else, so no `__float__` / `__index__` / `__eq__` of a
    user object can run."""
    assert C.is_canonical_spread_scalars(bad) is False


def test_is_canonical_spread_scalars_returns_a_plain_bool():
    for value in ((0.5, 0.75, 0.75), (0, 1, 1), None, object()):
        assert type(C.is_canonical_spread_scalars(value)) is bool


def test_is_canonical_ticks_is_true_exactly_for_the_canonical_container():
    """`_canonical_ticks` canonicalizes the CONTAINER (a read-only
    `MappingProxyType` over a shallow copy) and nothing else."""
    plain = {"Base": 1.0, "Conservative": 2.0}
    canon = C._canonical_ticks(plain)
    assert C.is_canonical_ticks(canon) is True
    assert C.is_canonical_ticks(plain) is False           # the M2 exposure
    assert C.is_canonical_ticks(_CountingDict(plain)) is False
    assert C.is_canonical_ticks(_spread_cost().adverse_slippage_ticks) is True
    for bad in (None, 1, "Base", (), [], object(), _RaisingGetattr(),
                _KeysBomb(plain), _GetItemBomb(plain)):
        assert C.is_canonical_ticks(bad) is False
    assert type(C.is_canonical_ticks(canon)) is bool


def test_is_canonical_ticks_accepts_exactly_canonicalizer_output():
    """THE BINDING (idempotence): whatever `_canonical_ticks` returns for a
    Mapping is canonical, and re-canonicalizing it is the identity."""
    for source in ({"Base": 1.0}, {"Base": 1, "Severe": 3.0}, {"A": 0.0},
                   MappingProxyType({"Base": 1.0})):
        canon = C._canonical_ticks(source)
        assert C.is_canonical_ticks(canon) is True
        assert C._canonical_ticks(canon) is canon


def test_is_canonical_ticks_never_reads_the_mapping_contents():
    """RESIDUAL SCOPE, stated exactly. The predicate is a CONTAINER check:
    it proves the object handed out exposes no mutation surface of its own
    (`proxy["Base"] = 9` raises TypeError). It does NOT traverse, and it
    cannot prove the WRAPPED mapping is immutable or is not a hostile dict
    subclass — a mappingproxy is a live view and CPython exposes no API to
    reach the object behind it. Mutation through a reference the wrapper's
    author retained is caught only by the gateway's revalidate-on-every-call
    invariant, ACROSS calls, never within one."""
    _CountingDict.reads = 0
    hostile = _CountingDict({"Base": 1.0})
    proxy = MappingProxyType(hostile)
    assert C.is_canonical_ticks(proxy) is True    # container IS canonical ...
    assert _CountingDict.reads == 0               # ... and was never read
    with pytest.raises(TypeError):
        proxy["Base"] = 9.0                       # no mutation surface
    hostile["Base"] = 9.0                         # but the view is LIVE
    assert proxy["Base"] == 9.0                   # <- the stated residual
    _CountingDict.reads = 0


def test_value_equality_does_not_imply_canonical_representation():
    """THE DEFECT, stated at its source. Two configs that are `==` and whose
    normalized values are identical can carry DIFFERENT representations, and
    the difference reaches the sealed bytes."""
    canonical = _config(scalars=(0.0, 1.0, 1.0))
    bypass = object.__new__(C.StudyConfig)
    object.__setattr__(bypass, "methods", _methods())
    object.__setattr__(bypass, "spread_scalars", (0, 1, 1))
    object.__setattr__(bypass, "regime_of", _regime)
    object.__setattr__(bypass, "vol_axis_of", _vol)

    assert bypass == canonical                              # value-EQUAL
    assert bypass.spread_scalars == canonical.spread_scalars
    assert C.canonical_spread_scalars(bypass.spread_scalars) == \
        canonical.spread_scalars
    # ... and yet NOT representation-identical, byte-visibly so:
    assert C.is_canonical_spread_scalars(canonical.spread_scalars) is True
    assert C.is_canonical_spread_scalars(bypass.spread_scalars) is False
    assert (json.dumps(list(bypass.spread_scalars))
            != json.dumps(list(canonical.spread_scalars)))


def test_negative_zero_value_equality_also_hides_a_byte_difference():
    """The `-0.0` half of the same defect (the LOW-2 property, restated as a
    representation obligation rather than a canonicalizer post-condition)."""
    canonical = _config(scalars=(0.0, 1.0, 1.0))
    bypass = object.__new__(C.StudyConfig)
    object.__setattr__(bypass, "methods", _methods())
    object.__setattr__(bypass, "spread_scalars", (-0.0, 1.0, 1.0))
    object.__setattr__(bypass, "regime_of", _regime)
    object.__setattr__(bypass, "vol_axis_of", _vol)
    assert bypass.spread_scalars == canonical.spread_scalars   # -0.0 == 0.0
    assert C.is_canonical_spread_scalars(bypass.spread_scalars) is False
    assert "-0.0" in json.dumps(list(bypass.spread_scalars))
    assert "-0.0" not in json.dumps(list(canonical.spread_scalars))


def test_a_bypass_built_spread_cost_carries_a_mutable_mapping():
    """The M2 exposure at the contracts layer: skipping `__post_init__`
    leaves a MUTABLE mapping where the class docstring promises a read-only
    one — and `structural_problems()` cannot tell the difference, because a
    plain dict is a perfectly legal `Mapping` of legal values."""
    sc = object.__new__(C.SpreadCostMethod)
    object.__setattr__(sc, "scalar_rule", "TEST_ONLY")
    object.__setattr__(sc, "adverse_slippage_ticks",
                       {"Base": 1.0, "Conservative": 2.0})
    object.__setattr__(sc, "adverse_semantics", "replaces_per_side")
    methods = _methods(spread_cost=sc)
    assert methods.structural_problems() == []          # structurally legal
    assert methods == _methods()                        # and value-EQUAL
    assert C.is_canonical_ticks(sc.adverse_slippage_ticks) is False
    sc.adverse_slippage_ticks["Base"] = 999.0           # mutate-after-validate
    assert sc.adverse_slippage_ticks["Base"] == 999.0


def test_the_canonicalized_field_set_is_pinned():
    """ANTI-DRIFT PIN for the whole representation claim. `contracts` creates
    a canonical-representation obligation exactly where a `__post_init__`
    REWRITES a field. If a new one appears, this turns RED and the gateway's
    canonical-form tables (scripts/s0_real_run.py) must gain a row — the
    claim is 'canonical wherever contracts specifies canonical', and this is
    what keeps that set honest."""
    rewritten = set(re.findall(r'object\.__setattr__\(\s*self,\s*"(\w+)"',
                               inspect.getsource(C)))
    assert rewritten == {"spread_scalars", "adverse_slippage_ticks"}


@pytest.mark.parametrize("predicate,producer,legal", [
    ("is_canonical_spread_scalars", "canonical_spread_scalars",
     [(0.5, 0.75, 0.75), (0, 1, 2), (-0.0, 0.0, 0.0)]),
    ("is_canonical_ticks", "_canonical_ticks",
     [{"Base": 1.0}, {"Base": 1}, MappingProxyType({"Base": 2.0})]),
])
def test_canonical_predicates_agree_with_the_producers_they_bind_to(
        predicate, producer, legal):
    """One rule per canonicalized field, never two: for every legal input,
    the producer's OUTPUT satisfies the predicate."""
    pred = getattr(C, predicate)
    make = getattr(C, producer)
    for value in legal:
        assert pred(make(value)) is True
