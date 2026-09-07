"""N09 R3 §6 — the four criteria that define the default-refuse scaffold.

WHAT THIS FILE IS FOR, and what it is deliberately not. R3 took the second
branch of the reviewer's minimal-unblock condition 3: limit the authorised
build explicitly to an always-refusing scaffold. R3 §6 then says what that
scaffold IS, in four criteria it calls "机械可检查，不靠自陈" — mechanically
checkable, not self-reported. Those four had no mechanism. This is it.

R3 §6's own sentence about why criterion 3 is the load-bearing one:

    骨架的价值不在于它今天拒绝，而在于它不能被悄悄改成不拒绝。
    (the scaffold's value is not that it refuses today, but that it cannot
     quietly be changed into not refusing)

SCOPE, from R3 §6 verbatim. Buildable: the structures of §1–§5. Not buildable:
any capability that lets those structures actually produce rows, seal,
archive, or append P3. R3 §7 is explicit that the four Aaron-only items and
this file are related in ONE direction — "它们未定，§1–§5 照样成立、照样可建、
照样可测". Nothing here asks for, assumes, or anticipates any of them.

NOT A GATE RELEASE. Everything below asserts that the path refuses. A test
that asserts refusal cannot authorise anything, and this file changes no
production code at all.
"""

import ast
import unittest
from pathlib import Path

import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

SRC = REPO / "src" / "itsf"

#: The eight effect-boundary fields of `ops/ND1_PROFILE_RATIFICATION.md` §4,
#: every one of them NO. R3 §6 quotes them as the reason the scaffold branch
#: was taken at all.
_ND1_FIELDS = (
    "SUPPLEMENT_EXECUTION_AUTHORIZED", "REAL_DATA_READ_AUTHORIZED",
    "DIRECTORY_CREATION_AUTHORIZED", "WRITE_PROBE_AUTHORIZED",
    "REGISTRY_EVENT_APPEND_AUTHORIZED", "EXPOSURE_EVENT_APPEND_AUTHORIZED",
    "MC_EXECUTION_AUTHORIZED", "STRATEGY_BUILD_AUTHORIZED",
)

#: Actions that put bytes on disk or move them. `replace` is here for
#: `Path.replace`/`os.replace` and it also matches `str.replace`, so a hit is
#: a question rather than a verdict — every use below pairs it with the
#: module it appears in.
_WRITE_ACTIONS = {"write_text", "write_bytes", "writelines", "mkdir",
                  "makedirs", "unlink", "rmtree", "copy", "copy2", "copytree"}


def _module(name):
    return ast.parse((SRC / name).read_text(encoding="utf-8"),
                     filename=str(SRC / name))


