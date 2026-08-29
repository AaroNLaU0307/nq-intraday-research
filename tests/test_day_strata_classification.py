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




def _builder_codes_from_source():
    """Every literal code `build_supplement_from_authority` can raise.

    Derived, for the same reason every other table here is: a hand-written
    mirror goes stale, and this project produced five instances of exactly
    that in one day. The sixth was the one that made this table necessary --
    `run_c_build` classified all of these as `row_schema_blind` on a comment
    claiming the builder only validates rows."""
    root = Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"
    tree = ast.parse(io.open(root / "supplement_production.py",
                             encoding="utf-8").read())
    fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
          and n.name == "build_supplement_from_authority"]
    codes = set()
    for f in fn:
        for node in ast.walk(f):
            if (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                    and node.exc.args
                    and isinstance(node.exc.args[0], ast.Constant)):
                codes.add(node.exc.args[0].value)
    return codes


class TestTheBuilderTableIsDerivedToo(unittest.TestCase):
    """Added 2026-08-29 after the end-to-end rehearsal found a B_DERIVE
    defect being filed under a C_BUILD gate."""

    def test_every_builder_code_is_mapped_or_marked_a_caller_bug(self):
        known = (set(dsc.STAGE_GATE_OF_BUILDER_CODE)
                 | set(dsc.CALLER_ERROR_BUILDER_CODES))
        missing = sorted(_builder_codes_from_source() - known)
        self.assertEqual(
            [], missing,
            "these builder refusals are in neither table: %s\nEach must "
            "either name a (stage, gate) justified by its raise site, or be "
            "recorded as a caller bug that never becomes a row." % missing)

    def test_the_derivation_found_the_codes(self):
        found = _builder_codes_from_source()
        self.assertGreaterEqual(len(found), 5)
        self.assertIn("production_authority_test_only", found)

    def test_neither_builder_table_names_a_code_it_cannot_raise(self):
        stale = sorted((set(dsc.STAGE_GATE_OF_BUILDER_CODE)
                        | set(dsc.CALLER_ERROR_BUILDER_CODES))
                       - _builder_codes_from_source())
        self.assertEqual([], stale, "stale builder entries: %s" % stale)

    def test_the_two_builder_tables_do_not_overlap(self):
        self.assertEqual([], sorted(set(dsc.STAGE_GATE_OF_BUILDER_CODE)
                                    & set(dsc.CALLER_ERROR_BUILDER_CODES)))

    def test_every_mapped_pair_is_a_real_stage_and_gate(self):
        for code, (stage, gate) in sorted(
                dsc.STAGE_GATE_OF_BUILDER_CODE.items()):
            with self.subTest(code=code):
                self.assertIn(stage, sc.STAGE_ENUM)
                self.assertIn(gate, sc.GATE_TABLE[stage])

    def test_the_authority_codes_really_are_B_DERIVE(self):
        """The correction itself. Under C_BUILD these would file an
        authority defect at the stage that builds rows."""
        for code in ("production_authority_type",
                     "production_authority_test_only",
                     "production_supplement_id_divergence"):
            with self.subTest(code=code):
                stage, gate = dsc.classify_builder_failure(code)
                self.assertEqual("B_DERIVE", stage)

    def test_a_caller_bug_refuses_and_says_so(self):
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_builder_failure("production_unknown_argument")
        message = str(caught.exception)
        self.assertIn("CALLER BUG", message)
        self.assertIn("Fix the call site", message)

    def test_an_unknown_builder_code_refuses_differently(self):
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_builder_failure("production_brand_new")
        self.assertIn("in neither builder table", str(caught.exception))


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
                 | set(dsc.ROUTER_B_SEAL_CODES))
        missing = sorted(_seal_codes_from_source() - known)
        self.assertEqual(
            [], missing,
            "these seal refusals are in neither table: %s\nAdd each to "
            "STAGE_GATE_OF_SEAL_CODE with the raise site that justifies the "
            "gate, or to ROUTER_B_SEAL_CODES with the reason." % missing)

    def test_the_two_tables_do_not_overlap(self):
        """A code in both tables would have two routers, and the one that
        won would be whichever branch was written first."""
        both = sorted(set(dsc.STAGE_GATE_OF_SEAL_CODE)
                      & set(dsc.ROUTER_B_SEAL_CODES))
        self.assertEqual([], both)

    def test_neither_table_names_a_code_the_seal_cannot_raise(self):
        found = _seal_codes_from_source()
        stale = sorted((set(dsc.STAGE_GATE_OF_SEAL_CODE)
                        | set(dsc.ROUTER_B_SEAL_CODES)) - found)
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

    def test_a_router_b_code_refuses_by_NAMING_ITS_ROUTER(self):
        """BD-1, executed. This used to say "nobody ruled". Somebody has:
        the refusal now tells the caller where the outcome actually lives
        instead of leaving them at a dead end."""
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_seal_failure("production_payload_drift")
        message = str(caught.exception)
        self.assertIn("that is the RULING (BD-1)", message)
        self.assertIn("decide_after_seal", message)
        self.assertIn("no P4 and no A1", message)
        self.assertNotIn("nobody ruled", message)

    def test_the_router_is_answerable_without_raising(self):
        """A caller that wants to ROUTE should not have to catch an
        exception and read its prose to find out where to go."""
        self.assertEqual(dsc.ROUTER_B,
                         dsc.seal_failure_router("production_payload_drift"))
        self.assertEqual(
            dsc.ROUTER_A,
            dsc.seal_failure_router("production_rows_digest_drift"))
        with self.assertRaises(dsc.ClassificationError):
            dsc.seal_failure_router("brand_new_code")

    def test_router_b_really_does_have_an_answer_for_a_failed_seal(self):
        """The premise of the whole ruling, measured on the runner rather
        than asserted. If `decide_after_seal` had no answer for
        local_seal_ok=False, BD-1 would be routing these codes into a hole."""
        from itsf.mc import supplement_runner as sr
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.decide_after_seal(local_seal_ok=False, archive_report=None)
        self.assertIn("local_seal_failed", str(caught.exception))
        self.assertIn("nothing was sealed", str(caught.exception))

    def test_an_unknown_code_refuses_differently(self):
        """"Undecided" and "unheard of" are different states and an
        operator needs different actions."""
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_seal_failure("brand_new_code")
        self.assertIn("in neither table", str(caught.exception))

    def test_the_ruling_that_emptied_the_undecided_set_is_recorded(self):
        """The predecessor of this test said: "If it ever empties, it
        should be because someone RULED, and the ruling should be recorded
        -- not because the entries were quietly moved into the mapped
        table." It emptied. This is that check, and note the entries did
        NOT move into the mapped table: they moved to a router."""
        from pathlib import Path
        record = (Path(__file__).resolve().parents[1] / "ops"
                  / "BUILDER_DECISIONS_2026-08-29.md")
        self.assertTrue(record.exists(), "BD-1 is not written down")
        text = record.read_text(encoding="utf-8")
        for code in dsc.ROUTER_B_SEAL_CODES:
            with self.subTest(code=code):
                self.assertIn(code, text)
        self.assertIn("archive_policy_a", text)     # the cited precedent

    def test_the_ruling_is_labelled_a_BUILDER_decision(self):
        """The distinction that matters more than the ruling itself. A
        builder decision filed among owner decisions would be using "Aaron
        said decide it yourself" to cover something he never delegated."""
        from pathlib import Path
        ops = Path(__file__).resolve().parents[1] / "ops"
        builder = (ops / "BUILDER_DECISIONS_2026-08-29.md").read_text(
            encoding="utf-8")
        self.assertIn("不是 owner 裁定", builder)
        owner = (ops / "OWNER_DECISIONS_2026-08-29.md").read_text(
            encoding="utf-8")
        self.assertNotIn("BD-1", owner,
                         "a builder ruling has leaked into the owner "
                         "decision record")

    def test_the_cited_precedent_is_real_and_executed(self):
        """BD-1 rests on `archive_policy_a` having been found to create a
        real contradiction. If that test disappeared, the ruling would be
        resting on a citation to nothing."""
        from pathlib import Path
        facts = (Path(__file__).resolve().parents[1] / "tests"
                 / "test_n09_r3_design_facts.py").read_text(encoding="utf-8")
        self.assertIn("test_routing_it_as_an_ordinary_gate_contradicts_"
                      "policy_a", facts)

    def test_router_b_entries_carry_a_reason_not_a_question(self):
        self.assertEqual(2, len(dsc.ROUTER_B_SEAL_CODES))
        for code, reason in dsc.ROUTER_B_SEAL_CODES.items():
            with self.subTest(code=code):
                self.assertGreater(len(reason), 60)
                self.assertNotIn("?", reason,
                                 "%s still reads as an open question" % code)


if __name__ == "__main__":
    unittest.main()
