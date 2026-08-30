"""SILENT_DELETE_FORBIDDEN as a property of the DIRECTORY, not of the calls.

WHY THIS FILE EXISTS, and it is the sixth round of the same lesson learned
one level down.

    R3-R5  I enumerated SYNTACTIC SHAPES. For any shape a checker demands,
           the set of expressions satisfying it while violating the
           semantics is infinite. Five rounds, five defeats.
    R6     So I switched to observing CALLS -- and enumerated INTERCEPTION
           POINTS instead. `Path.read_bytes`, `Path.write_bytes`,
           `Path.unlink`, `os.replace`. Sol emptied the residue through
           `builtins.open` inside a `Path` subclass: the observer reported
           `writes=[]`, `unlinks=[]`, both suites green, and
           b'irreplaceable partial residue' became b''.

The set of mechanisms that can change a byte is infinite too: `builtins.open`,
`os.open`, `shutil.*`, `mmap`, `os.truncate`, `ctypes`, a subprocess, a `Path`
subclass, a method bound to a local name before the wrapper was installed.
ADDING THOSE THREE TO THE WRAPPER WOULD HAVE BEEN ROUND SEVEN OF THE SAME
MISTAKE -- the next round arrives with `mmap` and is right.

WHAT CLOSES IT. Stop observing operations; observe STATE. Snapshot the whole
directory byte for byte, run the real function, snapshot again, and assert on
the difference. It does not matter what performed the change, because nothing
is being intercepted: the bytes are simply counted before and after.

THE PROPERTY, stated so it survives renaming:

    EVERY BLOB OF BYTES PRESENT BEFORE IS STILL PRESENT AFTER, SOMEWHERE.

A multiset of digests, and `before <= after`. A rename keeps the blob under a
new name and passes. An unlink loses it. A truncate to b'' loses it. A
same-length overwrite loses it. None of those can hide behind an API this file
never heard of.

THIS IS NOT A NEW IDEA IN THIS REPOSITORY. `day_strata_pipeline
.supplement_bytes_snapshot` is the same instrument, built for the same reason
and carrying the same sentence: the DIRECTORY is the universe, nothing is
declared and then looked for. C_BUILD_1 has been asserted this way all along.
The resolve_partial obligations should have been from the start.

WHAT STATE CANNOT SEE, said plainly rather than left for the next reviewer:

  * CAUSALITY. "The answer `already_sealed` was computed FROM the bytes it
    read" is not visible in a diff -- nothing changed either way. That
    obligation stays with `test_resolve_partial_observed_behaviour.py`, whose
    lying-read technique is the right instrument for it and which round 6 did
    not attack.
  * A WRITE THEN RESTORED inside one call. The blob is present at both ends,
    so the diff is empty. This is a genuinely narrower residual than "any
    unwrapped API", and it is the honest cost of the change.
"""

import hashlib
import os
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr

NAME = "DAY_STRATA_SUPPLEMENT.json"
INTENDED = b'{"schema": "mc_day_strata_supplement.v1", "rows": []}'
DIFFERENT = b'{"schema": "something else entirely"}'
RESIDUE = b"irreplaceable partial residue"
INCIDENT = "INC-0123456789ab"


def snapshot(root):
    """name -> sha256 for every file under `root`. The DIRECTORY is the
    universe: nothing is declared and then looked for."""
    root = Path(root)
    out = {}
    for entry in sorted(root.rglob("*")):
        if entry.is_file():
            out[entry.relative_to(root).as_posix()] = hashlib.sha256(
                entry.read_bytes()).hexdigest()
    return out


def blobs_lost(before, after):
    """Digests present before and no longer present anywhere after.

    A MULTISET difference, so two files holding identical bytes need two
    survivors. Renaming is invisible to it by design -- moving evidence aside
    is exactly what branch C is supposed to do, and forbidding renames would
    refuse the correct behaviour."""
    return sorted((Counter(before.values()) - Counter(after.values())).elements())


class _Run:
    """One real call, with the directory snapshotted either side."""

    def __init__(self, case, final_state, partial_state, *,
                 incident=INCIDENT, extra=None):
        holder = TemporaryDirectory()
        case.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        self.final = self.root / NAME
        self.partial = self.root / (NAME + sc.PARTIAL_SUFFIX)
        _place(self.final, final_state)
        _place(self.partial, partial_state)
        if extra:
            extra(self.root)

        self.before = snapshot(self.root)
        try:
            self.action = sr.resolve_partial(self.root, NAME, INTENDED,
                                             incident_id=incident)
            self.error = None
        except Exception as exc:                              # noqa: BLE001
            self.action, self.error = None, exc
        self.after = snapshot(self.root)

    @property
    def exit_name(self):
        """The exit ACTUALLY taken, read off the real result.

        This is the derivation round 6's coverage claim was missing: it typed
        the reached set out by hand next to a derived declared set, so an exit
        nothing executed counted as covered."""
        if self.error is not None:
            return getattr(self.error, "code", type(self.error).__name__)
        return self.action.action

    @property
    def lost(self):
        return blobs_lost(self.before, self.after)


