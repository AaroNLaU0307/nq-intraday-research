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

import ast
import ctypes
import hashlib
import os
import sys
import traceback
import unittest
from collections import Counter
from ctypes import wintypes
from pathlib import Path
from tempfile import TemporaryDirectory

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr

NAME = "DAY_STRATA_SUPPLEMENT.json"
INTENDED = b'{"schema": "mc_day_strata_supplement.v1", "rows": []}'
DIFFERENT = b'{"schema": "something else entirely"}'
RESIDUE = b"irreplaceable partial residue"
INCIDENT = "INC-0123456789ab"


_MAX_STREAM_NAME = 260 + 36


class _StreamData(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong),
                ("cStreamName", ctypes.c_wchar * _MAX_STREAM_NAME)]


def alternate_streams(path):
    """Every NAMED data stream of `path`; the default stream excluded.

    ROUND 7's HIGH-2. The snapshot hashed each file's default data stream and
    called the result "every blob of bytes in the directory". On NTFS that is
    false: `x.json:evidence` holds real bytes, a directory listing never shows
    it, and `Path.read_bytes` never reads it. Sol deleted a `.partial` and
    rewrote FINAL with identical main bytes -- `BLOBS_LOST=[]`, `ADS_SURVIVES=
    False`. The claim was wider than the instrument, which is the shape this
    whole review keeps finding.

    ENUMERATED, not narrowed. Writing "the default data stream only" into the
    docstring would have been the cheap answer and would have been honest, but
    it would also have left real bytes in a governed directory that nothing
    watches. `FindFirstStreamW` is the OS's own answer to "what streams does
    this file have", so the universe stays the FILE rather than becoming a
    list of stream names someone remembered to write down.

    Off NTFS there are no alternate streams to miss, so returning nothing
    there is the correct answer rather than a gap -- and
    `TestTheStreamWalkIsREAL` refuses to pass vacuously on a platform where
    the walk cannot run.
    """
    if sys.platform != "win32":
        return []
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.FindFirstStreamW.restype = wintypes.HANDLE
    k32.FindFirstStreamW.argtypes = [wintypes.LPCWSTR, ctypes.c_int,
                                     ctypes.c_void_p, wintypes.DWORD]
    k32.FindNextStreamW.restype = wintypes.BOOL
    k32.FindNextStreamW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    k32.FindClose.argtypes = [wintypes.HANDLE]
    data = _StreamData()
    handle = k32.FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    if handle == wintypes.HANDLE(-1).value:
        return []
    found = []
    try:
        while True:
            name = data.cStreamName
            if name.endswith(":$DATA"):
                name = name[:-len(":$DATA")]
            if name and name != ":":          # ":" is the default stream
                found.append(name)
            if not k32.FindNextStreamW(handle, ctypes.byref(data)):
                break
    finally:
        k32.FindClose(handle)
    return found


def snapshot(root):
    """name -> sha256 for every file under `root`, ALTERNATE STREAMS INCLUDED.

    The DIRECTORY is the universe: nothing is declared and then looked for.
    A named stream appears under its full `file:stream` key, so losing one is
    losing a blob exactly as losing a file is."""
    root = Path(root)
    out = {}
    for entry in sorted(root.rglob("*")):
        if not entry.is_file():
            continue
        key = entry.relative_to(root).as_posix()
        out[key] = hashlib.sha256(entry.read_bytes()).hexdigest()
        for stream in alternate_streams(entry):
            with open(str(entry) + stream, "rb") as handle:
                out[key + stream] = hashlib.sha256(handle.read()).hexdigest()
    return out


def blobs_lost(before, after):
    """Digests present before and no longer present anywhere after.

    A MULTISET difference, so two files holding identical bytes need two
    survivors. Renaming is invisible to it by design -- moving evidence aside
    is exactly what branch C is supposed to do, and forbidding renames would
    refuse the correct behaviour."""
    return sorted((Counter(before.values()) - Counter(after.values())).elements())


RUNNER_FILE = os.path.abspath(sr.__file__)


