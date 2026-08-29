"""Every producer refusal reaches exactly one C_BUILD gate.

The load-bearing test here is not that the mapping is right for the codes
someone listed — it is that the LIST IS DERIVED. `GATE_OF_PRODUCER_CODE` is
a hand-written table, and a hand-written table that mirrors something else
goes stale the first time the something else changes. That failure has
happened four times in this project in one evening (two `$`-anchor sweeps,
`ANCHOR_MODULES`, and the structural-only scan), so the table is checked
against the producer's SOURCE rather than against memory.

An unmapped code must be loud, not defaulted: the gate name is what the
F1/F2 failure event carries, so a code arriving under someone else's gate
would write the wrong defect into the registry.
"""

import ast
import io
import unittest
from pathlib import Path

from itsf.mc import day_strata_classify as dsc
from itsf.mc import day_strata_rows as dsr
from itsf.mc import supplement_contract as sc

PRODUCER = (Path(__file__).resolve().parents[1]
            / "src" / "itsf" / "mc" / "day_strata_rows.py")


def _codes_the_producer_can_raise():
    """Every literal first argument to `DayStrataRowsError(...)`, from the
    producer's AST. Derived, so a new refusal joins this check by existing
    rather than by being remembered."""
    tree = ast.parse(io.open(PRODUCER, encoding="utf-8").read())
    codes = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or not isinstance(node.exc,
                                                             ast.Call):
            continue
        if getattr(node.exc.func, "id", "") != "DayStrataRowsError":
            continue
        if not node.exc.args:
            continue
        first = node.exc.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            codes.add(first.value)
        elif isinstance(first, ast.JoinedStr):
            # f"{which}_day_missing" — the interpolated prefix is one of a
            # known pair, so both concrete codes are recorded.
            tail = "".join(v.value for v in first.values
                           if isinstance(v, ast.Constant))
            for which in ("vol", "event"):
                codes.add(which + tail)
    return codes


class TestTheTableIsDerivedNotRemembered(unittest.TestCase):

    def test_every_producer_code_has_exactly_one_gate(self):
        unmapped = sorted(_codes_the_producer_can_raise()
                          - set(dsc.GATE_OF_PRODUCER_CODE))
        self.assertEqual(
            [], unmapped,
            "these producer refusals reach no gate, so their failure event "
            "would carry the wrong gate name: %s" % unmapped)

    def test_the_table_names_no_code_the_producer_cannot_raise(self):
        """The other direction. A stale entry is a mapping nobody will
        notice is wrong, because it never fires."""
        stale = sorted(set(dsc.GATE_OF_PRODUCER_CODE)
                       - _codes_the_producer_can_raise())
        self.assertEqual([], stale,
                         "the table maps codes the producer cannot raise: %s"
                         % stale)

    def test_the_derivation_actually_found_codes(self):
        """A scan that matches nothing reports clean."""
        found = _codes_the_producer_can_raise()
        self.assertGreater(len(found), 8,
                           "the AST scan found %d producer codes, which is "
                           "too few to be real" % len(found))

    def test_every_gate_named_is_a_real_c_build_gate(self):
        """A typo in the table would name a gate that does not exist, and
        the failure event would carry it."""
        c_build = set(sc.GATE_TABLE["C_BUILD"])
        for code, gate in sorted(dsc.GATE_OF_PRODUCER_CODE.items()):
            with self.subTest(code=code):
                self.assertIn(gate, c_build)


class TestClassification(unittest.TestCase):

    def test_a_day_universe_refusal_reaches_day_set_exact(self):
        exc = dsr.DayStrataRowsError("vol_day_missing", "detail")
        self.assertEqual("day_set_exact", dsc.classify_producer_failure(exc))

    def test_a_row_refusal_reaches_row_schema_blind(self):
        exc = dsr.DayStrataRowsError("trade_date_malformed", "detail")
        self.assertEqual("row_schema_blind",
                         dsc.classify_producer_failure(exc))

    def test_an_unknown_code_refuses_rather_than_defaulting(self):
        exc = dsr.DayStrataRowsError("something_new", "detail")
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_producer_failure(exc)
        self.assertIn("has no gate", str(caught.exception))
        self.assertIn("do NOT let it fall through", str(caught.exception))

    def test_a_foreign_exception_refuses(self):
        with self.assertRaises(dsc.ClassificationError):
            dsc.classify_producer_failure(ValueError("not a producer code"))

    def test_the_three_c_build_1_gates_are_all_reachable(self):
        """A partition that only ever names one gate is not a partition.

        `rows_digest_recompute` is deliberately absent from the table: the
        producer does not compute the digest — `day_strata_supplement` does
        — so no producer code maps to it. Asserted rather than left as an
        apparent gap."""
        used = set(dsc.GATE_OF_PRODUCER_CODE.values())
        self.assertEqual({"row_schema_blind", "day_set_exact"}, used)
        self.assertIn("rows_digest_recompute", sc.GATE_TABLE["C_BUILD"])




