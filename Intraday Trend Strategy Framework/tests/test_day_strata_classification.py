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
    """Every code that can escape `build_supplement_from_authority`,
    TRANSITIVELY.

    WIDENED 2026-08-29. The first version scanned only raise sites inside
    the function body, and `production_payload_unsupported_type` -- raised
    one level down in `_freeze_value` -- escaped both the table and this
    test. The test claimed "every builder refusal is mapped" while looking
    at a fraction of them: the guard was narrower than its claim, which is
    the defect this repository keeps producing.

    Following calls within the module is still not a proof of reachability
    (a call inside a branch that can never be taken is counted), and that
    is the safe direction: over-counting forces a code into the tables,
    under-counting lets one out."""
    root = Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"
    tree = ast.parse(io.open(root / "supplement_production.py",
                             encoding="utf-8").read())
    fns = {n.name: n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef)}

    def walk(name, seen):
        if name in seen or name not in fns:
            return set()
        seen.add(name)
        codes = set()
        for node in ast.walk(fns[name]):
            if (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                    and node.exc.args
                    and isinstance(node.exc.args[0], ast.Constant)):
                codes.add(node.exc.args[0].value)
            if isinstance(node, ast.Call):
                callee = getattr(node.func, "id", None)
                if callee and callee != name:
                    codes |= walk(callee, seen)
        return codes

    return walk("build_supplement_from_authority", set())


class TestTheBuilderTableIsDerivedToo(unittest.TestCase):
    """Added 2026-08-29 after the end-to-end rehearsal found a B_DERIVE
    defect being filed under a C_BUILD gate."""

    def test_every_builder_code_is_mapped_or_marked_a_caller_bug(self):
        known = (set(dsc.STAGE_GATE_OF_BUILDER_CODE)
                 | set(dsc.CALLER_ERROR_BUILDER_CODES)
                 | set(dsc.UNMAPPED_BUILDER_CODES))
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
                        | set(dsc.CALLER_ERROR_BUILDER_CODES)
                        | set(dsc.UNMAPPED_BUILDER_CODES))
                       - _builder_codes_from_source())
        self.assertEqual([], stale, "stale builder entries: %s" % stale)

    def test_the_three_builder_tables_do_not_overlap(self):
        """A code in two tables would take whichever branch was written
        first, and the other table would be a lie nobody could see."""
        tables = {"mapped": set(dsc.STAGE_GATE_OF_BUILDER_CODE),
                  "caller_bug": set(dsc.CALLER_ERROR_BUILDER_CODES),
                  "unmapped": set(dsc.UNMAPPED_BUILDER_CODES)}
        for a in tables:
            for b in tables:
                if a < b:
                    with self.subTest(pair=(a, b)):
                        self.assertEqual([], sorted(tables[a] & tables[b]))

    def test_the_transitive_scan_reaches_deeper_than_the_body(self):
        """The correction itself, executed. `production_payload_unsupported_
        type` is raised in `_freeze_value`, one level below the builder, and
        a body-only scan cannot see it."""
        found = _builder_codes_from_source()
        self.assertIn("production_payload_unsupported_type", found)

    def test_the_payload_type_code_now_maps_to_C_BUILD_row_schema(self):
        """RULED 2026-08-30 by the Fable seat, on a data-flow fact builder
        had skipped: inside the builder the only frozen thing is the ROWS,
        so the offending key or value can only have come from one."""
        self.assertEqual(("C_BUILD", "row_schema_blind"),
                         dsc.classify_builder_failure(
                             "production_payload_unsupported_type"))

    def test_the_SEAL_side_still_refuses_the_same_code(self):
        """The scope split is the load-bearing half of that ruling.
        `freeze_payload` freezes the WHOLE payload including the binding,
        so on the seal path the source really is ambiguous and the code
        must not inherit the builder's answer."""
        with self.assertRaises(dsc.ClassificationError) as caught:
            dsc.classify_seal_failure("production_payload_unsupported_type")
        # It is now RECORDED as unmapped rather than merely absent -- BD-6
        # widened the derivation and every surfaced code must be in some
        # table. The ruling is unchanged and is what this asserts: the seal
        # side still refuses, and the reason names the scope split.
        self.assertIn("UNMAPPED", str(caught.exception))
        self.assertIn("freeze_payload", str(caught.exception))
        self.assertNotIn("production_payload_unsupported_type",
                         dsc.STAGE_GATE_OF_SEAL_CODE)

    def test_the_unmapped_MECHANISM_survives_the_table_emptying(self):
        """The table is empty now. Emptying it must not delete the branch:
        the next code that reaches a caller with no gate has to land
        somewhere loud rather than in a gate someone picked."""
        self.assertEqual({}, dsc.UNMAPPED_BUILDER_CODES)
        dsc.UNMAPPED_BUILDER_CODES["synthetic_probe"] = (
            "a question long enough to look like a real one, injected by "
            "this test to prove the refusal branch still exists")
        try:
            with self.assertRaises(dsc.ClassificationError) as caught:
                dsc.classify_builder_failure("synthetic_probe")
            self.assertIn("no ratified gate names it", str(caught.exception))
        finally:
            dsc.UNMAPPED_BUILDER_CODES.pop("synthetic_probe")