class _Run:
    """One real call, with the directory snapshotted either side.

    THE ROOT IS THE PARENT of out_dir, not out_dir. Round 7 promoted a file
    through `resolve_partial(out, "../escaped.json", ...)` and this instrument
    reported an empty diff, because it was looking only inside the directory
    the write had just left. Snapshotting the parent is what makes an escape
    visible at all; the runner now refuses one, and both halves are needed --
    the refusal so it cannot happen, the wider snapshot so a future one is
    not invisible again."""

    def __init__(self, case, final_state, partial_state, *,
                 incident=INCIDENT, extra=None, filename=NAME,
                 lie_partial=None, lie_final=None, lie_partial_from=1):
        holder = TemporaryDirectory()
        case.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.final = self.out / NAME
        self.partial = self.out / (NAME + sc.PARTIAL_SUFFIX)
        _place(self.final, final_state)
        _place(self.partial, partial_state)
        if extra:
            extra(self.out)

        self.before = snapshot(self.root)
        self._lines = []
        real_read = Path.read_bytes

        partial_reads = [0]

        def read_bytes(this):
            data = real_read(this)
            if this.name.endswith(sc.PARTIAL_SUFFIX):
                partial_reads[0] += 1
                # WHICH read lies matters, and getting it wrong hid three
                # declared paths. `resolve_partial` reads the partial TWICE
                # when one is already staged: once to decide branch C, once
                # to verify what it staged. A lie on the first read sends the
                # call down branch C, so the fall-through tail is never
                # reached and its exits look unreachable.
                if lie_partial and partial_reads[0] >= lie_partial_from:
                    return lie_partial
            if lie_final and data == INTENDED and this.name == NAME:
                return lie_final
            return data

        Path.read_bytes = read_bytes
        sys.settrace(self._trace)
        try:
            self.action = sr.resolve_partial(self.out, filename, INTENDED,
                                             incident_id=incident)
            self.error = None
        except Exception as exc:                              # noqa: BLE001
            self.action, self.error = None, exc
        finally:
            sys.settrace(None)
            Path.read_bytes = real_read
        self.after = snapshot(self.root)

    def _trace(self, frame, event, arg):
        """Record the lines executed inside `resolve_partial` ITSELF.

        The last one is the line the call left through, which is the half of
        an exit's identity that says WHICH path took it. A helper raise leaves
        through its call site, so branch C and branch E stop being the same
        thing the moment this is recorded."""
        if (frame.f_code.co_name != "resolve_partial"
                or os.path.abspath(frame.f_code.co_filename) != RUNNER_FILE):
            return None

        def local(inner, inner_event, inner_arg):
            if inner_event == "line":
                self._lines.append(inner.f_lineno)
            return local

        self._lines.append(frame.f_lineno)
        return local

    @property
    def exit_name(self):
        """The exit ACTUALLY taken, read off the real result."""
        if self.error is not None:
            return getattr(self.error, "code", type(self.error).__name__)
        return self.action.action

    @property
    def helper_raise_line(self):
        """The line INSIDE a helper that raised, or None for a direct exit.

        One call site can reach two different raises in one helper --
        `_require_plain_name` refuses an unnamed path at one statement and a
        forbidden character at another -- and those are two paths whose route
        through `resolve_partial` is identical. Without this they collapse."""
        if self.error is None:
            return None
        for frame in reversed(traceback.extract_tb(self.error.__traceback__)):
            if (os.path.abspath(frame.filename) == RUNNER_FILE
                    and frame.name != "resolve_partial"):
                return frame.lineno
        return None

    @property
    def exit_site_id(self):
        """(name, exit line, helper raise line) — the EXIT SITE, and that is
        all it ever was.

        NAMED HONESTLY AFTER ROUND 8. This was called `path_id` and the packet
        called it a path identity. It is not: two branches that fall through
        and rejoin leave by the same line, so `promote` reached with bytes
        already staged and `promote` reached having just staged them shared
        one value. Sol deleted one of those scenarios and coverage stayed
        green.

        Path identity moved to `_declared_paths` plus the executed line
        TRACE, which distinguishes them. This stays for the cases where the
        exit site is genuinely the question."""
        return (self.exit_name, self._lines[-1] if self._lines else None,
                self.helper_raise_line)

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
        # "out/" because the snapshot root is now out_dir's PARENT, which is
        # what makes an escaping write visible at all. See _Run's docstring.
        expected = "out/" + sr._divergent_name(NAME, INCIDENT)
        self.assertEqual(hashlib.sha256(RESIDUE).hexdigest(),
                         run.after.get(expected),
                         "after %r the directory holds %r"
                         % (run.exit_name, sorted(run.after)))

    def test_the_original_partial_name_is_free_again(self):
        """Unblocking the path is the other half of the ratified MODIFY;
        without it the rename would preserve evidence and wedge the run."""
        run = _Run(self, "absent", "residue")
        self.assertNotIn("out/" + NAME + sc.PARTIAL_SUFFIX, run.after)

    def test_a_second_incident_refuses_rather_than_clobbering(self):
        run = _Run(self, "absent", "residue",
                   extra=lambda root: (root / sr._divergent_name(
                       NAME, INCIDENT)).write_bytes(b"the first incident"))
        self.assertEqual("divergent_partial_exists", run.exit_name)
        self.assertEqual([], run.lost)


