"""The row producer, R3 §4's pinned call graph.

This is the step that had never been written. Everything downstream of it
existed — `day_strata_supplement` validates and digests rows,
`supplement_production` builds the product, mints the receipt and seals —
and nothing produced the rows.

WHAT EACH TEST HOLDS, stated because a producer's refusals are the only
thing standing between a sealed supplement and a wrong one:

    vocabulary      compared by SET, never by order (the two orders differ
                    today, and an order comparison would false-red)
    day universe    EXACT, day by day, with "missing" and "invented"
                    reported as SEPARATE refusals — they are different
                    defects and an operator needs different actions
    values          every stratum must be inside the supplement's own
                    vocabulary before it reaches the sealed bytes
    year            derived by a checked parse, not `int(day[:4])`
    order           rows sorted by trade_date, so the digest does not
                    depend on how a mapping happened to iterate

WHAT IS NOT TESTED HERE, and why: the real-data acquisition. `load_real`
is not called from the producer at all — it sits behind
`assert_real_run_allowed` in the runner. A producer that opened Development
data would put a second real read into a module the authorization gate does
not guard.
"""

import unittest
from unittest import mock

from itsf.mc import day_strata_rows as dsr
from itsf.mc import day_strata_supplement as ds
from itsf.s0 import dataset as s0

DAYS = ("2024-01-02", "2024-01-03", "2024-01-04")


class _Vol:
    def __init__(self, label_of):
        self.label_of = label_of


def _patched(label_of, stratum_of):
    """Substitute the two ruled S0 producers, nothing else.

    Patched rather than driven end-to-end because building a real
    `S0Universe` needs Development bars, and `REAL_DATA_READ_AUTHORIZED=NO`.
    What is under test is the producer's own contract — the call graph
    itself is pinned separately, at the AST level, by
    `test_n09_scaffold_criteria.py`."""
    return mock.patch.multiple(
        s0,
        build_vol20_regime_mapping_from_universe=mock.Mock(
            return_value=_Vol(label_of)),
        build_event_stratum_map=mock.Mock(
            return_value={"stratum_of": stratum_of}),
    )


def _derive(label_of, stratum_of, expected=None):
    # `expected if expected is not None else DAYS` — NOT `expected or DAYS`.
    # The first version used `or`, so passing `()` to test the empty-universe
    # refusal silently substituted the three real days and the test measured
    # a different refusal than it named.
    days = DAYS if expected is None else expected
    with _patched(label_of, stratum_of):
        return dsr.derive_day_strata_rows(
            universe=object(), vol_method="ruled",
            flag_by_date={}, event_na_mapping="ruled",
            expected_day_set=frozenset(days))