def _raised_in(fn):
    for node in ast.walk(fn):
        if (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                and node.exc.args
                and isinstance(node.exc.args[0], ast.Constant)):
            yield node.exc.args[0].value


def _transitive_codes(tree, entry):
    """Codes reachable from `entry`, FOLLOWING CALLS within the module."""
    fns = {n.name: n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef)}

    def walk(name, seen):
        if name in seen or name not in fns:
            return set()
        seen.add(name)
        codes = set(_raised_in(fns[name]))
        for node in ast.walk(fns[name]):
            if isinstance(node, ast.Call):
                callee = getattr(node.func, "id", None)
                if callee and callee != name:
                    codes |= walk(callee, seen)
        return codes

    return walk(entry, set())


def _seal_codes_from_source():
    """Every literal code the seal step can refuse with, derived
    TRANSITIVELY.

    WIDENED 2026-09-02 (BD-3), and it is the SAME widening the builder
    derivation got on 2026-08-29. This version scanned only the body of
    `seal_supplement_production`, so ten codes raised one level down --
    `production_product_type` out of `_product_receipt` among them --
    escaped both the seal tables and this test. The test claimed "every
    seal refusal is mapped" while looking at seven of seventeen: the guard
    was narrower than its claim, which is the shape this repository keeps
    producing.

    NOT found by reading. Composing the chain end to end handed a real
    caller a `ClassificationError` on `production_product_type`, and the
    scan was widened to ask how many more there were.

    Over-counting is the safe direction here, exactly as it is for the
    builder: a call inside a branch that can never be taken still forces a
    code into the tables, while under-counting lets one out."""
    root = Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"
    prod = ast.parse(io.open(root / "supplement_production.py",
                             encoding="utf-8").read())
    codes = _transitive_codes(prod, "seal_supplement_production")
    runner = ast.parse(io.open(root / "supplement_runner.py",
                               encoding="utf-8").read())
    codes |= _transitive_codes(runner, "resolve_partial")
    return {c for c in codes if isinstance(c, str)}


