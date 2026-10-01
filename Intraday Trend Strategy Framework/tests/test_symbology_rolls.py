"""Roll transitions come from vendor symbology, and they change vol20.

THE DEFECT THIS CLOSES. `build_universe` takes `roll_intervals` and nothing
produced any, so every caller passed `()`. With an empty transition list
`dataset._straddles_roll` is always False, `r1_drop_and_extend` drops
nothing, and vol20 is computed across contract rolls -- a price
discontinuity counted as a return, 47 times over the Development window.

NO REAL DATA IS READ HERE. The pure half is exercised on hand-built vendor
intervals; the I/O half is asserted structurally. The suite must not open
Development files on every run, and a test that did would make the boundary
depend on nobody noticing.
"""

import ast
import unittest
from pathlib import Path

from itsf.data import symbology
from itsf.s0 import dataset as s0d

MODULE = Path(symbology.__file__)


class TestCoalescing(unittest.TestCase):
    """The vendor splits its mapping at FILE boundaries, so month starts look
    like switches until adjacent same-instrument runs are merged."""

    def test_month_boundaries_are_not_rolls(self):
        vendor = [("2010-07-01", "2010-08-01", "26715"),
                  ("2010-08-01", "2010-09-01", "26715"),
                  ("2010-09-01", "2010-09-13", "26715"),
                  ("2010-09-13", "2010-10-01", "31415")]
        merged = symbology.coalesce(vendor)
        self.assertEqual((("2010-07-01", "2010-09-13", "26715"),
                          ("2010-09-13", "2010-10-01", "31415")), merged)
        self.assertEqual(("2010-09-13",),
                         symbology.roll_transition_dates(merged))

    def test_the_first_interval_start_is_not_a_transition(self):
        """It is the start of the sample. Counting it would drop a return
        that never crossed anything."""
        merged = symbology.coalesce([("2010-06-06", "2010-06-14", "6641"),
                                     ("2010-06-14", "2010-07-01", "26715")])
        self.assertEqual(("2010-06-14",),
                         symbology.roll_transition_dates(merged))

    def test_a_repeated_instrument_after_a_gap_is_not_merged(self):
        """Same instrument, non-adjacent: merging across the gap would erase
        the transition into and out of whatever ran between them."""
        merged = symbology.coalesce([("2010-01-01", "2010-02-01", "A"),
                                     ("2010-02-01", "2010-03-01", "B"),
                                     ("2010-03-01", "2010-04-01", "A")])
        self.assertEqual(3, len(merged))
        self.assertEqual(("2010-02-01", "2010-03-01"),
                         symbology.roll_transition_dates(merged))

    def test_it_is_order_independent(self):
        vendor = [("2010-08-01", "2010-09-01", "X"),
                  ("2010-07-01", "2010-08-01", "X")]
        self.assertEqual(symbology.coalesce(vendor),
                         symbology.coalesce(reversed(vendor)))

    def test_no_transitions_when_one_instrument_spans_everything(self):
        merged = symbology.coalesce([("2010-01-01", "2010-02-01", "X"),
                                     ("2010-02-01", "2010-03-01", "X")])
        self.assertEqual((), symbology.roll_transition_dates(merged))


class TestItNeverInfersFromPrices(unittest.TestCase):
    """The transitions must be vendor FACT, not price inference."""

    def test_the_source_decodes_no_bars(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for forbidden in ("to_df", "load_real", "read_csv", "read_parquet"):
            self.assertNotIn(forbidden, called, forbidden)

    def test_the_source_reads_the_vendor_mapping_by_name(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("metadata.mappings", source)

    def test_it_names_no_price_column(self):
        source = MODULE.read_text(encoding="utf-8")
        for column in ('"open"', '"high"', '"low"', '"close"', '"volume"'):
            self.assertNotIn(column, source, column)


class TestWhyAnEmptyListIsWrong(unittest.TestCase):
    """The reason this module exists, executed rather than asserted."""

    def test_a_return_straddling_a_roll_is_dropped_only_if_told(self):
        older, newer = "2021-12-10", "2021-12-14"
        self.assertTrue(s0d._straddles_roll(older, newer, ["2021-12-13"]))
        self.assertFalse(
            s0d._straddles_roll(older, newer, []),
            "with no transitions the roll is invisible, so r1_drop_and_extend "
            "drops nothing and vol20 counts a contract change as a return")

    def test_the_boundary_is_half_open_on_the_older_side(self):
        """`older < t <= newer`: a transition ON the older date belongs to
        the previous return, not this one."""
        self.assertFalse(s0d._straddles_roll("2021-12-13", "2021-12-14",
                                             ["2021-12-13"]))
        self.assertTrue(s0d._straddles_roll("2021-12-12", "2021-12-13",
                                            ["2021-12-13"]))


if __name__ == "__main__":
    unittest.main()
