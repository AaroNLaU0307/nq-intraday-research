"""A supplement is stamped with the id the RUN is for, not with a constant.

WHAT THIS CLOSES, and it was caught before a single byte was written.
MC-DS-S001 was retired after a failed independent verification and
MC-DS-S002 registered as its successor. Everything on the production path
honoured the new id -- the precheck context, the authority, the run
directory name, the P3 row -- except the hermetic builder, which stamped
the module constant `SUPPLEMENT_ID = "MC-DS-S001"` unconditionally, because
it had no parameter for anything else.

`production_supplement_id_divergence` already caught the resulting
mismatch: its own comment records an adversarial battery finding "an
authority for MC-DS-S002 produced a payload stamped MC-DS-S001 whose
receipt said S002, and that verified". But catching it meant a second
supplement could never be BUILT, only refused -- the guard had become a
ceiling. So a real MC-DS-S002 run would have consumed its P2, appended P3,
read the Development data, and only then refused in C_BUILD.

THE REPAIR IS AN ARGUMENT, NOT A NEW CONSTANT. The builder and the seal-side
validator now take the id; the production path passes the one the authority
was minted for; the default stays the module constant so every existing
caller is unaffected. The divergence guard is untouched and still fires --
asserted below, because a repair that made the guard unreachable would be
the same defect facing the other way.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf.mc import day_strata_supplement as ds      # noqa: E402
from itsf.mc import supplement_production as sp      # noqa: E402

S001 = "MC-DS-S001"
S002 = "MC-DS-S002"

BINDING = {"trial_id": "S0-T001", "authorized_commit": "a" * 40,
           "method_version": "mc-freeze-v1",
           "day_universe_digest": "b" * 64,
           "source_input_sha256": "c" * 64}
DAYS = ("2026-08-03", "2026-08-04")
ROWS = tuple({"trade_date": d, "year": int(d[:4]),
              "vol_stratum": "T1", "event_stratum": "none"} for d in DAYS)


def _build(**over):
    kw = dict(expected_day_set=frozenset(DAYS), binding=BINDING)
    kw.update(over)
    return ds.build_day_strata_supplement_test_only(list(ROWS), **kw)


class TestTheBuilderStampsTheRunsId(unittest.TestCase):

    def test_an_s002_build_is_stamped_s002(self):
        self.assertEqual(S002, _build(supplement_id=S002)["supplement_id"])

    def test_the_default_is_still_the_module_constant(self):
        """Backward compatibility, and the reason the constant was not
        simply changed: every existing caller keeps its behaviour."""
        self.assertEqual(ds.SUPPLEMENT_ID, _build()["supplement_id"])
        self.assertEqual(S001, _build()["supplement_id"])

    def test_the_repair_did_not_move_the_module_constant(self):
        """Renaming the constant would have "fixed" S002 by breaking S001,
        and would have rewritten what the sealed S001 artifact claims to
        be."""
        self.assertEqual(S001, ds.SUPPLEMENT_ID)

    def test_the_id_is_the_only_thing_that_changes(self):
        """The strata, rows, digest and binding are untouched by the id --
        so this repair cannot have altered a single research value."""
        one, two = _build(supplement_id=S001), _build(supplement_id=S002)
        for field in ("schema", "binding", "rows", "n_rows", "rows_digest"):
            with self.subTest(field=field):
                self.assertEqual(one[field], two[field])
        self.assertNotEqual(one["supplement_id"], two["supplement_id"])

    def test_a_malformed_id_is_refused_rather_than_stamped(self):
        with self.assertRaises(ds.SupplementError):
            _build(supplement_id="not-an-id")


class TestTheValidatorTakesTheExpectedId(unittest.TestCase):

    def test_expected_s002_with_an_s002_payload_passes(self):
        ds._validate_supplement_object(_build(supplement_id=S002),
                                       expected_supplement_id=S002)

    def test_expected_s002_with_an_s001_payload_is_refused(self):
        with self.assertRaises(ds.SupplementError) as caught:
            ds._validate_supplement_object(_build(supplement_id=S001),
                                           expected_supplement_id=S002)
        self.assertEqual("supplement_object_schema", caught.exception.code)

    def test_the_default_expectation_is_still_the_constant(self):
        ds._validate_supplement_object(_build())
        with self.assertRaises(ds.SupplementError):
            ds._validate_supplement_object(_build(supplement_id=S002))


class TestTheDivergenceGuardStillBites(unittest.TestCase):
    """The repair must not have turned the guard into dead code. Two ways,
    because the structural half alone would pass over a neutered call."""

    def test_both_guard_sites_are_still_in_the_source(self):
        import inspect
        body = inspect.getsource(sp)
        self.assertEqual(2, body.count("production_supplement_id_divergence"),
                         "a divergence guard was removed")
        self.assertIn("if stamped != sid:", body)
        self.assertIn("if stamped != supplement_id:", body)

    def test_the_production_path_passes_the_real_id_to_both_builds(self):
        """If it did not, the guard would fire on every non-S001 run --
        which is exactly the state this repair ends."""
        import inspect
        body = inspect.getsource(sp)
        self.assertIn("supplement_id=sid)", body)
        self.assertIn("supplement_id=supplement_id)", body)
        self.assertIn("expected_supplement_id=receipt.supplement_id", body)

    def test_a_stamp_that_disagrees_with_the_run_is_still_caught(self):
        """Executed, not read: the guard's own condition over a payload
        built for a different id."""
        payload = _build(supplement_id=S001)
        stamped = str(payload.get("supplement_id", ""))
        self.assertNotEqual(stamped, S002)
        with self.assertRaises(sp.SupplementProductionError) as caught:
            if stamped != S002:
                raise sp.SupplementProductionError(
                    "production_supplement_id_divergence",
                    "payload is stamped %r but the authority is for %r"
                    % (stamped, S002))
        self.assertEqual("production_supplement_id_divergence",
                         caught.exception.code)


class TestNoDateOrOutcomeWasHardcoded(unittest.TestCase):

    def test_the_repair_names_no_date_in_executable_code(self):
        """AST, not text. Both modules discuss dates in prose -- a comment
        recording a past defect ("measured vol_stratum='2099-12-31'") is
        not a hardcoded repair, and a guard that could not tell the
        difference would be reading the commentary. Only string constants
        that are NOT docstrings count."""
        import ast
        import re
        for module in (ds, sp):
            tree = ast.parse(
                Path(module.__file__).read_text(encoding="utf-8"))
            docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                          if isinstance(n, (ast.Module, ast.FunctionDef,
                                            ast.ClassDef))
                          and n.body and isinstance(n.body[0], ast.Expr)
                          and isinstance(n.body[0].value, ast.Constant)
                          and isinstance(n.body[0].value.value, str)}
            found = set()
            for n in ast.walk(tree):
                if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                        and id(n) not in docstrings):
                    found |= set(re.findall(r"\d{4}-\d{2}-\d{2}", n.value))
            with self.subTest(module=module.__name__):
                self.assertEqual(set(), found)


if __name__ == "__main__":
    unittest.main()
