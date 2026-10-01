"""The vol THRESHOLD population is not the supplement's OUTPUT population.

WHAT THE STRICT-BLIND MC-DS-S003 VERIFICATION PROVED. `build_vol20_regime_mapping`
computes the two tercile cut points ONCE over exactly the day sample it is
handed -- its own docstring calls that sample "the FULL Development sample day
set to label (every structurally eligible day)", and `tercile_reference` ruled
it. S0-T001 calls the wrapper with NO `days` argument, so it gets that eligible
population. The supplement producer used to pass `sorted(expected_day_set)`:
the SEALED OUTPUT set, which is narrower. A narrower sample moves the
quantiles, so days sitting near a cut got a different tercile than the run
being reconstructed had given them.

It was invisible to every existing check because the labels were internally
consistent either way -- conservation held, the vocabulary held, the day set
matched. Only replaying the sealed headline surface against both label sets
could see it.

THE REPAIR IS ONE ARGUMENT AND ONE PROJECTION: build the mapping the way S0
builds it, then read the sealed set's labels out of it. The output row
population is untouched.

The five dates the verifier named are NOT used here. They are regression
evidence about one frozen run; the property under test is the semantics.
"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf.mc import day_strata_rows as dsr          # noqa: E402
from itsf.s0 import dataset as s0                   # noqa: E402

SEALED = ("2024-01-02", "2024-01-03", "2024-01-04")
WIDER = SEALED + ("2024-01-05", "2024-01-08", "2024-01-09")


class _Vol:
    def __init__(self, label_of):
        self.label_of = dict(label_of)


def _derive(population_labels, *, sealed=SEALED, events=None):
    ev = {d: "none" for d in sealed} if events is None else events
    with mock.patch.multiple(
            s0,
            build_vol20_regime_mapping_from_universe=mock.Mock(
                return_value=_Vol(population_labels)),
            build_event_stratum_map=mock.Mock(
                return_value={"stratum_of": dict(ev)})):
        return dsr.derive_day_strata_rows(
            universe=object(), vol_method="ruled", flag_by_date={},
            event_na_mapping="ruled", expected_day_set=frozenset(sealed))


# ===========================================================================
# 1 — the two populations are allowed to differ
# ===========================================================================

def test_the_threshold_population_may_be_wider_than_the_output():
    """REGRESSION 1. Six labelled days, three sealed days, three rows."""
    labels = dict({d: "T1" for d in SEALED},
                  **{"2024-01-05": "T3", "2024-01-08": "T2",
                     "2024-01-09": "vol_na"})
    rows = _derive(labels)
    assert [r["trade_date"] for r in rows] == sorted(SEALED)
    assert len(rows) == len(SEALED) < len(labels)


def test_the_extra_population_days_change_no_emitted_label():
    """The projection reads each sealed day's OWN label. A wider population
    must not leak a neighbour's value in."""
    labels = {"2024-01-02": "T1", "2024-01-03": "T2", "2024-01-04": "T3",
              "2024-01-05": "vol_na", "2024-01-08": "T1"}
    rows = _derive(labels)
    assert {r["trade_date"]: r["vol_stratum"] for r in rows} == {
        "2024-01-02": "T1", "2024-01-03": "T2", "2024-01-04": "T3"}


def test_a_sealed_day_the_population_does_not_cover_still_refuses():
    """Coverage is the half that survived. Widening the population must not
    have cost the producer its ability to notice a day it cannot label."""
    labels = {d: "T1" for d in SEALED[:-1]}
    with pytest.raises(dsr.DayStrataRowsError) as ei:
        _derive(labels)
    assert ei.value.code == "vol_day_missing"


# ===========================================================================
# 2 — S0 and the supplement now use ONE population semantics
# ===========================================================================