def _write_actions_in(tree):
    """Write calls, and `open()` with a mode that can write."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", getattr(node.func, "id", ""))
        if name in _WRITE_ACTIONS:
            found.append(name)
        if name == "open":
            modes = list(node.args[1:2]) + [k.value for k in node.keywords
                                            if k.arg == "mode"]
            for mode in modes:
                if (isinstance(mode, ast.Constant)
                        and isinstance(mode.value, str)
                        and any(ch in mode.value for ch in "wax+")):
                    found.append("open(%s)" % mode.value)
    return found


class TestCriterion1NoRegistryWritePath(unittest.TestCase):
    """R3 §6 criterion 1 — no call path in the production package writes to
    the registry, established by AST reachability rather than by grep.

    THE PROOF IS IN TWO HALVES and both are mechanical:

      (a) exactly one module spells the governed path — already enforced by
          `test_registry_path_single_construction.py`, which is invariant 5
          of dec-registry-migration-2026-08-27;
      (b) that module performs no write action and exposes no function that
          performs one — enforced here.

    Together they close it: a write cannot target a path it cannot name.
    Neither half alone is sufficient, which is why the first half is cited
    rather than assumed — if that guard is deleted, this one still passes
    and would be proving nothing.
    """

    def test_the_only_write_action_is_inside_the_p3_seam(self):
        """AMENDED 2026-09-05 (Aaron's ruling). This asserted the boundary
        performed NO write. That was true and is deliberately no longer:
        `SUPPLEMENT_RUN_STARTED` is the ratified pre-start/post-start
        boundary and §D.3.2 gives it to the runner, but nothing could append
        it, so the first real N09 would have written supplement bytes with
        no P3 -- a state the failure vocabulary cannot describe (F2 requires
        P3; F1 would claim "nothing consumed").

        What replaces "no write" is "one write, and it is that one". The
        criterion the module still has to meet is that every write action in
        it belongs to `append_run_started` -- a second writer, or a write
        anywhere else in the module, fails here.
        """
        import ast
        import inspect

        from itsf.mc import registry_boundary as rb
        tree = _module("mc/registry_boundary.py")
        # WIDENED 2026-09-07 for QROS-CF F06, and the property is unchanged.
        # The write moved out of `append_run_started` into
        # `_compare_and_append`, because the check and the write had to share
        # ONE registry version: an OWNER_HOLD committed between the seam's two
        # independent reads was invisible to the hold check and preserved by
        # the second read, so the P3 landed after the hold on pre-hold state.
        # The seam is therefore two functions now, and this asserts what it
        # asserted before -- every write in the module belongs to that seam --
        # plus the thing that keeps the second function from becoming a
        # general writer: only the seam may call it.
        # The seam is two functions plus the lock that serializes them. The
        # lock's `unlink` removes its OWN lockfile, never the registry, and
        # the sharper assertion below is what pins that distinction: exactly
        # one registry-byte write exists in the module and it is the
        # compare-and-swap's.
        # WIDENED AGAIN 2026-09-07 for QROS-CF F06 ROUND TWO, and the
        # property is STILL unchanged. Astra's remaining finding was that a
        # sidecar lock protects the file only if every competing writer takes
        # it, and owner control had no sanctioned append at all -- so a hold
        # was filed by ad hoc mutation, taking no lock and reading no decided
        # snapshot. P3 was serialized against other P3s and nothing else.
        #
        # `_append_owner_row` is the missing half, and it is deliberately the
        # SAME primitive: it appears here as a member of the seam rather than
        # as an exception to it, and the caller assertion below still pins
        # that `_compare_and_append` has no callers outside the seam. Two
        # appenders, one serialized write. That is what changed; "every write
        # in this module belongs to the seam" did not.
        # WIDENED AGAIN 2026-09-07, PRE-CERT REPAIR, and the property is
        # STILL unchanged. The final-cert writer inventory found a
        # WORKFLOW-SUPPORTED writer that could not participate in
        # serialization even in principle: `s0/runner.append_registry_event_line`
        # receives the registry path as a PARAMETER and did `open("a")` +
        # `write`. The lock and the physical write lived only inside a private
        # function of this module, so there was nothing for it to call -- the
        # root cause was the primitive's LOCATION, not the writer's intent.
        #
        # `serialized_append` is that boundary, exposed. The physical write
        # moved into it and `_compare_and_append` became its compare-and-swap
        # caller. So the seam is one function wider and the invariant reads the
        # same: every write in this module belongs to the seam, and the one
        # physical write is in exactly one place.
        # WIDENED AGAIN 2026-09-07 (F06-OWNER-SEMANTICS). `serialized_start_append`
        # is the start-equivalent commit entry: it hands the applicable-hold
        # decision to the boundary as its `validate` callback, so the decisive
        # owner check and the physical write share ONE serialized decision. It
        # joins the seam for the same reason `_compare_and_append` did -- it is
        # part of the write path, not an exception to it.
        # WIDENED 2026-09-07 (final bounded repair, Root B). The physical
        # write became PRIVATE so the generic public entry could not be handed a
        # caller-controlled decision: the reviewer had committed raw start bytes
        # through `serialized_append(validate=None)`. Same lock, same single
        # write, one function further in.
        SEAM = ("append_run_started", "_append_owner_row",
                "_compare_and_append", "serialized_append",
                "serialized_start_append", "_physical_serialized_write")
        LOCK = "_AppendLock"
        funcs = {n.name: n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
        classes = {n.name: n for n in ast.walk(tree)
                   if isinstance(n, ast.ClassDef)}
        for name in SEAM:
            self.assertIn(name, funcs, "the P3 seam lost %s" % name)
        self.assertIn(LOCK, classes, "the append lock is gone")
        everywhere = _write_actions_in(tree)
        inside = [w for name in SEAM for w in _write_actions_in(funcs[name])]
        inside += _write_actions_in(classes[LOCK])
        self.assertTrue(inside, "the seam performs no write at all")
        self.assertEqual(sorted(everywhere), sorted(inside),
                         "registry_boundary writes outside the P3 seam"
                         ": %r" % sorted(set(everywhere) - set(inside)))
        self.assertEqual(
            ["write_bytes"],
            _write_actions_in(funcs["_physical_serialized_write"]),
            "the shared serialization boundary is the one place registry "
            "bytes are written")
        for appender in ("append_run_started", "_append_owner_row",
                         "_compare_and_append", "serialized_start_append",
                         "serialized_append"):
            self.assertEqual(
                [], _write_actions_in(funcs[appender]),
                "`%s` writes registry bytes directly again, bypassing the "
                "compare-and-swap" % appender)
        self.assertNotIn(
            "write_bytes", _write_actions_in(classes[LOCK]),
            "the append lock writes registry bytes")
        def _callers_of(target):
            return sorted(
                f.name for f in funcs.values()
                for c in ast.walk(f)
                if isinstance(c, ast.Call)
                and getattr(c.func, "id", getattr(c.func, "attr", None))
                == target)

        # F06-OWNER-SEMANTICS: `append_run_started` no longer calls the
        # compare-and-swap directly. It commits through
        # `serialized_start_append`, which carries its decided snapshot INTO the
        # serialized decision together with the applicable-hold check -- the
        # whole point of that repair. So the CAS's remaining caller is the owner
        # path, and the start path is asserted just below.
        self.assertEqual(["_append_owner_row"],
                         _callers_of("_compare_and_append"),
                         "the compare-and-swap has callers other than the "
                         "authorized owner appender, which would make it a "
                         "general registry writer")
        self.assertEqual(["append_run_started"],
                         _callers_of("serialized_start_append"),
                         "the start-equivalent commit entry has callers other "
                         "than the P3 seam inside this module")
        # THE REGISTERED CALLER SET for the exposed boundary. It knows no event
        # vocabulary, so an open door here would be a general registry writer.
        # In-module there is exactly one caller; the cross-module caller
        # (`s0/runner.append_registry_event_line`) is pinned by
        # `tests/test_qros_cf_f06_writer_completeness.py`, which is the test
        # that owns completeness across modules.
        self.assertEqual(["_compare_and_append"],
                         _callers_of("serialized_append"),
                         "the generic entry gained an in-module caller outside "
                         "the compare-and-swap")
        self.assertEqual(["serialized_append", "serialized_start_append"],
                         _callers_of("_physical_serialized_write"),
                         "the one physical write gained a caller outside the "
                         "two public entries")
        del rb, inspect

    def test_the_seam_is_the_only_exported_writer_and_writes_one_token(self):
        """A writer defined but unexported would still be one import away,
        and a writer that took the token as a PARAMETER would be a general
        registry writer wearing a narrow name."""
        import inspect

        from itsf.mc import registry_boundary as rb
        public = [n for n in dir(rb) if not n.startswith("_")]
        suspect = [n for n in public
                   if any(w in n.lower() for w in ("write", "append", "save",
                                                   "commit", "put", "emit"))
                   # an exception TYPE named for a refusal is not a writer;
                   # `AppendRefused` is how this seam says no.
                   and not (isinstance(getattr(rb, n), type)
                            and issubclass(getattr(rb, n), BaseException))]
        # QROS-CF F06 ROUND TWO: three exported writers, each naming ONE
        # event. The owner append's first shape took `token` as a parameter --
        # precisely the "general registry writer wearing a narrow name" this
        # test forbids -- so it was split into two narrow entries over a
        # private `_append_owner_row`. The rule below is unchanged and is now
        # applied to every exported writer rather than to one.
        # PRE-CERT REPAIR: `serialized_append` is exported deliberately, and
        # it is the ONE exception to the token rule below -- it takes raw bytes
        # precisely because it knows no event vocabulary. That makes it more
        # general, not less, which is why its callers are a registered set
        # (asserted above and in the completeness test) rather than a rule
        # about its signature.
        PRIMITIVE = "serialized_append"
        START_ENTRY = "serialized_start_append"
        self.assertEqual(["append_owner_hold", "append_owner_release",
                          "append_run_started", PRIMITIVE, START_ENTRY],
                         suspect,
                         "registry_boundary exposes %r; only the three narrow "
                         "event writers plus the shared boundary are "
                         "authorised" % suspect)
        for name in suspect:
            # The primitive takes raw bytes; the start entry takes raw bytes and
            # a run id. Neither takes an EVENT, which is the rule below.
            if name in (PRIMITIVE, START_ENTRY):
                continue
            params = inspect.signature(getattr(rb, name)).parameters
            for forbidden in ("event", "token", "event_type", "note", "row"):
                self.assertNotIn(forbidden, params,
                                 "%s takes the event as a caller-supplied "
                                 "value" % name)
        # and the primitive really is mechanism-only: no event-shaped parameter
        for mech in (PRIMITIVE, START_ENTRY):
            prim = inspect.signature(getattr(rb, mech)).parameters
            for forbidden in ("event", "token", "event_type", "note",
                              "trial_id"):
                self.assertNotIn(forbidden, prim,
                                 "%s grew an event-shaped parameter, which "
                                 "would make it an event writer" % mech)
        self.assertEqual("SUPPLEMENT_RUN_STARTED", rb.RUN_STARTED_TOKEN)

    def test_the_other_half_of_the_proof_still_exists(self):
        """Half (a) lives in another file. If it is ever deleted, this file
        stops proving what its docstring claims — so the dependency is
        asserted rather than remembered."""
        other = REPO / "tests" / "test_registry_path_single_construction.py"
        self.assertTrue(other.exists(),
                        "the single-construction-site guard is gone; without "
                        "it, 'the boundary does not write' no longer implies "
                        "'nothing writes the registry'")
        text = other.read_text(encoding="utf-8")
        self.assertIn("only_the_boundary_constructs_the_registry_path", text)


class TestCriterion2NoSubtreeIsCreated(unittest.TestCase):
    """R3 §6 criterion 2 — the two supplements subtrees still do not exist,
    and no code creates them.

    `DIRECTORY_CREATION_AUTHORIZED=NO`, and R3 §8 states as a fact about the
    repository that both subtrees are absent. That is a claim about DISK, so
    it is checked against disk."""

    def test_no_supplements_subtree_exists(self):
        # The premise. `assertEqual([], found)` is equally true of a walk
        # that visited nothing, so the walk is shown to work by finding a
        # directory that is certainly there.
        self.assertTrue([p for p in REPO.rglob("ops") if p.is_dir()],
                        "the tree walk found no ops/ directory, so it is not "
                        "walking this repository and proves nothing")
        found = [p.relative_to(REPO).as_posix()
                 for p in REPO.rglob("supplements")
                 if p.is_dir() and ".git" not in p.parts]
        self.assertEqual([], found,
                         "a supplements subtree exists while "
                         "DIRECTORY_CREATION_AUTHORIZED=NO: %r" % found)

    def test_the_supplement_directory_creator_is_named_and_counted(self):
        """REGISTERED, not zero. `day_strata_supplement` does contain a
        `mkdir`, and pretending otherwise would be worse than naming it: it
        sits inside `seal_supplement_test_only`, behind the gate-first
        refusal, and the count is pinned so a SECOND creator cannot appear
        without this going red."""
        tree = _module("mc/day_strata_supplement.py")
        creators = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(a in ("mkdir", "makedirs")
                       for a in _write_actions_in(node)):
                    creators.append(node.name)
        self.assertEqual(["seal_supplement_test_only"], sorted(creators),
                         "the set of directory creators in the supplement "
                         "module changed: %r" % sorted(creators))

    def test_the_production_entry_creates_nothing_before_it_refuses(self):
        """C_BUILD_1's assertion from R3 §1, applied where it is testable
        today: the exact set of files under a probe root is byte-identical
        before and after, and empty.

        This is the assertion R2 was HOLD'd for making about all three
        checkpoints at once. It holds for the first one, and only that one
        is claimed here."""
        import shutil
        import tempfile
        from itsf.mc import day_strata_supplement as dss
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        before = sorted(p.relative_to(root).as_posix()
                        for p in root.rglob("*"))
        with self.assertRaises(Exception):
            dss.run_supplement_production()
        after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
        self.assertEqual(before, after)
        self.assertEqual([], after)


class TestCriterion3TheRefusalNamesItsBlocker(unittest.TestCase):
    """R3 §6 criterion 3 — the load-bearing one.

        the scaffold's value is not that it refuses today, but that it
        cannot quietly be changed into not refusing.

    A refusal that says only "not authorised" can be weakened to a warning
    without any test noticing what was lost. A refusal that NAMES the token
    blocking it cannot: the name is the thing a mutation has to delete.

    MEASURED, and the measurement is recorded rather than smoothed over.
    The three production entries do not name the same KIND of token:

        run_supplement_production  -> SUPPLEMENT_EXECUTION_AUTHORIZED
                                      (an ND1 effect-boundary field)
        run_real_mc                -> MC_RUN_AUTHORIZED
        prepare_real_mc_input      -> MC_RUN_AUTHORIZED
                                      (a registry-grammar vocabulary item)

    Both are true and they are different facts: one says Aaron has not
    authorised the effect, the other says the registry grammar has no word
    for the event. Pinned as measured. Deciding whether the MC entries
    SHOULD also name `MC_EXECUTION_AUTHORIZED` would change gate semantics,
    which the rulings put outside the builder's reach.
    """

    #: token -> the entries whose refusal must name it.
    _EXPECTED = {
        "run_supplement_production": "SUPPLEMENT_EXECUTION_AUTHORIZED",
        "run_real_mc": "MC_RUN_AUTHORIZED",
        "prepare_real_mc_input": "MC_RUN_AUTHORIZED",
    }

    def _entries(self):
        from itsf.mc import consumer, day_strata_supplement, real_input
        return (day_strata_supplement.run_supplement_production,
                consumer.run_real_mc,
                real_input.prepare_real_mc_input)

    def test_every_production_entry_refuses(self):
        for fn in self._entries():
            with self.assertRaises(Exception, msg=fn.__name__) as caught:
                fn()
            self.assertNotIsInstance(
                caught.exception, AssertionError,
                "%s refused via a bare assert; an AssertionError is a bug "
                "report, not a governed refusal" % fn.__name__)

    def test_every_refusal_names_the_token_that_blocks_it(self):
        """WIDENED AT THE PRE-CERT REPAIR (R3). The launch refusal now arrives
        first for the entries that call the real-run gate with production
        flags, and it names ITS blocker, not the authorization token. The
        property below is about the authorization layer, so the launch is
        attested for the duration of each call -- the alternative, accepting
        any message, would have removed the check instead of relocating it."""
        import unittest.mock as mock

        from itsf import execution_identity as ei
        attested = ei.LaunchAttestation("/injected", 0, "injected", True)
        missing = []
        for fn in self._entries():
            text = ""
            try:
                with mock.patch.object(ei, "launch_attestation",
                                       lambda: attested):
                    fn()
            except Exception as exc:
                text = str(exc)
            token = self._EXPECTED[fn.__name__]
            if token not in text:
                missing.append("%s: expected %r, message was %r"
                               % (fn.__name__, token, text[:120]))
        self.assertEqual([], missing,
                         "a refusal stopped naming what blocks it, so a "
                         "mutation could weaken it without deleting any "
                         "name:\n  " + "\n  ".join(missing))

    def test_the_expected_tokens_are_not_invented(self):
        """A token this file made up would be satisfiable by editing this
        file. Each must be either an ND1 effect-boundary field or a real
        registry-grammar name."""
        from itsf.mc import mc_contract
        #: The MC grammar's own declared vocabulary — checked against the
        #: closed enum rather than against the file's words, because a
        #: substring match against source text would accept a token that
        #: appears only in a comment.
        declared = set(mc_contract.SPEC_BY_NAME) | set(mc_contract.EVENTS)
        declared |= set(mc_contract.AARON_ONLY_EVENTS)
        self.assertGreater(len(declared), 3,
                           "the MC grammar yielded %d event names; at that "
                           "count this proves nothing" % len(declared))
        for token in sorted(set(self._EXPECTED.values())):
            self.assertTrue(
                token in _ND1_FIELDS or token in declared,
                "%r is neither an ND1 effect-boundary field nor a declared "
                "event name in the MC grammar, so this file invented it and "
                "could satisfy itself by editing itself" % token)

    def test_the_refusal_is_deterministic(self):
        """R3 §6 criterion 4's positive form: with the fields NO, the whole
        path refuses — every time, identically. A refusal that varies is one
        that depends on something, and what it depends on could change."""
        for fn in self._entries():
            seen = []
            for _ in range(3):
                try:
                    fn()
                except Exception as exc:
                    seen.append((type(exc).__name__, str(exc)))
            self.assertEqual(1, len(set(seen)),
                             "%s refused differently across calls: %r"
                             % (fn.__name__, seen))


class TestCondition4StructuralOnlyCallGraph(unittest.TestCase):
    """R3 §4 — the allowed call graph, pinned at the AST level.

    The reviewer's High #3: "reuse the production S0 universe/data assembly
    path" can reasonably be read as reusing `RealChain._ensure`, which
    imports and calls `build_s0_dataset`, which calls `compute_day` for each
    day, which calls `labels_mod.d_open_from_ret_open30` — computing LABELS.
    That crosses the supplement's structural-only boundary.

    So the forbidden names are forbidden mechanically, not by comment."""

    _FORBIDDEN = ("build_s0_dataset", "compute_day", "iter_day_contexts",
                  "d_open_from_ret_open30", "_ensure")

    _ALLOWED_CHAIN = ("load_real", "build_universe",
                      "build_vol20_regime_mapping_from_universe",
                      "build_event_stratum_map")

    def _names_in(self, relpath):
        tree = _module(relpath)
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    docs.add(doc)
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                called.add(getattr(node.func, "attr",
                                   getattr(node.func, "id", "")))
            if isinstance(node, ast.Attribute):
                called.add(node.attr)
            if isinstance(node, ast.Name):
                called.add(node.id)
        return called, docs

    def _mc_modules(self):
        """Every module in the supplement's package.

        WIDENED 2026-08-29, before the row producer was written. This scan
        named two files — `day_strata_supplement.py` and
        `supplement_runner.py` — while the property it enforces is the
        structural-only boundary of the SUPPLEMENT, which is a property of
        the package. A new module added to `itsf/mc/` would have crossed
        the boundary freely and nothing would have said so.

        That is the fourth time in one evening a guard here was scoped to
        the files its author was looking at (the `$`-anchor sweep twice,
        `ANCHOR_MODULES` once). Measured before widening: no module in the
        package reaches any forbidden name, so this costs nothing today and
        covers whatever is added tomorrow."""
        root = REPO / "src" / "itsf" / "mc"
        mods = sorted(p for p in root.rglob("*.py") if p.name != "__init__.py")
        self.assertGreater(len(mods), 2,
                           "the package glob found %d modules, which is not "
                           "more than the old hand-written pair" % len(mods))
        return mods

    def test_no_module_in_the_package_reaches_a_forbidden_name(self):
        offenders = {}
        for path in self._mc_modules():
            called, _docs = self._names_in(
                path.relative_to(REPO / "src" / "itsf").as_posix())
            crossed = sorted(set(self._FORBIDDEN) & called)
            if crossed:
                offenders[path.name] = crossed
        self.assertEqual({}, offenders,
                         "these modules reach the structural-only boundary: "
                         "%r" % offenders)

    def test_the_two_modules_the_design_names_are_still_scanned(self):
        """The old pair, kept as a floor. A glob that silently stops
        matching would report clean over nothing."""
        seen = {p.name for p in self._mc_modules()}
        for name in ("day_strata_supplement.py", "supplement_runner.py"):
            with self.subTest(module=name):
                self.assertIn(name, seen)

    def test_the_forbidden_names_are_real(self):
        """Otherwise a typo makes the two guards above vacuous — the same
        lesson `test_the_forbidden_names_are_real_symbols` records for the
        hermetic-core guard."""
        defined = set()
        # scripts/ TOO. `_ensure` lives at scripts/s0_real_run.py:2650 — R3
        # §4 names that file and line explicitly, and the first version of
        # this scan looked only at the package. The guard reported it, which
        # is the guard working: a forbidden name it cannot find is a name it
        # cannot prove is forbidden.
        for path in list(SRC.rglob("*.py")) + list((REPO / "scripts").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    defined.add(node.name)
        missing = sorted(set(self._FORBIDDEN) - defined)
        self.assertEqual([], missing,
                         "these are forbidden but do not exist, so forbidding "
                         "them proves nothing: %r" % missing)

    def test_the_allowed_chain_still_exists_with_its_signatures(self):
        from itsf.s0 import context as s0ctx, dataset as s0ds
        from itsf.data import dbn_loader
        import inspect
        self.assertTrue(hasattr(dbn_loader.DevelopmentSignalLoader, "load_real"))
        self.assertTrue(callable(s0ctx.build_universe))
        for fn in (s0ds.build_vol20_regime_mapping_from_universe,
                   s0ds.build_event_stratum_map):
            self.assertTrue(callable(fn))
            self.assertTrue(inspect.signature(fn).parameters)

    def test_the_structural_only_evidence_is_still_in_the_docstring(self):
        """R3 cites the docstring's own sentence as the evidence that this
        path reads no bars. If that sentence goes, the citation is stale."""
        import inspect
        from itsf.s0 import dataset as s0ds
        doc = inspect.getdoc(s0ds.build_vol20_regime_mapping_from_universe) or ""
        self.assertIn("Nothing here reads bars", doc)


class TestVocabularyComparedAsSets(unittest.TestCase):
    """R3 §4's last measured note, and it is a warning about how to compare.

    `s0.dataset.EVENT_STRATA` and `mc.day_strata_supplement.EVENT_STRATA`
    hold the same five values in a DIFFERENT ORDER. R3 requires the
    implementation to compare them as SETS — an ordered comparison would go
    red while nothing is wrong, and a false red is how a real guard gets
    switched off."""

    def test_the_two_event_strata_vocabularies_are_set_equal(self):
        from itsf.s0 import dataset as s0ds
        from itsf.mc import day_strata_supplement as dss
        self.assertEqual(set(s0ds.EVENT_STRATA), set(dss.EVENT_STRATA))

    def test_and_the_order_really_does_differ(self):
        """The premise of the warning. If the orders ever coincide, the note
        above stops being a live caution and someone will 'simplify' the set
        comparison into an ordered one."""
        from itsf.s0 import dataset as s0ds
        from itsf.mc import day_strata_supplement as dss
        self.assertNotEqual(list(s0ds.EVENT_STRATA), list(dss.EVENT_STRATA),
                            "the orders now agree; the set-comparison rule "
                            "still holds but its measured justification is "
                            "gone, so re-measure before trusting it")


if __name__ == "__main__":
    unittest.main()
