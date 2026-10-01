"""`supplement_inputs` assembles from bars, and never goes and gets them.

THE BOUNDARY THIS FILE PINS. Loading real Development bars is
`DevelopmentSignalLoader.load_real`, and it is gate-first by construction.
This module sits directly above it and must stay on the pure side: it takes
bars already in hand and turns them into the chain's four inputs. If it ever
reached for a file, the real-data boundary would have moved without anyone
deciding to move it.

DRIVEN OVER REAL SYNTHETIC BARS, not over mocks, because the two things most
worth checking -- that the universe actually builds and that `flag_by_date`
is keyed by `trade_date` -- are exactly what a mock would paper over. A
mis-named field would raise here; an empty universe would make the mapping
vacuously correct, so the count is asserted too.
"""

import ast
import hashlib
import inspect
import unittest
from pathlib import Path
from unittest import mock

from itsf import contracts as _c
from itsf.mc import supplement_inputs as si

from test_s0_context import NO_EVENTS, make_market

GOVERNED = (Path(_c.RULED_RUNS_ROOT), Path(_c.RULED_ARCHIVE_ROOT))
MODULE = Path(si.__file__)
DATES = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]


def _blobs():
    out = []
    for root in GOVERNED:
        if root.exists():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    out.append((str(path),
                                hashlib.sha256(path.read_bytes()).hexdigest()))
    return sorted(out)


#: A sealed universe deliberately NARROWER than the market, because that is
#: the real shape: `derive_day_strata_rows` compares by exact set equality,
#: and an unscoped mapping refuses with `event_day_invented`.
SEALED = frozenset(DATES[-2:])


def _assemble(expected_day_set=None):
    bars, schedule = make_market(DATES)
    return si.assemble_chain_inputs(
        bars_by_date=bars, schedule=schedule, events=NO_EVENTS,
        expected_day_set=(SEALED if expected_day_set is None
                          else expected_day_set))