class TestTheHappyPath(unittest.TestCase):

    def test_one_row_per_sealed_day_with_the_four_ruled_fields(self):
        rows = _derive({d: "T1" for d in DAYS},
                       {d: "none" for d in DAYS})
        self.assertEqual(len(DAYS), len(rows))
        for row in rows:
            self.assertEqual(set(ds.ROW_FIELDS), set(row))

    def test_rows_come_back_sorted_by_trade_date(self):
        """The digest must not depend on iteration order.

        THE FIRST VERSION OF THIS TEST WAS FLAKY, and finding that out is
        worth more than the test. It scrambled the `label_of` mapping and
        asserted the output was sorted — but the row order comes from
        `sorted(expected_day_set)`, and the mutation that removes that
        `sorted` was caught only when the frozenset's own iteration order
        happened to differ. String hashing is randomised per process, so
        that was a coin flip: sometimes red, sometimes silently green.

        A test that holds a property only on some runs is worse than one
        that does not hold it, because the green tells you nothing.

        So it sweeps several universes and requires at least one whose
        iteration order really is unsorted. If a run's hash seed makes
        every one of them sorted, it SKIPS with the reason rather than
        passing over nothing."""
        universes = [
            tuple("2024-01-%02d" % d for d in range(2, 2 + n))
            for n in (3, 5, 8, 13)
        ]
        exercised = 0
        for days in universes:
            if list(frozenset(days)) == sorted(days):
                continue                    # this seed gave a sorted set
            exercised += 1
            rows = _derive({d: "T1" for d in days},
                           {d: "none" for d in days}, expected=days)
            self.assertEqual(sorted(days), [r["trade_date"] for r in rows],
                             "the producer emitted rows in the set's "
                             "iteration order, not sorted")
        if not exercised:                   # pragma: no cover - seed-dependent
            self.skipTest("every candidate frozenset iterated in sorted "
                          "order under this run's hash seed; the property "
                          "was not exercised")

    def test_the_strata_are_transcribed_not_decided(self):
        """R3 §4: 生产者自身不得携带任何分层逻辑. Every value comes out of
        the ruled mapping unchanged."""
        rows = _derive({"2024-01-02": "T3", "2024-01-03": "vol_na",
                        "2024-01-04": "T1"},
                       {"2024-01-02": "CPI", "2024-01-03": "NA_multi_event",
                        "2024-01-04": "none"})
        self.assertEqual(["T3", "vol_na", "T1"],
                         [r["vol_stratum"] for r in rows])
        self.assertEqual(["CPI", "NA_multi_event", "none"],
                         [r["event_stratum"] for r in rows])

    def test_the_rows_feed_the_supplement_builder(self):
        """The integration this producer exists for. If the shape were
        wrong, every test above could pass and the supplement would still
        refuse the rows."""
        rows = _derive({d: "T2" for d in DAYS}, {d: "none" for d in DAYS})
        built = ds.build_day_strata_supplement_test_only(
            rows, expected_day_set=frozenset(DAYS),
            binding=_a_binding())
        self.assertEqual(len(DAYS), len(built["rows"]))
        self.assertTrue(built["rows_digest"])


class TestTheDayUniverseIsExact(unittest.TestCase):
    """R3 §4: 逐日精确相等对拍（不是覆盖，不是包含）."""

    def test_a_missing_day_refuses_and_says_so(self):
        short = {d: "T1" for d in DAYS[:-1]}
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _derive(short, {d: "none" for d in DAYS})
        self.assertEqual("vol_day_missing", caught.exception.code)

    def test_a_WIDER_vol_population_is_accepted_and_projected(self):
        """THE 2026-09-06 REPAIR, and this test used to assert its opposite.

        It pinned `vol_day_invented` for a vol mapping carrying a day outside
        the sealed set. That was right while the producer handed the sealed
        set to the tercile constructor -- and it was also the defect: the
        thresholds were then cut over the sealed sample instead of the
        structurally eligible one S0-T001 cut them over, which moved labels
        for days near a cut. A strict-blind verification proved it.

        The population is now DELIBERATELY a superset, so "invented" is no
        longer a defect on this axis. What must hold instead is that the
        extra day changes nothing about the OUTPUT: the rows are still
        exactly the sealed set, and each label is still the population's own
        value for that day, transcribed.

        The `vol_day_invented` code is not gone -- the event axis still
        raises it, and `test_the_event_mapping_is_checked_the_same_way`'s
        sibling below covers that direction."""
        extra = dict({d: "T1" for d in DAYS}, **{"2024-01-05": "T3"})
        rows = _derive(extra, {d: "none" for d in DAYS})
        self.assertEqual(sorted(DAYS), [r["trade_date"] for r in rows])
        self.assertNotIn("2024-01-05", [r["trade_date"] for r in rows])
        self.assertEqual(["T1"] * len(DAYS),
                         [r["vol_stratum"] for r in rows])

    def test_an_invented_day_on_the_EVENT_axis_still_refuses(self):
        """The direction that did NOT change. The event mapping is still
        compared to the sealed set by exact equality in both directions."""
        extra = dict({d: "none" for d in DAYS}, **{"2024-01-05": "none"})
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _derive({d: "T1" for d in DAYS}, extra)
        self.assertEqual("event_day_invented", caught.exception.code)

    def test_the_event_mapping_is_checked_the_same_way(self):
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _derive({d: "T1" for d in DAYS},
                    {d: "none" for d in DAYS[:-1]})
        self.assertEqual("event_day_missing", caught.exception.code)

    def test_an_empty_sealed_universe_refuses(self):
        """Otherwise every conservation check above would pass over
        nothing — the vacuous-guard shape, in production code."""
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _derive({}, {}, expected=())
        self.assertEqual("expected_day_set_empty", caught.exception.code)

    def test_a_non_frozenset_universe_refuses(self):
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            with _patched({d: "T1" for d in DAYS},
                          {d: "none" for d in DAYS}):
                dsr.derive_day_strata_rows(
                    universe=object(), vol_method="ruled", flag_by_date={},
                    event_na_mapping="ruled", expected_day_set=set(DAYS))
        self.assertEqual("expected_day_set_not_frozenset",
                         caught.exception.code)