def _place(path, state):
    if state == "absent":
        return
    path.write_bytes({"intended": INTENDED, "different": DIFFERENT,
                      "residue": RESIDUE}[state])


#: The scenario space, GENERATED rather than listed. Round 6 shipped five
#: hand-written scenarios and Sol found the four missing combinations where
#: FINAL and `.partial` both exist -- which is precisely where the bypass
#: lived, because that is the region where the function answers from FINAL
#: while a residue is sitting there unattended.
FINAL_STATES = ("absent", "intended", "different")
PARTIAL_STATES = ("absent", "intended", "residue")
SCENARIOS = [(f, p) for f in FINAL_STATES for p in PARTIAL_STATES]


class TestTheScenarioSpaceIsGeneratedNotListed(unittest.TestCase):

    def test_all_nine_combinations_exist(self):
        self.assertEqual(9, len(SCENARIOS))

    def test_the_four_combinations_round_6_missed_are_in_it(self):
        both = [(f, p) for f, p in SCENARIOS
                if f != "absent" and p != "absent"]
        self.assertEqual(4, len(both), "%r" % (both,))


class TestNoBlobIsEverLost(unittest.TestCase):
    """The load-bearing property, over the generated space.

    Closed under mechanism: it never asks HOW the directory changed."""

    def test_no_scenario_loses_any_bytes(self):
        for final_state, partial_state in SCENARIOS:
            with self.subTest(final=final_state, partial=partial_state):
                run = _Run(self, final_state, partial_state)
                self.assertEqual(
                    [], run.lost,
                    "bytes that existed before the call exist nowhere after "
                    "it (exit %s); SILENT_DELETE_FORBIDDEN is a statement "
                    "about the directory, so this holds no matter which API "
                    "removed them" % run.exit_name)

    def test_the_residue_survives_even_when_FINAL_answers(self):
        """The four both-exist cases, called out separately because this is
        the exact region Sol's bypass lived in: the function answers from
        FINAL and never looks at the residue, so nothing in the happy path
        would notice it being emptied."""
        for final_state in ("intended", "different"):
            for partial_state in ("intended", "residue"):
                with self.subTest(final=final_state, partial=partial_state):
                    run = _Run(self, final_state, partial_state)
                    self.assertIn(
                        hashlib.sha256(
                            {"intended": INTENDED,
                             "residue": RESIDUE}[partial_state]).hexdigest(),
                        set(run.after.values()),
                        "the staged residue is gone after an answer that "
                        "never concerned it (exit %s)" % run.exit_name)


class TestBranchCMovesRatherThanDeletes(unittest.TestCase):
    """`retry_permitted` must leave the divergent bytes readable under the
    ratified name -- a STATE claim, so a rename performed by any means at all
    satisfies it and a delete performed by any means at all does not."""

    def test_the_residue_is_present_under_the_divergent_name(self):
        run = _Run(self, "absent", "residue")
        self.assertEqual("retry_permitted", run.exit_name)
        expected = sr._divergent_name(NAME, INCIDENT)
        self.assertEqual(hashlib.sha256(RESIDUE).hexdigest(),
                         run.after.get(expected),
                         "after %r the directory holds %r"
                         % (run.exit_name, sorted(run.after)))

    def test_the_original_partial_name_is_free_again(self):
        """Unblocking the path is the other half of the ratified MODIFY;
        without it the rename would preserve evidence and wedge the run."""
        run = _Run(self, "absent", "residue")
        self.assertNotIn(NAME + sc.PARTIAL_SUFFIX, run.after)

    def test_a_second_incident_refuses_rather_than_clobbering(self):
        run = _Run(self, "absent", "residue",
                   extra=lambda root: (root / sr._divergent_name(
                       NAME, INCIDENT)).write_bytes(b"the first incident"))
        self.assertEqual("divergent_partial_exists", run.exit_name)
        self.assertEqual([], run.lost)


