"""A sealed handoff line carries S0's PUBLISHED names, not the internal ones.

THE BOUNDARY. `s0.report.record_to_formal_dict` publishes the frozen §10.1
record: `entry_ts`/`exit_ts` become `entry_timestamp`/`exit_timestamp` and
"every other field keeps its internal name" -- 17 of 19 verbatim, measured
below rather than assumed. S0 goes further and treats an internal name
appearing on a sealed line as a LEAK, "never silently accepted as a synonym",
so the published spelling is not one of two options; it is the only legal one.

WHAT WENT WRONG. `consumer._parse_record` validated the sealed line against
the INTERNAL dataclass -- the wrong side of that boundary. It demanded names
S0 guarantees will never be there, and the first real N09 run refused the real
bundle with `record_schema_violation`.

WHY THE SUITE NEVER CAUGHT IT, and it is the same shape as the manifest
defect found the same day: every synthetic fixture built its rows with
`dataclasses.asdict(rec)`, so the fixtures emitted the internal names -- a
shape S0 would never seal. The fixtures agreed with the consumer's mistake
instead of with the producer. They now go through `record_to_formal_dict`,
which is what actually writes a sealed line.

WHAT IS NOT AFFECTED, and it is the part worth checking rather than
asserting: `FrozenTradePath`, `_record_canonical_row` and the records custody
digest all still use the INTERNAL names, so no custody digest moves. A rename
that quietly changed an identity digest would be a much larger act than the
one authorised.

Synthetic bytes only.
"""

import dataclasses
import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from conftest import make_trade_path                # noqa: E402
from itsf.contracts import TradePathRecord          # noqa: E402
from itsf.mc import consumer as mcc                 # noqa: E402
from itsf.mc.atoms import MCInputError              # noqa: E402
from itsf.s0.report import (FORMAL_RECORD_FIELDS,   # noqa: E402
                            record_to_formal_dict)

#: The two names S0 renames at the publish boundary, written out HERE so the
#: test does not read its expectation from the same map the code uses.
RENAMED = {"entry_ts": "entry_timestamp", "exit_ts": "exit_timestamp"}


def _rec():
    return make_trade_path([40.0, 80.0], date="2026-08-03", final=80.0)


class TestTheTwoSpellings(unittest.TestCase):

    def test_exactly_two_names_differ_and_seventeen_are_verbatim(self):
        internal = set(TradePathRecord.__dataclass_fields__)
        published = set(FORMAL_RECORD_FIELDS)
        self.assertEqual(19, len(internal))
        self.assertEqual(19, len(published))
        self.assertEqual(set(RENAMED), internal - published)
        self.assertEqual(set(RENAMED.values()), published - internal)
        self.assertEqual(17, len(internal & published))

    def test_the_rename_does_not_touch_the_value(self):
        rec = _rec()
        formal = record_to_formal_dict(rec)
        for internal_name, published_name in RENAMED.items():
            with self.subTest(field=internal_name):
                self.assertEqual(getattr(rec, internal_name),
                                 formal[published_name])

    def test_the_consumers_map_is_s0s_map_inverted(self):
        """Taken FROM S0, not restated. If someone hand-edits the consumer's
        map it stops agreeing with the producer, and this says so."""
        self.assertEqual({v: k for k, v in RENAMED.items()},
                         dict(mcc._PUBLISHED_TO_INTERNAL))


class TestTheParserReadsThePublishedShape(unittest.TestCase):

    def test_a_published_row_parses(self):
        parsed = mcc._parse_record(record_to_formal_dict(_rec()), "f", 0)
        self.assertEqual(_rec().entry_ts, parsed.entry_ts)

    def test_an_internal_named_row_is_refused_as_the_leak_s0_calls_it(self):
        """S0: an internal name on a sealed line is a leak, 'never silently
        accepted as a synonym'. Accepting both spellings would contradict a
        ratified guard, so the fix is a rename, not an alias."""
        with self.assertRaises(MCInputError) as caught:
            mcc._parse_record(dataclasses.asdict(_rec()), "f", 0)
        self.assertEqual("record_schema_violation", caught.exception.code)

    def test_a_missing_published_field_is_still_refused(self):
        row = record_to_formal_dict(_rec())
        del row["entry_timestamp"]
        with self.assertRaises(MCInputError) as caught:
            mcc._parse_record(row, "f", 0)
        self.assertEqual("record_schema_violation", caught.exception.code)

    def test_an_extra_field_is_still_refused(self):
        row = record_to_formal_dict(_rec())
        row["diagnostic_extra"] = 1
        with self.assertRaises(MCInputError) as caught:
            mcc._parse_record(row, "f", 0)
        self.assertEqual("record_schema_violation", caught.exception.code)


class TestNoCustodyDigestMoved(unittest.TestCase):
    """The load-bearing negative. A rename that also changed an identity
    digest would invalidate evidence, which is not what was authorised."""

    def test_the_records_digest_schema_still_lists_the_internal_names(self):
        parsed = mcc._parse_record(record_to_formal_dict(_rec()), "f", 0)
        row = mcc._record_canonical_row(parsed, where="test")
        self.assertEqual(set(TradePathRecord.__dataclass_fields__), set(row))
        for name in RENAMED.values():
            self.assertNotIn(name, row)

    def test_the_digest_preimage_is_byte_identical_to_the_internal_names(self):
        """Computed the way `records_digest` computes it, so a change to the
        field list would change these bytes."""
        preimage = json.dumps(
            {"schema": mcc.RECORDS_DIGEST_SCHEMA,
             "fields": list(mcc._RECORD_FIELDS)}, sort_keys=True)
        self.assertIn("entry_ts", preimage)
        self.assertNotIn("entry_timestamp", preimage)
        self.assertEqual(
            hashlib.sha256(json.dumps(
                {"schema": mcc.RECORDS_DIGEST_SCHEMA,
                 "fields": list(TradePathRecord.__dataclass_fields__)},
                sort_keys=True).encode("utf-8")).hexdigest(),
            hashlib.sha256(preimage.encode("utf-8")).hexdigest())


class TestTheFixturesNowProduceWhatS0Produces(unittest.TestCase):
    """The defect was never in the code alone -- it was that no fixture
    disagreed with it."""

    def test_no_mc_fixture_builds_a_row_with_asdict_any_more(self):
        """The scan's PREMISE is asserted first, because this repository's
        own meta-guard caught the first draft of this test: an absence
        asserted over a collection that might be empty passes by looking at
        nothing. Twelve fixtures were converted; if the glob ever stops
        finding them, that is the failure, not a clean bill."""
        builders, offenders = [], []
        for path in sorted((REPO / "tests").glob("test_mc_*.py")):
            text = path.read_text(encoding="utf-8")
            if "def _record_row" not in text:
                continue
            builders.append(path.name)
            if "dataclasses.asdict(rec)" in text:
                offenders.append(path.name)
        self.assertGreaterEqual(
            len(builders), 12,
            "the scan found %d record-building fixtures; twelve were "
            "converted, so a smaller number means the scan stopped "
            "matching rather than the defect being gone" % len(builders))
        self.assertEqual([], offenders,
                         "these fixtures emit the internal names, a shape S0 "
                         "would never seal: %r" % offenders)
        for name in builders:
            with self.subTest(fixture=name):
                self.assertIn("record_to_formal_dict",
                              (REPO / "tests" / name).read_text(
                                  encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