class TestVocabulary(unittest.TestCase):

    def test_the_two_packages_agree_as_SETS(self):
        dsr.assert_vocabularies_agree()

    def test_the_orders_really_do_differ(self):
        """The premise for comparing by set, asserted before the behaviour
        that depends on it. R3 §4 calls this out because an order
        comparison would report a drift that does not exist."""
        self.assertNotEqual(tuple(s0.EVENT_STRATA), tuple(ds.EVENT_STRATA))
        self.assertEqual(set(s0.EVENT_STRATA), set(ds.EVENT_STRATA))

    def test_a_real_drift_is_caught(self):
        with mock.patch.object(s0, "EVENT_STRATA",
                               ("CPI", "FOMC", "NFP", "none")):
            with self.assertRaises(dsr.DayStrataRowsError) as caught:
                dsr.assert_vocabularies_agree()
        self.assertEqual("event_vocabulary_drift", caught.exception.code)

    def test_a_value_outside_the_vocabulary_refuses(self):
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _derive(dict({d: "T1" for d in DAYS},
                         **{"2024-01-03": "T9"}),
                    {d: "none" for d in DAYS})
        self.assertEqual("vol_stratum_outside_vocabulary",
                         caught.exception.code)


class TestTheYearIsParsedNotSliced(unittest.TestCase):
    """`int(day[:4])` accepts four characters nobody checked, and the value
    lands in the sealed bytes."""

    def test_a_well_formed_date_gives_its_year(self):
        rows = _derive({d: "T1" for d in DAYS}, {d: "none" for d in DAYS})
        self.assertEqual([2024] * len(DAYS), [r["year"] for r in rows])

    def test_a_malformed_date_refuses(self):
        bad = "2024-1-2"
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _derive({bad: "T1"}, {bad: "none"}, expected=(bad,))
        self.assertEqual("trade_date_malformed", caught.exception.code)

    def test_a_slice_would_have_accepted_it(self):
        """The reason the parse is not a slice, made explicit."""
        self.assertEqual(2024, int("2024-1-2"[:4]))


def _a_binding():
    """The smallest binding the supplement builder accepts.

    Shapes taken from `_validate_binding`, not guessed: `authorized_commit`
    is 40-hex, the two digests are 64-hex, and `trial_id` / `method_version`
    are non-empty strings. My first version filled everything with 64 `x`
    and the builder correctly refused `authorized_commit is not 40-hex`."""
    return {
        "trial_id": "S0-T001",
        "authorized_commit": "a" * 40,
        "day_universe_digest": "b" * 64,
        "method_version": ds.SUPPLEMENT_SCHEMA,
        "source_input_sha256": "c" * 64,
    }


if __name__ == "__main__":
    unittest.main()