class TestTheSealTableIsDerivedToo(unittest.TestCase):

    def _known(self):
        return (set(dsc.STAGE_GATE_OF_SEAL_CODE)
                | set(dsc.ROUTER_B_SEAL_CODES)
                | set(dsc.CALLER_ERROR_SEAL_CODES)
                | set(dsc.UNMAPPED_SEAL_CODES))

    def test_every_seal_code_is_mapped_or_recorded_as_undecided(self):
        missing = sorted(_seal_codes_from_source() - self._known())
        self.assertEqual(
            [], missing,
            "these seal refusals are in no seal table: %s\nAdd each to "
            "STAGE_GATE_OF_SEAL_CODE with the raise site that justifies the "
            "gate, to ROUTER_B_SEAL_CODES with the reason no gate names it, "
            "to CALLER_ERROR_SEAL_CODES if it is a programming error, or to "
            "UNMAPPED_SEAL_CODES with the open question." % missing)

    def test_the_derivation_actually_follows_calls(self):
        """The half that makes the check above worth anything. Before the
        BD-3 widening this returned seven codes and missed ten, including
        one a real caller then hit."""
        found = _seal_codes_from_source()
        self.assertIn("production_product_type", found,
                      "raised in `_product_receipt`, one level below the "
                      "seal -- if this is absent the scan stopped at the "
                      "function body again")
        self.assertGreaterEqual(len(found), 17)

    def test_no_seal_table_names_a_code_the_seal_cannot_raise(self):
        """The other direction: a table entry for a code nobody raises is a
        rule about nothing, and it rots silently."""
        stale = sorted(self._known() - _seal_codes_from_source())
        self.assertEqual([], stale)

    def test_the_four_tables_do_not_overlap(self):
        """A code in two tables would have two answers, and the one that won
        would be whichever branch was written first."""
        tables = {
            "STAGE_GATE_OF_SEAL_CODE": set(dsc.STAGE_GATE_OF_SEAL_CODE),
            "ROUTER_B_SEAL_CODES": set(dsc.ROUTER_B_SEAL_CODES),
            "CALLER_ERROR_SEAL_CODES": set(dsc.CALLER_ERROR_SEAL_CODES),
            "UNMAPPED_SEAL_CODES": set(dsc.UNMAPPED_SEAL_CODES),
        }
        names = sorted(tables)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                self.assertEqual(sorted(tables[a] & tables[b]), [],
                                 "%s and %s share a code" % (a, b))

    def test_each_bucket_refuses_in_its_own_words(self):
        """One message for all of them would tell a caller to "add it
        somewhere" without saying which question is open."""
        with self.assertRaises(dsc.ClassificationError) as caller:
            dsc.classify_seal_failure("production_product_type")
        self.assertIn("CALLER BUG", str(caller.exception))

        with self.assertRaises(dsc.ClassificationError) as unmapped:
            dsc.classify_seal_failure("production_rebuild_refused")
        self.assertIn("UNMAPPED", str(unmapped.exception))
        self.assertIn("inner", str(unmapped.exception))

        with self.assertRaises(dsc.ClassificationError) as unknown:
            dsc.classify_seal_failure("production_never_heard_of_it")
        self.assertIn("in no seal table", str(unknown.exception))

    def test_the_router_refuses_them_too_rather_than_picking_one(self):
        for code in ("production_product_type", "production_rebuild_refused",
                     "production_never_heard_of_it"):
            with self.subTest(code=code):
                with self.assertRaises(dsc.ClassificationError):
                    dsc.seal_failure_router(code)

    def test_no_builder_answer_was_carried_over_to_the_seal_side(self):
        """The first BD-6 draft gave three shared raise sites the builder's
        answers. `test_the_SEAL_side_still_refuses_the_same_code` refused
        that at once and was right: `freeze_payload` widens the seal path's
        scope, so one shared site genuinely means different things on the
        two paths. Since one was wrong, none were taken."""
        for code in ("production_authority_type",
                     "production_payload_unsupported_type",
                     "production_supplement_id_divergence"):
            with self.subTest(code=code):
                self.assertIn(code, dsc.STAGE_GATE_OF_BUILDER_CODE)
                self.assertNotIn(code, dsc.STAGE_GATE_OF_SEAL_CODE)
                self.assertIn(code, dsc.UNMAPPED_SEAL_CODES)

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
        self.assertIn("in no seal table", str(caught.exception))

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
