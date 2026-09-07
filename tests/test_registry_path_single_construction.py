"""Invariant 5 of dec-registry-migration-2026-08-27 — one construction site.

WHY THE EXISTING GUARD DID NOT COVER THIS. `test_registry_boundary.py`
asserts that no production module READS the governed path outside the
boundary, and it deliberately exempts three refusal stubs — each proved to
refuse by being CALLED. That architecture is sound for reads.

But migration changes the PATH, and the two sets do not overlap: the three
exempt modules each CONSTRUCTED the path themselves. The seat put it exactly
right — `registry_boundary`'s "the one governed path" comment described an
intention, not a mechanically guaranteed fact.

WHAT THE FOUR SITES ALSO CARRIED. Every one had
`read_text(...) if exists() else ""`, the same silent-empty fallback fixed
inside the boundary — so fixing the boundary alone would have closed nothing.
And `consumer.py` built a RELATIVE path, which resolved only when the
process happened to run from the repository root.

WHY THIS LANDS BEFORE THE ROUTE IS CHOSEN. The ruling made it route-
independent and ordered it first: whichever route wins, the path then
changes in one place instead of five.
"""

import ast
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "itsf"

#: The one module allowed to spell the path.
_BOUNDARY = "registry_boundary"

#: How the path gets built: either the literal, or the segments joined.
_LITERAL = "ops/TRIAL_REGISTRY.md"
_FILENAME = "TRIAL_REGISTRY.md"