def test_the_producer_calls_the_wrapper_the_way_s0_does():
    """REGRESSION 2, and the strongest form available without Development
    bars: the supplement must not pass a `days` argument at all, so the
    population is decided in ONE place -- the ruled wrapper's default --
    for both callers."""
    captured = {}

    def spy(universe, method, *args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = dict(kwargs)
        return _Vol({d: "T1" for d in SEALED})

    with mock.patch.multiple(
            s0,
            build_vol20_regime_mapping_from_universe=spy,
            build_event_stratum_map=mock.Mock(
                return_value={"stratum_of": {d: "none" for d in SEALED}})):
        dsr.derive_day_strata_rows(
            universe=object(), vol_method="ruled", flag_by_date={},
            event_na_mapping="ruled", expected_day_set=frozenset(SEALED))
    assert captured["args"] == (), captured
    assert "days" not in captured["kwargs"], captured


def test_the_wrappers_default_population_is_the_eligible_one():
    """The other half: what that default resolves to. Read off the ruled
    wrapper, so if the default ever stops being the eligible population this
    fails HERE rather than silently changing what the supplement means."""
    src = inspect.getsource(s0.build_vol20_regime_mapping_from_universe)
    assert "universe.funnel.structurally_eligible" in src
    assert "if days is None" in src


def test_s0_and_the_supplement_reach_the_same_default():
    """Executed, not read: with `days` omitted the wrapper labels the
    universe's eligible population, and the producer emits the sealed
    subset of exactly those labels."""
    eligible = tuple(WIDER)

    class _Funnel:
        structurally_eligible = eligible

    class _Uni:
        funnel = _Funnel()
        roll_transition_dates = ()

    seen = {}

    def fake_mapping(days, qualifying_closes, roll_transition_dates, method):
        seen["days"] = tuple(days)
        return _Vol({d: "T2" for d in days})

    with mock.patch.multiple(
            s0,
            build_vol20_regime_mapping=fake_mapping,
            qualifying_rth_closes=mock.Mock(return_value=()),
            build_event_stratum_map=mock.Mock(
                return_value={"stratum_of": {d: "none" for d in SEALED}})):
        rows = dsr.derive_day_strata_rows(
            universe=_Uni(), vol_method="ruled", flag_by_date={},
            event_na_mapping="ruled", expected_day_set=frozenset(SEALED))
    assert seen["days"] == tuple(sorted(eligible)), seen
    assert set(seen["days"]) > set(SEALED), "the population was not widened"
    assert [r["trade_date"] for r in rows] == sorted(SEALED)


# ===========================================================================
# 3-5 — output day set, event axis, year axis all unchanged
# ===========================================================================

def test_the_output_day_set_is_still_exactly_the_sealed_universe():
    """REGRESSION 3."""
    labels = dict({d: "T1" for d in SEALED}, **{d: "T3" for d in WIDER})
    rows = _derive(labels)
    assert frozenset(r["trade_date"] for r in rows) == frozenset(SEALED)


def test_the_event_axis_is_untouched():
    """REGRESSION 4. Both directions still refuse, and the labels still come
    straight out of the event mapping."""
    labels = {d: "T1" for d in WIDER}
    rows = _derive(labels, events={"2024-01-02": "CPI", "2024-01-03": "FOMC",
                                   "2024-01-04": "NA_multi_event"})
    assert [r["event_stratum"] for r in rows] == ["CPI", "FOMC",
                                                 "NA_multi_event"]
    for events, code in (
            ({d: "none" for d in SEALED[:-1]}, "event_day_missing"),
            (dict({d: "none" for d in SEALED},
                  **{"2024-01-05": "none"}), "event_day_invented")):
        with pytest.raises(dsr.DayStrataRowsError) as ei:
            _derive(labels, events=events)
        assert ei.value.code == code


def test_the_year_axis_is_untouched():
    """REGRESSION 5."""
    sealed = ("2019-12-31", "2020-01-02")
    rows = _derive({d: "T1" for d in sealed + ("2020-01-03",)},
                   sealed=sealed,
                   events={d: "none" for d in sealed})
    assert [r["year"] for r in rows] == [2019, 2020]


# ===========================================================================
# 6-7 — the earlier repairs are still in place
# ===========================================================================

def test_the_production_identity_repair_is_untouched():
    """REGRESSION 6."""
    from itsf.mc import day_strata_supplement as ds
    from itsf.mc import supplement_production as sp
    assert "sid = supplement_id or authority.supplement_id" in \
        inspect.getsource(sp.build_supplement_from_authority)
    assert inspect.getsource(sp).count(
        "production_supplement_id_divergence") == 2
    assert "expected_supplement_id" in inspect.signature(
        ds._validate_supplement_object).parameters


def test_the_archive_scope_and_pre_p3_repairs_are_untouched():
    """REGRESSION 7."""
    from itsf.mc import day_strata_pipeline as dsp
    from itsf.mc import supplement_chain as ch
    body = inspect.getsource(ch.run_supplement_chain)
    assert "archive_root=planned.archive_target)" in body
    assert "archive_root=planned.archive_parent" not in body
    assert "ARCHIVE_SEAM(out_dir, planned.archive_parent)" in body
    first = inspect.getsource(ch.run_supplement_gate_first)
    assert first.index("assert_current_run_namespaces_are_clear") < \
        first.index("append_run_started()")
    assert hasattr(dsp, "assert_current_run_namespaces_are_clear")


# ===========================================================================
# 8-9 — no evidence smuggled into production logic
# ===========================================================================

PRODUCTION = ("src/itsf/mc/day_strata_rows.py",
              "src/itsf/mc/day_strata_supplement.py",
              "src/itsf/mc/day_strata_classify.py",
              "src/itsf/mc/day_strata_pipeline.py",
              "src/itsf/mc/supplement_inputs.py",
              "src/itsf/s0/dataset.py")


def _executable_constants(rel):
    """String and number constants that are NOT docstrings. Prose that
    RECORDS a past defect is not an implementation of it -- a check that
    could not tell the difference would be reading the commentary, which is
    the mistake the provenance guards made in August."""
    tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef))
            and n.body and isinstance(n.body[0], ast.Expr)
            and isinstance(n.body[0].value, ast.Constant)
            and isinstance(n.body[0].value.value, str)}
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and id(n) not in docs:
            if isinstance(n.value, str) or isinstance(n.value, int):
                out.append(n.value)
    return out