def _seal_codes_from_source():
    """Every literal code the seal step can refuse with, derived.

    Two sources: `seal_supplement_production`'s own drift checks, and the
    `resolve_partial` codes it inherits by calling it. Both are read from
    source so a new refusal joins this check by existing."""
    root = Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"
    codes = set()
    prod = ast.parse(io.open(root / "supplement_production.py",
                             encoding="utf-8").read())
    seal = [n for n in ast.walk(prod) if isinstance(n, ast.FunctionDef)
            and n.name == "seal_supplement_production"]
    for fn in seal:
        for node in ast.walk(fn):
            if (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                    and node.exc.args
                    and isinstance(node.exc.args[0], ast.Constant)):
                codes.add(node.exc.args[0].value)
    runner = ast.parse(io.open(root / "supplement_runner.py",
                               encoding="utf-8").read())
    rp = [n for n in ast.walk(runner) if isinstance(n, ast.FunctionDef)
          and n.name in ("resolve_partial", "_preserve", "_divergent_name")]
    for fn in rp:
        for node in ast.walk(fn):
            if (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                    and node.exc.args
                    and isinstance(node.exc.args[0], ast.Constant)):
                codes.add(node.exc.args[0].value)
    return {c for c in codes if isinstance(c, str)}


class TestTheSealTableIsDerivedToo(unittest.TestCase):

    def test_every_seal_code_is_mapped_or_recorded_as_undecided(self):
        known = (set(dsc.STAGE_GATE_OF_SEAL_CODE)
                 | set(dsc.UNDECIDED_SEAL_CODES))
        missing = sorted(_seal_codes_from_source() - known)
        self.assertEqual(
            [], missing,
            "these seal refusals are in neither table: %s\nAdd each to "
            "STAGE_GATE_OF_SEAL_CODE with the raise site that justifies the "
            "gate, or to UNDECIDED_SEAL_CODES with the question." % missing)

    def test_the_two_tables_do_not_overlap(self):
        """A code that is both mapped and undecided would classify silently
        while claiming to be an open question."""
        both = sorted(set(dsc.STAGE_GATE_OF_SEAL_CODE)
                      & set(dsc.UNDECIDED_SEAL_CODES))
        self.assertEqual([], both)

    def test_neither_table_names_a_code_the_seal_cannot_raise(self):
        found = _seal_codes_from_source()
        stale = sorted((set(dsc.STAGE_GATE_OF_SEAL_CODE)
                        | set(dsc.UNDECIDED_SEAL_CODES)) - found)
        self.assertEqual([], stale, "stale entries: %s" % stale)

    def test_the_derivation_found_both_sources(self):
        """A scan that reached only one module would look clean while
        missing half the surface."""
        found = _seal_codes_from_source()
        self.assertIn("production_rows_digest_drift", found)   # the seal's
        self.assertIn("supplement_seal_conflict", found)       # resolve_partial's

    def test_every_mapped_pair_is_a_real_stage_and_gate(self):
        for code, (stage, gate) in sorted(
                dsc.STAGE_GATE_OF_SEAL_CODE.items()):
            with self.subTest(code=code):
                self.assertIn(stage, sc.STAGE_ENUM)
                self.assertIn(gate, sc.GATE_TABLE[stage])

    def test_the_b_derive_codes_really_are_b_derive(self):
        """The reason the table carries pairs. Putting an authority defect
        under C_BUILD would file the right defect at the wrong stage, and
        the stage is half of what the failure event carries."""
        for code in ("production_binding_drift",
                     "production_day_universe_drift"):
            with self.subTest(code=code):
                stage, gate = dsc.classify_seal_failure(code)
                self.assertEqual("B_DERIVE", stage)
                self.assertIn(gate, sc.GATE_TABLE["B_DERIVE"])

    def test_an_undecided_code_refuses_with_its_question(self):
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_seal_failure("production_payload_drift")
        message = str(caught.exception)
        self.assertIn("no ratified gate", message)
        self.assertIn("rebuild to", message)
        self.assertIn("nobody ruled", message)

    def test_an_unknown_code_refuses_differently(self):
        """"Undecided" and "unheard of" are different states and an
        operator needs different actions."""
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_seal_failure("brand_new_code")
        self.assertIn("in neither table", str(caught.exception))

    def test_the_undecided_set_is_not_empty_by_accident(self):
        """If it ever empties, it should be because someone RULED, and the
        ruling should be recorded — not because the entries were quietly
        moved into the mapped table."""
        self.assertEqual(2, len(dsc.UNDECIDED_SEAL_CODES))
        for code, question in dsc.UNDECIDED_SEAL_CODES.items():
            with self.subTest(code=code):
                self.assertGreater(len(question), 60,
                                   "%s carries no real question" % code)


if __name__ == "__main__":
    unittest.main()