def _constructions(path: Path):
    """String constants naming the registry file, outside docstrings.

    AST rather than grep, because a docstring that DESCRIBES the path is
    not a construction of it — and this file's whole point is that the
    distinction was being made by eye."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstrings:
                continue
            if _FILENAME in node.value or node.value == _LITERAL:
                found.append((node.lineno, node.value))
    return found


#: `scripts/` is not the package, and the first version of this guard did
#: not scan it. The migration-plan review found the gap: S6's "only one
#: place to change" was not proven to cover registry WRITERS, and
#: `scripts/s0_real_run.py` constructs the path itself at module level and
#: reads it in two more places.
#:
#: It is registered rather than converged. The script is the real-run entry
#: and its `CLEAN_GATE_ALLOWLIST_FILES` entry is GATE SEMANTICS the ruling
#: said not to touch; folding its path construction into the boundary is a
#: change to the real-run stack, not to this window's subject. So the
#: exception is named, counted, and will fail if it grows.
_KNOWN_SCRIPT_CONSTRUCTIONS = {
    # WAS 2 until 2026-08-31. Migration Route A step S6 replaced the REGISTRY
    # constant's own construction with an import of the boundary's frozen
    # root, so only the clean-gate allowlist entry still spells the path --
    # and that one is gate semantics the ruling said not to touch.
    "scripts/s0_real_run.py": 1,   # clean-gate allowlist entry only
    # ADDED 2026-08-31. This one is not a path CONSTRUCTION at all -- the
    # strings are the text of the CR1 canonical grammar block, which names
    # the relative path inside its own prose and must stay verbatim or the
    # approved hash changes. Registered rather than reworded for exactly
    # that reason: rewording it to please a guard would alter the artifact
    # the guard exists to protect.
    #
    # The guard cannot tell grammar text from a path construction, and that
    # is not a defect in it. A migration has to find every spelling, and a
    # walk that tried to judge intent would miss the ones that matter.
    #
    # MEASURED. I first typed 6 here and the walk found 3 --
    # the sixth hand-typed number to come out wrong tonight, and
    # this one inside the table whose own comment argues against
    # typing things. Register the FILE by hand; take the COUNT
    # from the walk.
    "scripts/r4v2_block_builder.py": 3,
}

#: THE HOLE THIS GUARD HAD, found by the migration it was written for.
#:
#: It walked `src/` and `scripts/` and never `tests/`. So when S6 repointed
#: the path, eight test-side constructions stayed pointed at the old
#: location -- and the failure mode was not a red test. The old path now
#: holds a TOMBSTONE, which parses cleanly and yields zero rows, so
#: `test_mc_supplement_paths_battery`'s "real registry" became an empty
#: sequence namespace. One assert on "no numbered rows" is the only reason
#: that surfaced at all.
#:
#: Registered rather than converged, for the same reason as the script
#: above: a test that deliberately reads the OLD path (to prove it is a
#: tombstone) is correct and must not be rewritten to read the new one. What
#: matters is that the set is enumerated, so the next migration can find
#: every one instead of discovering them by silent pass.
_KNOWN_TEST_CONSTRUCTIONS = {
    # MEASURED, not typed. My first version of this table was written
    # from a grep and named seven files with eight constructions; the
    # walk finds twelve files with 26. A hand-written mirror of derived
    # data, wrong on its first outing -- which is the argument for the
    # walk existing, made against the person who wrote the walk.
    "tests/test_mc_supplement_integration.py": 1,
    "tests/test_mc_supplement_paths_battery.py": 1,
    "tests/test_mc_supplement_registry.py": 1,
    "tests/test_mc_supplement_runner.py": 2,
    "tests/test_nd1_profile_revision_chain.py": 1,
    # The P3 seam's tests copy the real ledger to a temp file and write
    # only to the copy; the construction is the READ of the original.
    "tests/test_p3_append_seam.py": 1,
    # QROS-CF F05/F06 settling tests. Six constructions, all of them the
    # READ of the live ledger used as realistic text for the owner-control
    # intent scan, plus the final assertion that this file wrote nothing to
    # it. Every append case writes to a tmp_path copy.
    "tests/test_qros_cf_astra_repairs.py": 6,
    # QROS-CF ROUND TWO settling tests. Eleven constructions, every one the
    # NAME of a tmp_path copy the append cases write to -- the F05 and F06
    # cases each build their own ledger under `tmp_path`. This file takes NO
    # read of the live ledger: it reuses round one's `LIVE_REGISTRY`, and its
    # last test asserts the real file is byte-identical to that snapshot when
    # the module finishes.
    #
    # MEASURED, not typed -- the walk says 11. The table above already carries
    # one comment about a hand-typed count coming out wrong; no reason to add
    # a second.
    "tests/test_qros_cf_astra_round2.py": 11,
    # QROS-CF PRE-CERT settling tests. One construction: the tmp_path ledger
    # the F06 physical-write count is driven against. Its last test asserts the
    # real ledger is byte-identical to round one's snapshot afterwards.
    #
    # MEASURED, not typed -- the walk says 1.
    "tests/test_qros_cf_pre_cert.py": 1,
    # F06 cross-module writer completeness + the S0 interleavings. Two
    # constructions: the tmp_path ledger fixture and the tailless-ledger
    # case. Its last test asserts the real ledger is untouched.
    #
    # MEASURED, not typed -- the walk says 4. I typed 2 first and the walk
    # corrected me, in the table whose own comment warns about exactly that.
    "tests/test_qros_cf_f06_writer_completeness.py": 4,
    # F06-OWNER-SEMANTICS: the confirmed final-cert failure shape and the
    # ten deterministic orderings around it. Three constructions, all
    # tmp_path ledgers; its last test asserts the real ledger is untouched.
    #
    # MEASURED from the walk, not typed.
    "tests/test_qros_cf_f06_owner_semantics.py": 3,
    "tests/test_registry_absence_refuses.py": 7,
    "tests/test_registry_boundary.py": 2,
    "tests/test_registry_path_single_construction.py": 2,
    "tests/test_registry_witness.py": 2,
    "tests/test_s0_runner.py": 5,
    "tests/test_the_writer_rulings_are_already_in_the_contract.py": 1,
    "tests/test_what_the_registry_append_unlocks.py": 1,
}


class TestOneConstructionSite(unittest.TestCase):

    def test_scripts_constructions_are_exactly_the_registered_ones(self):
        """Not zero — REGISTERED. A count that grows means a new writer
        appeared outside the boundary, which is what would make a migration
        miss a path."""
        found = {}
        for path in sorted((REPO / "scripts").rglob("*.py")):
            hits = _constructions(path)
            if hits:
                found[path.relative_to(REPO).as_posix()] = len(hits)
        self.assertEqual(_KNOWN_SCRIPT_CONSTRUCTIONS, found,
                         "the set of registry-path constructions under "
                         "scripts/ changed; a migration would have to find "
                         "and update every one")

    def test_test_constructions_are_exactly_the_registered_ones(self):
        """ADDED 2026-08-31, because the migration walked past these.

        A test pointing at the old path does not necessarily go red -- the
        tombstone parses -- so this set has to be enumerated rather than
        trusted to announce itself."""
        found = {}
        for path in sorted((REPO / "tests").rglob("*.py")):
            hits = _constructions(path)
            if hits:
                found[path.relative_to(REPO).as_posix()] = len(hits)
        self.assertEqual(
            _KNOWN_TEST_CONSTRUCTIONS, found,
            "the set of registry-path constructions under tests/ changed. "
            "Registering one is fine; leaving it unregistered means the next "
            "migration cannot find it, and a test reading the old path can "
            "pass while reasoning about a tombstone.")

    def test_the_scan_actually_reaches_files(self):
        """THE PREMISE THE GUARD BELOW CANNOT PROVE ABOUT ITSELF.

        `assertEqual([], offenders)` is true when the scan found nothing to
        look at. A wrong root, a changed glob, a package move — the guard
        then reports clean forever, which is worse than no guard because it
        reports clean LOUDLY. Measured here so the failure is visible."""
        modules = [p for p in SRC.rglob("*.py") if p.stem != _BOUNDARY]
        self.assertGreater(len(modules), 20,
                           f"the construction scan reached {len(modules)} "
                           "modules; at that count it proves nothing")

    def test_only_the_boundary_constructs_the_registry_path(self):
        offenders = []
        for path in sorted(SRC.rglob("*.py")):
            if path.stem == _BOUNDARY:
                continue
            for lineno, value in _constructions(path):
                offenders.append(
                    f"{path.relative_to(REPO).as_posix()}:{lineno} "
                    f"constructs {value!r}")
        self.assertEqual([], offenders,
                         "the governed registry path is constructed outside "
                         "registry_boundary; a migration would have to find "
                         "and update every one of these:\n  "
                         + "\n  ".join(offenders))

    def test_the_boundary_still_holds_it_exactly_once(self):
        """The other direction: if the constant disappeared, the guard above
        would pass vacuously."""
        found = _constructions(SRC / "mc" / "registry_boundary.py")
        self.assertEqual(1, len(found),
                         f"expected exactly one construction, got {found}")
        self.assertEqual(_LITERAL, found[0][1])


class TestTheConvergenceKeptTheSemantics(unittest.TestCase):
    """A refactor that changed what the gates do would be a different act
    from the one the ruling authorised."""

    def test_the_three_production_entries_still_refuse_gate_first(self):
        from itsf.mc import consumer, day_strata_supplement, real_input
        for fn in (day_strata_supplement.run_supplement_production,
                   consumer.run_real_mc,
                   real_input.prepare_real_mc_input):
            with self.assertRaises(Exception, msg=fn.__name__) as cm:
                fn()
            self.assertNotIsInstance(cm.exception, AssertionError)

    def test_they_route_through_the_boundary_now(self):
        """Named explicitly: if a site goes back to reading the file
        directly, the construction guard above catches the path but not a
        direct read of a path obtained some other way."""
        import inspect
        from itsf.mc import consumer, day_strata_supplement, real_input
        for fn in (day_strata_supplement.run_supplement_production,
                   consumer.run_real_mc,
                   real_input.prepare_real_mc_input):
            src = inspect.getsource(fn)
            self.assertIn("read_snapshot", src,
                          f"{fn.__name__} no longer reads through the "
                          "boundary")
            self.assertNotIn('else ""', src,
                             f"{fn.__name__} regained the silent-empty "
                             "fallback")


if __name__ == "__main__":
    unittest.main()