class TestEveryDeclaredExitIsReachedBYEXECUTION(unittest.TestCase):
    """Round 6's HIGH-2, closed.

    The old version compared a DERIVED `declared` set against a HAND-TYPED
    `reached` set, under a docstring claiming both were derived. Sol added an
    `unseen_exit` to the contract and to that literal, gave it no scenario,
    and both suites stayed green.

    Here `reached` is accumulated from `run.exit_name` -- the value the real
    function actually returned or raised. An exit no scenario drives cannot
    appear in it, whatever anyone types."""

    def _reached(self):
        reached = {_Run(self, f, p).exit_name for f, p in SCENARIOS}
        reached.add(_Run(self, "absent", "residue",
                         incident="not a valid incident id").exit_name)
        reached.add(_Run(self, "absent", "residue",
                         extra=lambda root: (root / sr._divergent_name(
                             NAME, INCIDENT)).write_bytes(b"first")).exit_name)
        reached |= {self._with_lying_read(after_replace)
                    for after_replace in (False, True)}
        return reached

    def _with_lying_read(self, after_replace):
        """Branch E and the post-promotion verify both need a read to diverge
        from what is on disk, which no directory state can produce. Driving
        them needs an intervention; COUNTING them still comes from the real
        result."""
        real = Path.read_bytes
        seen = {"replaced": False}
        real_replace = os.replace

        def replace(src, dst):
            seen["replaced"] = True
            return real_replace(src, dst)

        def read_bytes(self):
            data = real(self)
            if seen["replaced"] == after_replace and data == INTENDED:
                return b"a divergent re-read"
            return data

        Path.read_bytes, os.replace = read_bytes, replace
        try:
            return _Run(self, "absent", "absent").exit_name
        finally:
            Path.read_bytes, os.replace = real, real_replace

    def test_every_declared_exit_name_was_actually_executed(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from test_resolve_partial_path_contract import DECLARED_EXITS

        declared = {name for _kind, name, _guard in DECLARED_EXITS}
        reached = self._reached()
        self.assertEqual(
            [], sorted(declared - reached),
            "declared by the contract and executed by nothing here: %s -- "
            "such an exit is counted as accounted for while no instrument "
            "has ever seen what it does"
            % sorted(declared - reached))
        self.assertEqual(
            [], sorted(reached - declared),
            "executed here but not declared in the contract: %s"
            % sorted(reached - declared))


class TestTheInstrumentIsNotVACUOUS(unittest.TestCase):
    """Every assertion above passes today, so each mechanism is exercised
    against a case built to break it. Two of them use `builtins.open` and
    `os.truncate` SPECIFICALLY -- the APIs round 6's observer could not see."""

    def _pair(self, mutate):
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "residue.partial").write_bytes(RESIDUE)
        before = snapshot(root)
        mutate(root)
        return blobs_lost(before, snapshot(root))

    def test_an_unlink_is_reported(self):
        self.assertEqual(1, len(self._pair(
            lambda root: (root / "residue.partial").unlink())))

    def test_a_truncation_through_builtins_open_is_reported(self):
        """SOL'S EXACT BYPASS. The round-6 observer reported writes=[] here."""
        def mutate(root):
            with open(str(root / "residue.partial"), "wb") as handle:
                handle.write(b"")
        self.assertEqual([hashlib.sha256(RESIDUE).hexdigest()],
                         self._pair(mutate))

    def test_a_truncation_through_os_truncate_is_reported(self):
        """An API neither round-6 nor its proposed fix wrapped, included to
        show the property is not tied to any list of names."""
        self.assertEqual(1, len(self._pair(
            lambda root: os.truncate(str(root / "residue.partial"), 0))))

    def test_a_same_LENGTH_overwrite_is_reported(self):
        self.assertEqual(1, len(self._pair(
            lambda root: (root / "residue.partial").write_bytes(
                b"X" * len(RESIDUE)))))

    def test_a_RENAME_is_correctly_NOT_reported(self):
        """The other direction, and it matters: a check that refused renames
        would refuse branch C, which is the ratified behaviour."""
        self.assertEqual([], self._pair(
            lambda root: os.replace(str(root / "residue.partial"),
                                    str(root / "moved.aside"))))

    def test_two_identical_blobs_need_two_survivors(self):
        """The multiset half. A set would call one survivor enough and let
        the duplicate be destroyed silently."""
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "a").write_bytes(RESIDUE)
        (root / "b").write_bytes(RESIDUE)
        before = snapshot(root)
        (root / "b").unlink()
        self.assertEqual(1, len(blobs_lost(before, snapshot(root))))

    def test_an_untouched_directory_really_reports_nothing(self):
        self.assertEqual([], self._pair(lambda root: None))

    def test_the_snapshot_really_sees_nested_files(self):
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "deep").mkdir()
        (root / "deep" / "x.json").write_bytes(b"x")
        self.assertEqual(["deep/x.json"], sorted(snapshot(root)))


if __name__ == "__main__":
    unittest.main()