FIVE = ("2012-11-26", "2012-11-27", "2013-05-06", "2014-10-20", "2015-12-10")


def test_no_production_module_names_the_five_mismatch_dates():
    """REGRESSION 8. They are regression EVIDENCE about one frozen run, and
    a producer that named them would be fitting the evidence."""
    for rel in PRODUCTION:
        found = [c for c in _executable_constants(rel)
                 if isinstance(c, str) and any(d in c for d in FIVE)]
        assert found == [], (rel, found)


def test_no_production_module_hardcodes_the_population_sizes():
    """REGRESSION 9. 2842 is one frozen run's sealed day count and 2882 is
    one frozen run's eligible count. Either as a rule would make the
    semantics a coincidence."""
    for rel in PRODUCTION:
        consts = _executable_constants(rel)
        numeric = [c for c in consts
                   if isinstance(c, int) and not isinstance(c, bool)
                   and c in (2842, 2882)]
        textual = [c for c in consts
                   if isinstance(c, str) and ("2842" in c or "2882" in c)]
        assert numeric == [] and textual == [], (rel, numeric, textual)


def test_the_repair_is_an_argument_not_a_new_constant():
    """The shape of the fix, pinned. The producer must not name a population
    of its own -- that would be a second authority on which days the
    thresholds are cut over, which is how this defect happened."""
    src = inspect.getsource(dsr.derive_day_strata_rows)
    assert "build_vol20_regime_mapping_from_universe(universe, vol_method)" \
        in src
    assert "structurally_eligible" not in src, \
        "the producer names the population itself instead of deferring"
