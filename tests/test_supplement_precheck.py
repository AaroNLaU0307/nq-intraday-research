"""`supplement_precheck` measures, and it writes nothing while doing it.

TWO CLAIMS, AND THE SECOND IS THE ONE THAT MATTERS. The module says it reads
the registry, git, two flag files and two directory roots, and that it creates
nothing and appends nothing. A docstring saying so is a claim; today has been
one long lesson in the distance between those. So the write claim is proved
the way this repository proves that kind of thing now -- snapshot the governed
directories before and after, and require every blob present before to still
be present after, with nothing added.

THE OTHER CLAIM is that it measures rather than assumes. The assembler's first
version called a guards function that does not exist, swallowed the
AttributeError into a "gap", left frozen_hashes_ok as None, and the gate
refused -- which read exactly like "a frozen file has been modified". It was
not; seven hashes checked by hand said so. The tests below therefore assert
that the fields ARE measured, not merely that the report comes back.
"""

import hashlib
import sys
import unittest
from pathlib import Path

from itsf import contracts as _c
from itsf import guards as _guards
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_precheck as pc

GOVERNED = (Path(_c.RULED_RUNS_ROOT), Path(_c.RULED_ARCHIVE_ROOT))


def _blobs(roots):
    """(name, sha256) for every file under each root. The DIRECTORY is the
    universe -- the same shape the C_BUILD_1 assertion uses."""
    out = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                out.append((str(path),
                            hashlib.sha256(path.read_bytes()).hexdigest()))
    return sorted(out)


class TestItWritesNothing(unittest.TestCase):
    """The safety claim, measured rather than read."""

    def test_running_the_precheck_changes_no_governed_byte(self):
        before = _blobs(GOVERNED)
        pc.run_precheck()
        after = _blobs(GOVERNED)
        self.assertEqual(before, after,
                         "the precheck changed a governed byte; it is "
                         "supposed to read and report, nothing else")

    def test_it_creates_no_run_directory(self):
        """It supplies a UTC stamp so `supplement_subtree_absent` can plan a
        directory NAME. Planning a name must not bring the directory into
        existence."""
        before = {p for root in GOVERNED if root.exists()
                  for p in root.rglob("*")}
        report = pc.run_precheck()
        after = {p for root in GOVERNED if root.exists()
                 for p in root.rglob("*")}
        self.assertEqual(before, after)
        self.assertTrue(report.results)

    def test_the_registry_is_unchanged(self):
        from itsf.mc import registry_boundary as rb
        path = rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        pc.run_precheck()
        self.assertEqual(before,
                         hashlib.sha256(path.read_bytes()).hexdigest())


class TestItMeasuresRatherThanAssumes(unittest.TestCase):

    def test_every_context_field_a_gate_reads_is_populated(self):
        ctx, gaps = pc.assemble_precheck_context()
        self.assertEqual((), gaps, "a field could not be measured: %s" % (gaps,))
        self.assertEqual(40, len(ctx.head_commit), ctx.head_commit)
        self.assertTrue(ctx.registry_text.strip())
        self.assertIsNotNone(ctx.runs_root)
        self.assertIsNotNone(ctx.archive_root)
        self.assertIsNotNone(ctx.chain)
        self.assertTrue(ctx.utc_stamp, "no stamp -> subtree gate cannot plan")

    def test_frozen_hashes_is_a_REAL_measurement(self):
        """None would mean 'not measured', and the gate refuses on it -- the
        failure that read like a tampered file. True or False both mean
        somebody looked."""
        ctx, _gaps = pc.assemble_precheck_context()
        self.assertIn(ctx.frozen_hashes_ok, (True, False))

    def test_it_agrees_with_the_guard_it_is_reporting_on(self):
        """Not a second implementation of the check -- the SAME function,
        asked directly. If these disagreed, one of them would be a mirror."""
        ctx, _gaps = pc.assemble_precheck_context()
        try:
            _guards.verify_frozen_hashes()
            directly = True
        except _guards.FrozenTamperError:
            directly = False
        self.assertEqual(directly, ctx.frozen_hashes_ok)

    def test_it_REALLY_calls_the_guard_rather_than_assuming_True(self):
        """THE DISCRIMINATING TEST, and the previous ones could not do it.

        On a healthy machine `verify_frozen_hashes()` passes, so "measured
        True" and "assumed True" produce the same value and every assertion
        above holds either way -- I proved that by mutating the assembler to
        assume, and the file stayed green. So this makes the guard REPORT
        TAMPER and requires the assembler to carry that through. An assembler
        that assumes still says True here, and goes red."""
        real = _guards.verify_frozen_hashes

        def tampered():
            raise _guards.FrozenTamperError("frozen file modified: (injected)")

        _guards.verify_frozen_hashes = tampered
        try:
            ctx, gaps = pc.assemble_precheck_context()
        finally:
            _guards.verify_frozen_hashes = real
        self.assertEqual((), gaps)
        self.assertIs(False, ctx.frozen_hashes_ok,
                      "the assembler reported frozen_hashes_ok=True while "
                      "the guard was raising FrozenTamperError, so it is "
                      "not calling the guard")

    def test_a_tampered_report_reaches_the_GATE_too(self):
        """The value has to travel, not just be stored: the gate is what
        acts on it."""
        real = _guards.verify_frozen_hashes

        def tampered():
            raise _guards.FrozenTamperError("frozen file modified: (injected)")

        _guards.verify_frozen_hashes = tampered
        try:
            report = pc.run_precheck()
        finally:
            _guards.verify_frozen_hashes = real
        refusing = {n for n, d in report.results if d is not None}
        self.assertIn("frozen_hashes", refusing)

    def test_the_head_it_reports_is_the_head_git_reports(self):
        import subprocess
        repo = Path(__file__).resolve().parents[1]
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(head, pc.run_precheck().head_commit)


class TestTheReportCoversEveryGate(unittest.TestCase):

    def test_it_reports_all_thirteen_in_the_contracts_order(self):
        report = pc.run_precheck()
        self.assertEqual(list(sc.GATE_TABLE["A_PRECHECK"]),
                         [name for name, _detail in report.results],
                         "the report's order must be the contract's, so the "
                         "gate it names is reproducible from the governance "
                         "text rather than from this module")

    def test_it_does_not_stop_at_the_first_refusal(self):
        """`run_stage_gates` short-circuits, which is right for a run and
        wrong for a report: 'the first gate that refuses' and 'which of the
        thirteen would refuse' are different questions."""
        report = pc.run_precheck()
        self.assertEqual(13, len(report.results))
        first = report.first_refusal
        if first is not None:
            index = [n for n, _d in report.results].index(first[0])
            self.assertGreater(len(report.results) - index, 1,
                               "results stop at the first refusal")

    def test_passed_is_false_while_anything_refuses(self):
        report = pc.run_precheck()
        refusing = [n for n, d in report.results if d is not None]
        self.assertEqual(report.passed, not refusing)

    def test_the_report_is_not_vacuously_green(self):
        """Today it MUST refuse somewhere: there is no live P2. A report
        that came back clean would mean the gates were not consulted."""
        report = pc.run_precheck()
        names = {n for n, d in report.results if d is not None}
        self.assertIn("live_authorization_unique", names,
                      "no live authorization exists, so this gate must "
                      "refuse; if it passed, the context is not the real one")


if __name__ == "__main__":
    unittest.main()