class TestItNeverLoadsAnything(unittest.TestCase):

    def test_it_imports_no_loader(self):
        """Checked against the IMPORTS, not the raw text. The docstring names
        `dbn_loader` on purpose -- saying where the boundary is is the point
        of the file -- and a text scan that failed on prose would push the
        documentation out to make the guard pass, which is backwards."""
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(a.name for a in node.names)
        for forbidden in ("dbn_loader", "DevelopmentSignalLoader",
                          "itsf.data.dbn_loader", "manifests"):
            self.assertNotIn(forbidden, imported, forbidden)

    def test_it_calls_no_loader(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for forbidden in ("load_real", "load_manifest",
                          "DevelopmentSignalLoader"):
            self.assertNotIn(forbidden, called, forbidden)

    def test_the_source_opens_no_file(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for forbidden in ("open", "read_bytes", "read_text", "mkdir",
                          "write_bytes", "write_text", "read_parquet",
                          "read_csv"):
            self.assertNotIn(forbidden, called, forbidden)

    def test_it_stays_on_the_structural_only_side(self):
        """R3 §4's ruled boundary, asserted here as well as in the package
        sweep. The first draft used `iter_day_contexts`, which is on the S0
        dataset assembly path and reaches label computation;
        `test_no_module_in_the_package_reaches_a_forbidden_name` refused it.
        Kept local too, so the reason travels with the code that had it."""
        source = MODULE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for forbidden in ("iter_day_contexts", "build_day_context",
                          "build_s0_dataset", "compute_day"):
            self.assertNotIn(forbidden, called, forbidden)
        self.assertIn("encode_f10", called,
                      "the event flag has to come from the injected event "
                      "calendar; if this call is gone the derivation moved")

    def test_bars_by_date_is_required(self):
        """A default would let a caller omit it and leave this module to
        find bars -- the one thing it must never do."""
        params = inspect.signature(si.assemble_chain_inputs).parameters
        self.assertIs(params["bars_by_date"].default, inspect.Parameter.empty)

    def test_assembling_changes_no_governed_byte(self):
        before = _blobs()
        _assemble()
        self.assertEqual(before, _blobs())


class TestTheRuledValuesAreReadNotWrittenDown(unittest.TestCase):
    """A literal would work today and drift silently the first time the
    ratified spec moved."""

    def test_they_come_from_the_contract(self):
        # `assertEqual`, not `assertIs`: `aaron_ruled_methods()` builds a
        # fresh object per call, so identity would have measured caching
        # rather than provenance. Provenance is what the mutation below
        # measures.
        methods = _c.aaron_ruled_methods()
        vol, na = si.ruled_methods()
        self.assertEqual(methods.volatility_regime, vol)
        self.assertEqual(methods.event_na_mapping, na)

    def test_and_they_FOLLOW_the_contract_when_it_changes(self):
        """The half that a literal would also pass. If this module had the
        values baked in, this is where it would fail."""
        fake = mock.Mock(volatility_regime="MOVED",
                         event_na_mapping="ALSO_MOVED")
        with mock.patch.object(_c, "aaron_ruled_methods", return_value=fake):
            self.assertEqual(("MOVED", "ALSO_MOVED"), si.ruled_methods())

    def test_vol_method_is_an_object_and_not_a_string(self):
        """`_validate_vol_method` compares six of its FIELDS. A string would
        be refused by the producer -- and `supplement_chain` annotated this
        `str` until 2026-09-02, because its tests mock the consumer."""
        vol, _na = si.ruled_methods()
        self.assertNotIsInstance(vol, str)
        for field in ("close_source", "return_basis", "roll_crossing_rule",
                      "tercile_reference", "na_rule", "mapping_scope"):
            self.assertTrue(hasattr(vol, field), field)


class TestWhatItActuallyBuilds(unittest.TestCase):

    def test_it_returns_all_four_chain_inputs(self):
        got = _assemble()
        self.assertIsNotNone(got.universe)
        self.assertNotIsInstance(got.vol_method, str)
        self.assertEqual(_c.aaron_ruled_methods().event_na_mapping,
                         got.event_na_mapping)

    def test_flag_by_date_is_keyed_by_trade_date_and_is_not_empty(self):
        """NOT vacuous: over zero contexts the mapping would be `{}` and
        every claim about its keys would hold over nothing."""
        got = _assemble()
        self.assertTrue(got.flag_by_date, "empty, so this proves nothing")
        self.assertEqual(sorted(SEALED), sorted(got.flag_by_date))

    def test_it_is_scoped_to_the_sealed_set_and_the_market_is_wider(self):
        """The scoping is load-bearing only if there was something to scope
        away. Measured here rather than assumed."""
        got = _assemble()
        eligible = got.universe.funnel.structurally_eligible
        self.assertGreater(len(eligible), len(got.flag_by_date),
                           "the market is no wider than the sealed set, so "
                           "this fixture cannot show scoping at all")

    def test_no_sealed_day_is_dropped(self):
        """The load-bearing half of the event ruling at this layer: a sealed
        day with no event still gets an entry rather than vanishing."""
        got = _assemble()
        self.assertEqual(len(SEALED), len(got.flag_by_date))
        self.assertTrue(all(v is None or isinstance(v, str)
                            for v in got.flag_by_date.values()))

    def test_a_sealed_day_the_universe_lacks_simply_does_not_appear(self):
        """And it is NOT refused here. `_assert_day_by_day` reports both
        directions, so it arrives at the gate as `event_day_missing`; a
        second refusal here would be a second implementation of one
        invariant."""
        got = _assemble(SEALED | {"1999-01-04"})
        self.assertNotIn("1999-01-04", got.flag_by_date)
        self.assertEqual(sorted(SEALED), sorted(got.flag_by_date))

    def test_expected_day_set_is_required(self):
        params = inspect.signature(si.assemble_chain_inputs).parameters
        self.assertIs(params["expected_day_set"].default,
                      inspect.Parameter.empty)


if __name__ == "__main__":
    unittest.main()
