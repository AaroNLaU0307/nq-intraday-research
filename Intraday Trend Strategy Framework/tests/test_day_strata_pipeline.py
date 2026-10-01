"""C_BUILD's work: every refusal reaches the gate that names it.

The pipeline returns an OUTCOME rather than raising, and that is the point
under test. A gate has to report its own refusal — if C_BUILD failures
arrived as whatever exception escaped, the F1/F2 event would carry the
wrong gate name and the registry would record the wrong defect.

C_BUILD_1's assertion (R3 §1) is held here rather than described: the exact
set of supplement bytes under the output root must be byte-identical across
the three gates AND empty. Both halves are separate claims and both are
tested — "unchanged" alone holds over a root that already had bytes in it,
"empty" alone holds over a root something wrote to and then cleaned up.

NOTHING HERE RUNS A SUPPLEMENT. The authority and prepared input are stand-
ins, the universe is a stub, and the two ruled S0 producers are patched.
The production entry stays refused at `assert_real_run_allowed`.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from itsf.mc import day_strata_pipeline as pipe
from itsf.mc import day_strata_rows as dsr
from itsf.mc import supplement_production as sp
from itsf.s0 import dataset as s0

DAYS = ("2024-01-02", "2024-01-03", "2024-01-04")


class _Vol:
    def __init__(self, label_of):
        self.label_of = label_of


def _patched(label_of=None, stratum_of=None):
    label_of = label_of or {d: "T1" for d in DAYS}
    stratum_of = stratum_of or {d: "none" for d in DAYS}
    return mock.patch.multiple(
        s0,
        build_vol20_regime_mapping_from_universe=mock.Mock(
            return_value=_Vol(label_of)),
        build_event_stratum_map=mock.Mock(
            return_value={"stratum_of": stratum_of}),
    )


def _run(label_of=None, stratum_of=None, product=None, builder_raises=None,
         runs_root=None, archive_root=None, days=DAYS):
    build = (mock.Mock(side_effect=builder_raises) if builder_raises
             else mock.Mock(return_value=product if product is not None
                            else _a_product(days)))
    with _patched(label_of, stratum_of), \
            mock.patch.object(sp, "build_supplement_from_authority", build):
        return pipe.run_c_build(
            authority=object(), prepared=object(), universe=object(),
            vol_method="ruled", flag_by_date={}, event_na_mapping="ruled",
            expected_day_set=frozenset(days),
            runs_root=runs_root, archive_root=archive_root)


def _a_product(days=DAYS, digest=None):
    """A product carrying the digest the pipeline will recompute."""
    from itsf.mc import day_strata_supplement as ds
    rows = [{"trade_date": d, "year": 2024, "vol_stratum": "T1",
             "event_stratum": "none"} for d in sorted(days)]
    return {"rows": rows,
            "rows_digest": digest or ds.canonical_rows_digest(rows)}


class TestEveryRefusalReachesItsGate(unittest.TestCase):

    def test_a_day_universe_refusal_reaches_day_set_exact(self):
        outcome = _run(label_of={d: "T1" for d in DAYS[:-1]})
        self.assertIsNotNone(outcome.failure)
        self.assertEqual("day_set_exact", outcome.failure.gate)
        self.assertEqual("vol_day_missing", outcome.failure.code)

    def test_a_row_refusal_reaches_row_schema_blind(self):
        outcome = _run(label_of=dict({d: "T1" for d in DAYS},
                                     **{"2024-01-03": "T9"}))
        self.assertEqual("row_schema_blind", outcome.failure.gate)

    def test_a_SCHEMA_refusal_from_the_builder_reaches_row_schema_blind(self):
        """The supplement-object validators, reached through the builder.
        These genuinely are row/schema refusals."""
        from itsf.mc.day_strata_supplement import SupplementError
        outcome = _run(builder_raises=SupplementError(
            "supplement_row_schema", "row 0: missing=['year']"))
        self.assertEqual("row_schema_blind", outcome.failure.gate)
        self.assertEqual("C_BUILD", outcome.failure.stage)
        self.assertIn("year", outcome.failure.detail)

    def test_an_AUTHORITY_refusal_reaches_B_DERIVE_not_row_schema_blind(self):
        """THE CORRECTION, 2026-08-29, found by the end-to-end rehearsal.

        This test used to read `test_a_builder_refusal_reaches_row_schema_
        blind`, on the docstring "the builder validates the rows it was
        handed, so its refusals are row-schema refusals by construction".
        `day_strata_dryrun` walked the chain for the first time and showed
        that false: the builder validates the AUTHORITY too, and a
        `production_authority_test_only` refusal was being filed as a
        row-schema defect at the wrong stage.

        The stage and the gate are what an F1/F2 row carries, so the old
        behaviour put a wrong defect on record under a name nobody ruled."""
        from itsf.mc.supplement_production import SupplementProductionError
        outcome = _run(builder_raises=SupplementProductionError(
            "production_authority_test_only",
            "a test_only authority may never build a production supplement"))
        self.assertEqual("B_DERIVE", outcome.failure.stage)
        self.assertEqual("custody_authority_production", outcome.failure.gate)

    def test_a_CALLER_BUG_raises_instead_of_becoming_a_failure_row(self):
        """A forbidden keyword is a programming error. Filing it as a gate
        failure would record a failed run that never happened."""
        from itsf.mc.day_strata_classify import ClassificationError
        from itsf.mc.supplement_production import SupplementProductionError
        with self.assertRaises(ClassificationError) as caught:
            _run(builder_raises=SupplementProductionError(
                "production_decisive_argument_supplied", "binding"))
        self.assertIn("CALLER BUG", str(caught.exception))

    def test_an_UNANTICIPATED_exception_propagates(self):
        """Better a real traceback than a guessed gate. An exception nobody
        mapped is a defect in the code, not a refusal by the run."""
        with self.assertRaises(ValueError):
            _run(builder_raises=ValueError("nobody planned for this"))

    def test_a_digest_mismatch_reaches_rows_digest_recompute(self):
        outcome = _run(product=_a_product(digest="0" * 64))
        self.assertEqual("rows_digest_recompute", outcome.failure.gate)
        self.assertEqual("rows_digest_mismatch", outcome.failure.code)

    def test_belongs_to_answers_for_exactly_one_gate(self):
        """The whole of a gate's body, once the runner's freeze lifts."""
        outcome = _run(label_of={d: "T1" for d in DAYS[:-1]})
        self.assertIsNotNone(outcome.belongs_to("day_set_exact"))
        self.assertIsNone(outcome.belongs_to("row_schema_blind"))
        self.assertIsNone(outcome.belongs_to("rows_digest_recompute"))

    def test_a_clean_run_belongs_to_no_gate(self):
        outcome = _run()
        self.assertIsNone(outcome.failure)
        for gate in ("row_schema_blind", "day_set_exact",
                     "rows_digest_recompute"):
            with self.subTest(gate=gate):
                self.assertIsNone(outcome.belongs_to(gate))

    def test_a_refusal_carries_no_product(self):
        """Never both. A product alongside a failure would let a caller
        use the product and ignore the refusal."""
        outcome = _run(label_of={d: "T1" for d in DAYS[:-1]})
        self.assertIsNone(outcome.product)


class TestCBuild1ExactSet(unittest.TestCase):
    """R3 §1: byte-identical across the gates, AND empty. Two claims."""

    def _root(self, *files):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name, body in files:
            (root / name).write_bytes(body)
        return root

    def test_an_empty_unchanged_root_passes(self):
        outcome = _run(runs_root=self._root(), archive_root=self._root())
        self.assertIsNone(outcome.failure)

    def test_a_root_that_already_holds_bytes_refuses(self):
        """The "empty" half. Unchanged alone would hold here."""
        root = self._root(("leftover.json", b"{}"))
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _run(runs_root=root)
        self.assertEqual("c_build_1_not_empty", caught.exception.code)

    def test_a_write_during_the_gates_refuses(self):
        """The "unchanged" half. Empty-at-the-end alone would hold if
        something wrote and then cleaned up, so the comparison is of the
        two snapshots, not of the final state."""
        root = self._root()
        before = (("x.json", 2, "d" * 64),)
        with mock.patch.object(pipe, "supplement_bytes_snapshot",
                               side_effect=[before, (), (), ()]):
            with self.assertRaises(dsr.DayStrataRowsError) as caught:
                _run(runs_root=root)
        self.assertEqual("c_build_1_bytes_moved", caught.exception.code)

    def test_the_archive_root_is_checked_too(self):
        """Zero archive attempts — the second half of C_BUILD_1's
        assertion, and a separate root."""
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            _run(archive_root=self._root(("archived.json", b"{}")))
        self.assertIn("archive_root", caught.exception.detail)

    def test_a_missing_root_snapshots_as_empty(self):
        self.assertEqual((), pipe.supplement_bytes_snapshot(
            Path("C:/no/such/root/anywhere")))

    def test_a_root_that_is_a_file_refuses_rather_than_reading_empty(self):
        """"I could not look" must never read as "nothing is there" — the
        collapse the sister repository spent five rounds on."""
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        target = Path(tmp.name) / "afile"
        target.write_bytes(b"x")
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            pipe.supplement_bytes_snapshot(target)
        self.assertEqual("snapshot_root_not_a_directory",
                         caught.exception.code)

    def test_the_snapshot_universe_is_the_directory(self):
        """Nothing is declared and then looked for. A file nobody expected
        changes the snapshot instead of being invisible to it."""
        root = self._root(("a.json", b"1"), ("b.json", b"22"))
        snap = pipe.supplement_bytes_snapshot(root)
        self.assertEqual(2, len(snap))
        self.assertEqual({"a.json", "b.json"}, {n for n, _s, _d in snap})
        (root / "c.json").write_bytes(b"333")
        self.assertEqual(3, len(pipe.supplement_bytes_snapshot(root)))


class TestTheCleanPath(unittest.TestCase):

    def test_rows_and_product_come_back(self):
        outcome = _run()
        self.assertEqual(len(DAYS), len(outcome.rows))
        self.assertIsNotNone(outcome.product)

    def test_the_rows_are_the_ones_the_builder_was_handed(self):
        """If the pipeline recomputed the digest over different rows than
        the builder saw, the comparison would prove nothing."""
        build = mock.Mock(return_value=_a_product())
        with _patched(), mock.patch.object(
                sp, "build_supplement_from_authority", build):
            outcome = pipe.run_c_build(
                authority=object(), prepared=object(), universe=object(),
                vol_method="ruled", flag_by_date={},
                event_na_mapping="ruled",
                expected_day_set=frozenset(DAYS))
        handed = build.call_args[0][2]
        self.assertEqual(list(outcome.rows), list(handed))




class TestCBuild3AfterTheArchiveAttempt(unittest.TestCase):
    """R3 §1's third checkpoint asserts something DIFFERENT from the first
    two: the attempt has already happened, and what must hold is that the
    local seal is unchanged and nothing archived was lost.

    Both are RECOMPUTATIONS. §11.3: a field named `local_seal_immutable`
    proves nothing on its own, and reading it instead of recomputing is
    exactly how a false claim survives."""

    def _sealed(self, body=b'{"sealed": true}'):
        import hashlib
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "supplement.json"
        path.write_bytes(body)
        return path, hashlib.sha256(body).hexdigest()

    def test_an_untouched_seal_and_intact_archive_pass(self):
        path, digest = self._sealed()
        archive = (("a.json", 2, "d" * 64),)
        outcome = pipe.run_c_build_3(sealed_path=path,
                                     local_seal_sha256=digest,
                                     archive_before=archive,
                                     archive_after=archive)
        self.assertIsNone(outcome.failure)

    def test_a_mutated_seal_refuses(self):
        path, digest = self._sealed()
        path.write_bytes(b'{"sealed": false}')
        outcome = pipe.run_c_build_3(sealed_path=path,
                                     local_seal_sha256=digest,
                                     archive_before=(), archive_after=())
        self.assertEqual("archive_policy_a", outcome.failure.gate)
        self.assertEqual("local_seal_mutated", outcome.failure.code)

    def test_a_vanished_seal_refuses(self):
        path, digest = self._sealed()
        path.unlink()
        outcome = pipe.run_c_build_3(sealed_path=path,
                                     local_seal_sha256=digest,
                                     archive_before=(), archive_after=())
        self.assertEqual("local_seal_absent", outcome.failure.code)

    def test_a_deleted_archived_file_refuses(self):
        path, digest = self._sealed()
        outcome = pipe.run_c_build_3(
            sealed_path=path, local_seal_sha256=digest,
            archive_before=(("a.json", 2, "d" * 64),), archive_after=())
        self.assertEqual("archived_bytes_deleted", outcome.failure.code)

    def test_a_changed_archived_file_refuses_too(self):
        """Present but different is a loss of the bytes that were there."""
        path, digest = self._sealed()
        outcome = pipe.run_c_build_3(
            sealed_path=path, local_seal_sha256=digest,
            archive_before=(("a.json", 2, "d" * 64),),
            archive_after=(("a.json", 2, "e" * 64),))
        self.assertEqual("archived_bytes_deleted", outcome.failure.code)

    def test_ADDING_archived_bytes_is_fine(self):
        """The check is one-directional on purpose. Archiving ADDS, so a
        symmetric comparison would refuse every successful archive — and a
        guard that refuses the success case gets deleted, not fixed."""
        path, digest = self._sealed()
        outcome = pipe.run_c_build_3(
            sealed_path=path, local_seal_sha256=digest,
            archive_before=(("a.json", 2, "d" * 64),),
            archive_after=(("a.json", 2, "d" * 64),
                           ("b.json", 3, "e" * 64)))
        self.assertIsNone(outcome.failure)

    def test_it_is_a_recompute_not_a_flag_read(self):
        """The property §11.3 names. A caller passing a digest that does
        not match the bytes must be refused, however confident it is."""
        path, _digest = self._sealed()
        outcome = pipe.run_c_build_3(sealed_path=path,
                                     local_seal_sha256="f" * 64,
                                     archive_before=(), archive_after=())
        self.assertEqual("local_seal_mutated", outcome.failure.code)



class TestTheDigestAccessorReachesEveryCarrier(unittest.TestCase):
    """THE COVERAGE THAT WAS MISSING, and its absence is why a wider-than-
    true docstring survived. `_declared_digest` said "however it carries it"
    while every test here drove it with a plain mapping -- so the real
    `SupplementProduct`, which keeps its fields in `.payload`, refused with
    `product_carries_no_rows_digest` the first time the chain composed one.

    Each carrier below is a shape something actually builds."""

    def test_a_plain_mapping(self):
        self.assertEqual("d" * 64, pipe._declared_digest({"rows_digest":
                                                          "d" * 64}))

    def test_an_attribute_carrier(self):
        class P:
            rows_digest = "e" * 64
        self.assertEqual("e" * 64, pipe._declared_digest(P()))

    def test_the_real_production_product(self):
        """The one that was missing. Built by the real factory, not by a
        stand-in, so a change to where SupplementProduct keeps its fields
        fails here rather than at the end of a chain."""
        from itsf.mc import supplement_production as sp

        payload = {"rows_digest": "f" * 64}
        product = sp.SupplementProduct(payload)
        self.assertEqual("f" * 64, pipe._declared_digest(product))

    def test_a_product_carrying_none_of_them_still_refuses(self):
        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            pipe._declared_digest(object())
        self.assertEqual("product_carries_no_rows_digest",
                         caught.exception.code)

if __name__ == "__main__":
    unittest.main()