def _declared_paths():
    """Every declared path, as (name, statement lines, helper raise line).

    THE THIRD COMPONENT is what separates two refusals raised from the SAME
    call site by different statements inside one helper -- `_require_plain_name`
    rejects an unnamed path at one line and a forbidden character at another.
    Their statement lines through `resolve_partial` are identical, so without
    it they collapse, which is the same defect one scope down.

    Both halves come from the AST walk. The DOCSTRING line is dropped because
    the tracer reports the `def` line where the walker reports the first
    statement -- a fixed, measured offset, not a fudge: with it removed the
    correspondence below is exact on every path."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_resolve_partial_path_contract as contract
    function = contract._resolve_partial()
    doc = function.body[0]
    docstring_line = (doc.lineno if isinstance(doc, ast.Expr)
                      and isinstance(doc.value, ast.Constant) else None)
    return [(e["name"], frozenset(e["lines"]) - {docstring_line},
             e["raise_line"]) for e in contract._exits()]


class TestEveryDeclaredPATHIsReachedBYEXECUTION(unittest.TestCase):
    """Round 8's HIGH, and the FOURTH instrument this one claim has needed.

        R6  `reached` was a set LITERAL typed beside a derived `declared`.
        R7  Derived, but reduced to `{name}`. Branch C's exits stood in for
            branch E's, which had never executed.
        R8  Derived and name-plus-line -- which identifies the EXIT SITE, not
            the path. Two branches that fall through and rejoin share their
            exit line, so `promote` reached with bytes already staged and
            `promote` reached having just staged them were one identity. Sol
            deleted one of those scenarios from the generator and the
            coverage assertion stayed green.

    Each round the collapse got smaller and each round it was still a
    collapse. The root cause was upstream the whole time: the AST walker
    walked everything after an `if` ONCE, carrying the guards from before it,
    so the two rejoining paths were never two declarations to begin with.
    Fixing the walker to fork the remainder turned 12 declared exits into 17
    -- none of them new code, five of them always executable and counted as
    someone else.

    THE IDENTITY IS NOW THE PATH ITSELF, derived on both sides:

        declared  the set of statement lines the walk passes to reach an exit
        executed  the lines `sys.settrace` records inside resolve_partial

    A declared path matches a run when every one of its lines was executed,
    and the match must be UNIQUE -- two declarations fitting one trace would
    mean the identity had collapsed again, so that is a failure here rather
    than a silent pass.
    """

    def _runs(self):
        """Every declared path, driven for real."""
        divergent = lambda root: (root / sr._divergent_name(
            NAME, INCIDENT)).write_bytes(b"an earlier incident")
        lie = b"the staged bytes re-read differently"
        runs = [_Run(self, f, p) for f, p in SCENARIOS]
        runs += [
            _Run(self, "absent", "absent", filename="../escaped.json"),
            _Run(self, "absent", "absent", filename=NAME + ":evidence"),
            _Run(self, "absent", "residue", extra=divergent),
            _Run(self, "absent", "residue", incident="not-an-incident-id"),
        ]
        # The tail, reached BOTH ways -- with a byte-identical residue already
        # staged, and having staged the bytes in this call. Round 8 proved
        # those are two paths; before it, only one of each pair ever ran.
        for staged, first_lie in (("absent", 1), ("intended", 2)):
            runs += [
                _Run(self, "absent", staged, extra=divergent, lie_partial=lie,
                     lie_partial_from=first_lie),
                _Run(self, "absent", staged, incident="not-an-incident-id",
                     lie_partial=lie, lie_partial_from=first_lie),
                _Run(self, "absent", staged, lie_partial=lie,
                     lie_partial_from=first_lie),
                _Run(self, "absent", staged,
                     lie_final=b"the promotion did not survive"),
            ]
        return runs

    def test_the_tracer_actually_saw_something(self):
        """Vacuity first. `sys.settrace` is inert under some runners, and an
        empty trace would make every path match nothing -- or everything."""
        run = _Run(self, "absent", "absent")
        self.assertTrue(run._lines, "the tracer recorded no lines")
        self.assertEqual("promote", run.exit_name)

    def test_the_declared_paths_are_distinguishable_at_all(self):
        declared = _declared_paths()
        self.assertEqual(len(declared), len(set(declared)),
                         "two declared paths are identical: %s" % declared)
        names = [name for name, _lines, _raised in declared]
        self.assertLess(
            len(set(names)), len(names),
            "no name repeats, so this file's premise -- that a name is not "
            "an identity -- is not being tested by anything")

    def test_two_rejoining_paths_are_NOT_the_same_declaration(self):
        """Sol's exact pair, named. `promote` with bytes already staged and
        `promote` having staged them here."""
        promotes = [lines for name, lines, _raised in _declared_paths()
                    if name == "promote"]
        self.assertEqual(2, len(promotes))
        self.assertNotEqual(promotes[0], promotes[1])

    def test_every_declared_path_was_actually_executed(self):
        declared, runs = _declared_paths(), self._runs()
        covered = set()
        for run in runs:
            trace = set(run._lines)
            fits = [d for d in declared
                    if d[0] == run.exit_name and d[1] <= trace
                    and d[2] == run.helper_raise_line]
            self.assertEqual(
                1, len(fits),
                "a run exiting via %s fits %d declared paths, not exactly "
                "one. Zero means the walk does not model what the code did; "
                "more than one means the identity has collapsed again."
                % (run.exit_name, len(fits)))
            covered.add(fits[0])
        missing = sorted((name, sorted(lines), raised)
                          for name, lines, raised in set(declared) - covered)
        self.assertEqual(
            [], missing,
            "declared by the contract and executed by nothing here: %s\n"
            "A path is the set of statements that reach the exit, so two "
            "branches sharing an exit line are still two paths." % missing)


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

    def test_an_ADS_TRUNCATION_is_reported(self):
        """SOL'S ROUND-7 MUTATION. Under the shipped version this was
        `BLOBS_LOST=[]` while `ADS_SURVIVES=False`."""
        if sys.platform != "win32":
            self.skipTest("alternate data streams are an NTFS feature")

        def mutate(root):
            target = str(root / "residue.partial") + ":evidence"
            with open(target, "wb") as handle:
                handle.write(b"")

        def prepare(root):
            with open(str(root / "residue.partial") + ":evidence", "wb") as h:
                h.write(b"evidence nobody can see in a directory listing")

        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "residue.partial").write_bytes(RESIDUE)
        prepare(root)
        before = snapshot(root)
        self.assertEqual(2, len(before),
                         "the stream was not snapshotted at all: %r" % before)
        mutate(root)
        self.assertEqual(1, len(blobs_lost(before, snapshot(root))),
                         "an alternate stream was emptied and the diff was "
                         "silent, which is round 7's HIGH-2 exactly")

    def test_the_MAIN_bytes_surviving_does_not_excuse_a_lost_stream(self):
        """The precise shape of the bypass: same main bytes either side."""
        if sys.platform != "win32":
            self.skipTest("alternate data streams are an NTFS feature")
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        victim = root / "residue.partial"
        victim.write_bytes(RESIDUE)
        with open(str(victim) + ":evidence", "wb") as handle:
            handle.write(b"the only copy of something")
        before = snapshot(root)
        victim.unlink()
        (root / "residue.partial").write_bytes(RESIDUE)   # main bytes restored
        after = snapshot(root)
        self.assertIn(hashlib.sha256(RESIDUE).hexdigest(), after.values(),
                      "the main bytes really are back")
        self.assertEqual(1, len(blobs_lost(before, after)))

    def test_an_untouched_directory_really_reports_nothing(self):
        self.assertEqual([], self._pair(lambda root: None))

    def test_the_snapshot_really_sees_nested_files(self):
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "deep").mkdir()
        (root / "deep" / "x.json").write_bytes(b"x")
        self.assertEqual(["deep/x.json"], sorted(snapshot(root)))


class TestTheStreamWalkIsREAL(unittest.TestCase):
    """Non-vacuity for the stream walk itself.

    `alternate_streams` returning `[]` is indistinguishable from a broken
    ctypes binding, and a broken binding would make every ADS test above pass
    while measuring nothing. On Windows the walk must actually find a stream
    that was actually written."""

    def test_a_written_stream_is_found_and_read_back(self):
        if sys.platform != "win32":
            self.skipTest("alternate data streams are an NTFS feature")
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        target = Path(holder.name) / "x.json"
        target.write_bytes(b"main")
        with open(str(target) + ":evidence", "wb") as handle:
            handle.write(b"stream bytes")
        self.assertEqual([":evidence"], alternate_streams(target))
        snap = snapshot(Path(holder.name))
        self.assertEqual(
            hashlib.sha256(b"stream bytes").hexdigest(),
            snap.get("x.json:evidence"),
            "the walk found the stream but the snapshot did not record it: "
            "%r" % snap)

    def test_a_file_with_no_streams_reports_none(self):
        if sys.platform != "win32":
            self.skipTest("alternate data streams are an NTFS feature")
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        plain = Path(holder.name) / "plain.json"
        plain.write_bytes(b"x")
        self.assertEqual([], alternate_streams(plain))

    def test_the_runner_can_no_longer_CREATE_one(self):
        """The production half of the same finding. A filename carrying a
        colon would have written into a stream of a different file; round 7's
        out_dir fix refuses it, so both halves are closed rather than one."""
        run = _Run(self, "absent", "absent", filename=NAME + ":evidence")
        self.assertEqual("filename_not_a_plain_name", run.exit_name)
        self.assertEqual({}, run.after)


if __name__ == "__main__":
    unittest.main()
