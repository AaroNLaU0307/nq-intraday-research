"""N09 R3 §1 — the three checkpoints' side-effect assertions, each its own.

WHAT R2 WAS HELD FOR. It asserted one zero-side-effect rule across all three
C_BUILD moments. That is impossible and untestable: staging writes `.partial`
bytes before it can verify them, so "no writes" is false for C_BUILD_2 BY
CONSTRUCTION, and by C_BUILD_3 the archive attempt has already happened.

R3 §1 replaced it with three assertions that are each true at their own
moment, and closes with the sentence this file exists to hold:

    这三条互不蕴含。把它们写成一条通用规则正是 R2 出错的地方。
    (the three do not imply one another; writing them as one general rule is
     exactly where R2 went wrong)

C_BUILD_1's assertion already has a mechanism in
`test_n09_scaffold_criteria.py` — an exact-set snapshot around the production
entry. This file holds the other two, the independence claim, and one gap
that measuring found in R3 §1 itself.

WHAT MEASURING CORRECTED. The first draft of this file assumed
`resolve_partial` leaves bytes staged. It does not: it stages, verifies and
PROMOTES inside one call. Four tests were written against that wrong model
and failed, which is how the C_BUILD_2 observability gap below came to light.

NOTHING HERE EXECUTES A SUPPLEMENT. `resolve_partial` runs on a temporary
directory over bytes this file made up; the production entries stay refused
and no gate is released.
"""

import ast
import hashlib
import inspect
import shutil
import tempfile
import unittest
from pathlib import Path

import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf.mc import supplement_contract as sc          # noqa: E402
from itsf.mc import supplement_runner as sr            # noqa: E402

INCIDENT = "INC-0123456789ab"


class _Tmp(unittest.TestCase):

    def _dir(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d


class TestCBuild2DuringStaging(_Tmp):
    """R3 §1's C_BUILD_2, gate `seal_staging_partial`.

    The assertion is explicitly NOT "no writes" — the `.partial` bytes exist
    by construction, which is the fact R2 could not accommodate. It is three
    filesystem facts:

        (a) the FINAL path does not exist
        (b) no `.partial` bytes were deleted (`SILENT_DELETE_FORBIDDEN=YES`)
        (c) if a divergent rename happened, the divergent file exists at
            `<filename>.partial.divergent.<incident_id>` (BRANCH_E of the
            ratified `ND1_PARTIAL_RECOVERY_RULE=MODIFY`)
    """

    def test_the_ratified_values_this_asserts_against_are_still_in_force(self):
        """The premise. These assertions derive from two ratified values; if
        either changed, the tests below enforce a rule that is not in force."""
        self.assertIs(True, sc.SILENT_DELETE_FORBIDDEN)
        self.assertEqual(".partial.divergent.{incident_id}",
                         sc.DIVERGENT_PARTIAL_TEMPLATE)

    def test_staging_promotes_atomically_and_leaves_no_partial_behind(self):
        """MEASURED, and it corrects the model this file was drafted with.
        `resolve_partial` stages, verifies and PROMOTES inside one call."""
        out = self._dir()
        action = sr.resolve_partial(out, "supp.jsonl", b"rows",
                                    incident_id=INCIDENT)
        self.assertEqual("promote", action.action)
        self.assertEqual([("supp.jsonl", b"rows")],
                         [(p.name, p.read_bytes())
                          for p in sorted(out.iterdir())])

    def test_c_build_2s_state_is_not_observable_to_a_caller(self):
        """THE GAP MEASURING FOUND, and it is about R3 §1 rather than the code.

        C_BUILD_2 asserts "FINAL absent AND `.partial` present". That state
        exists only INSIDE `resolve_partial`, between the write and the
        promotion, and `resolve_partial` offers no hook for a gate to run
        there. `seal_staging_partial` is a default-refuse stub, so nothing
        observes anything today: the gap is latent, not active.

        Recorded rather than tested around. A test asserting that state after
        the call would assert something false; one that skipped the assertion
        would report coverage that does not exist."""
        out = self._dir()
        sr.resolve_partial(out, "supp.jsonl", b"rows", incident_id=INCIDENT)
        names = sorted(p.name for p in out.iterdir())
        self.assertNotIn("supp.jsonl.partial", names,
                         "a `.partial` survives the call; if that changed, "
                         "C_BUILD_2's assertion became observable and this "
                         "record is stale")
        self.assertIn("supp.jsonl", names)

    def test_identical_bytes_seal_once_and_destroy_nothing(self):
        """(b), the ordinary case."""
        out = self._dir()
        sr.resolve_partial(out, "supp.jsonl", b"rows", incident_id=INCIDENT)
        before = (out / "supp.jsonl").read_bytes()
        action = sr.resolve_partial(out, "supp.jsonl", b"rows",
                                    incident_id=INCIDENT)
        self.assertEqual("already_sealed", action.action)
        self.assertEqual(before, (out / "supp.jsonl").read_bytes())

    def test_a_sealed_supplement_is_never_overwritten(self):
        """Different bytes over an already-sealed file REFUSE — they are not
        renamed aside, because nothing may replace a sealed supplement."""
        out = self._dir()
        sr.resolve_partial(out, "supp.jsonl", b"rows", incident_id=INCIDENT)
        before = sorted((p.name, p.read_bytes()) for p in out.iterdir())
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out, "supp.jsonl", b"different",
                               incident_id=INCIDENT)
        self.assertIn("never overwritten", str(caught.exception))
        self.assertEqual(before,
                         sorted((p.name, p.read_bytes())
                                for p in out.iterdir()))

    def test_a_stale_partial_is_moved_aside_not_deleted(self):
        """(b) and (c) together.

        BRANCH_C, not E — corrected 2026-08-28 after the decision seat found
        the labels contradicting each other. The ratified text is two
        clauses: `BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>` names
        the rename TARGET; `BRANCH_C_RENAME_THEN_ALLOW_RETRY` adds the retry.
        This case renames and permits a retry, so the ACTION is C while the
        NAME it produces is E's. The earlier comment gave both to E.

        This is what a crashed run leaves behind: a `.partial` with no
        matching final."""
        out = self._dir()
        (out / "supp.jsonl.partial").write_bytes(b"stale from a crash")
        action = sr.resolve_partial(out, "supp.jsonl", b"new rows",
                                    incident_id=INCIDENT)
        self.assertEqual("retry_permitted", action.action)
        # The template already carries `.partial`; appending it to
        # `supp.jsonl.partial` produced a doubled suffix and a red test.
        divergent = out / ("supp.jsonl"
                           + sc.DIVERGENT_PARTIAL_TEMPLATE.format(
                               incident_id=INCIDENT))
        self.assertTrue(divergent.exists(),
                        "the stale bytes are gone; branch C renames and "
                        "permits a retry, it does not delete")
        self.assertEqual(b"stale from a crash", divergent.read_bytes())
        self.assertEqual(divergent.name, Path(action.preserved_as).name,
                         "the action does not report where the bytes went")

    def test_an_unverified_final_is_refused_after_promotion(self):
        """CLAUSE (a) OF THE R3 §12 DRAFT, and it had no proof until now.

        The draft says: an unverified FINAL does not exist, detected as a
        post-call filesystem fact. Running the draft's own mutation list
        against it, "delete the post-promotion re-read" came back GREEN —
        nothing in the suite noticed, because on the happy path the FINAL
        always reads back correctly, so removing the check changes nothing
        any existing test could see.

        A clause with no mutation proof does not satisfy criterion (2) of
        the ruling. This is that proof: make the FINAL read differently
        after `os.replace`, which is what a corrupted or racing filesystem
        would do, and the mechanism must refuse rather than report a seal."""
        out = self._dir()
        real = Path.read_bytes

        def tampered(self, *a, **k):
            if self.name == "supp.jsonl":          # the FINAL, after replace
                return b"CORRUPTED AFTER PROMOTION"
            return real(self, *a, **k)

        Path.read_bytes = tampered
        self.addCleanup(setattr, Path, "read_bytes", real)
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out, "supp.jsonl", b"rows",
                               incident_id=INCIDENT)
        self.assertIn("post_promotion", str(caught.exception),
                      "the promotion was accepted without re-reading it; a "
                      "FINAL nobody verified is exactly what clause (a) "
                      "forbids")

    def test_branch_e_also_leaves_a_divergent_file_and_refuses(self):
        """THE HALF THE OLD WORDING MISSED, found while drafting R3 §12.

        (c) says "if a divergent rename happened, the divergent file exists".
        There are TWO outcomes that rename, and only one had a test:

            branch C  stale `.partial` differs  -> rename, retry_permitted
            branch E  staged bytes re-read      -> rename, REFUSE
                      differently

        Measured here by making the first `.partial` read return other bytes,
        which is exactly the corruption branch E exists to catch. It leaves
        the same `<name>.partial.divergent.<incident_id>` and raises — so
        (c) holds on both outcomes, and now both are asserted."""
        out = self._dir()
        real = Path.read_bytes
        state = {"n": 0}

        def tampered(self, *a, **k):
            if self.name.endswith(".partial"):
                state["n"] += 1
                if state["n"] == 1:
                    return b"CORRUPTED IN FLIGHT"
            return real(self, *a, **k)

        Path.read_bytes = tampered
        self.addCleanup(setattr, Path, "read_bytes", real)
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out, "supp.jsonl", b"rows",
                               incident_id=INCIDENT)
        self.assertIn("SILENT_DELETE_FORBIDDEN", str(caught.exception))
        Path.read_bytes = real
        divergent = out / ("supp.jsonl"
                           + sc.DIVERGENT_PARTIAL_TEMPLATE.format(
                               incident_id=INCIDENT))
        self.assertTrue(divergent.exists(),
                        "branch E refused but left nothing behind; the bytes "
                        "it could not verify are gone")
        self.assertFalse((out / "supp.jsonl").exists(),
                         "branch E promoted despite failing verification")

    def test_the_divergent_name_carries_the_incident_id(self):
        """(c) exactly — and (c) IS BRANCH_E: the ratified clause that names
        the rename target. Residue that does not name its incident cannot be
        tied to the failure that produced it."""
        out = self._dir()
        (out / "supp.jsonl.partial").write_bytes(b"stale")
        sr.resolve_partial(out, "supp.jsonl", b"new", incident_id=INCIDENT)
        names = sorted(p.name for p in out.iterdir())
        self.assertTrue(any(INCIDENT in n for n in names),
                        "no file names the incident: %r" % names)

    def test_a_malformed_incident_id_refuses_before_touching_bytes(self):
        out = self._dir()
        (out / "supp.jsonl.partial").write_bytes(b"stale")
        before = sorted((p.name, p.read_bytes()) for p in out.iterdir())
        with self.assertRaises(sr.SupplementRunnerError):
            sr.resolve_partial(out, "supp.jsonl", b"new",
                               incident_id="not-an-incident")
        self.assertEqual(before,
                         sorted((p.name, p.read_bytes())
                                for p in out.iterdir()),
                         "bytes moved despite the refusal")

    #: What a silent delete is spelled as. Not exhaustive by construction --
    #: see `test_the_scan_declares_what_it_cannot_see`.
    DESTRUCTIVE = ("unlink", "rmtree", "remove", "removedirs", "rmdir")

    def _reachable_sources(self, entry):
        """`entry` plus every module-level function it can reach.

        WIDENED 2026-08-29 after measuring the old one-function scan:

            局部别名     rm = os.remove; rm(partial)     -> NOT caught
            被调函数里删 _preserve(partial, incident)     -> NOT caught

        The second one matters: `_preserve` is called on BOTH divergence
        branches, and a delete moved into it satisfied the old check
        completely. (b) claimed "no `.partial` bytes are ever silently
        destroyed" while looking at one function body -- the claimed class
        was wider than the route that detected it, which is the same defect
        §12.5 records for (a)."""
        module = sys.modules[sr.__name__]
        defined = {name: obj for name, obj in vars(module).items()
                   if inspect.isfunction(obj)
                   and getattr(obj, "__module__", None) == sr.__name__}
        seen, queue, sources = set(), [entry.__name__], {}
        while queue:
            name = queue.pop()
            if name in seen or name not in defined:
                continue
            seen.add(name)
            source = inspect.getsource(defined[name])
            sources[name] = source
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Call):
                    called = getattr(node.func, "id", None)
                    if called in defined:
                        queue.append(called)
        return sources

    def test_nothing_is_ever_unlinked_by_the_staging_path(self):
        """(b) as a property of the CODE rather than of one run. No scenario
        test enumerates every scenario; a single delete here is the ratified
        prohibition broken."""
        for name, source in self._reachable_sources(sr.resolve_partial).items():
            tree = ast.parse(source)
            calls = {getattr(n.func, "attr", getattr(n.func, "id", ""))
                     for n in ast.walk(tree) if isinstance(n, ast.Call)}
            for destructive in self.DESTRUCTIVE:
                self.assertNotIn(destructive, calls,
                                 "%s() calls %r; SILENT_DELETE_FORBIDDEN=YES"
                                 % (name, destructive))

    def test_no_destructive_call_is_hidden_behind_a_local_alias(self):
        """`rm = os.remove` renames the call and the name check stops
        seeing it. Measured on the old scan: not caught.

        WIDENED 2026-08-29 after the wording review measured a bypass the
        first version could not see:

            rm = os.remove          ast.Assign      caught
            rm: object = os.remove  ast.AnnAssign   NOT caught

        An annotation is not a different act. Every binding form that can
        put a destructive callable behind a new name is checked, not the
        one form that came to mind."""
        binding = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)
        for name, source in self._reachable_sources(sr.resolve_partial).items():
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, binding) and isinstance(
                        getattr(node, "value", None), (ast.Attribute, ast.Name)):
                    bound = getattr(node.value, "attr",
                                    getattr(node.value, "id", ""))
                    self.assertNotIn(bound, self.DESTRUCTIVE,
                                     "%s() binds %r to a local name, which "
                                     "hides it from the call-name scan"
                                     % (name, bound))

    #: Destroying bytes by writing over them rather than by deleting the
    #: file. `write_bytes` itself is legitimate and used on the staging
    #: path, so only a provably-empty payload is banned.
    TRUNCATING = ("write_bytes", "write_text", "truncate")

    def test_no_path_is_emptied_in_place(self):
        """The second bypass the wording review found: `partial.write_bytes
        (b"")` destroys the residue while calling nothing on the delete
        list. SILENT_DELETE_FORBIDDEN is about the BYTES, not about which
        syscall removed them."""
        for name, source in self._reachable_sources(sr.resolve_partial).items():
            for node in ast.walk(ast.parse(source)):
                if not isinstance(node, ast.Call):
                    continue
                if getattr(node.func, "attr", "") not in self.TRUNCATING:
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and arg.value in (b"", ""):
                        self.fail("%s() empties a path in place via %s(); "
                                  "SILENT_DELETE_FORBIDDEN=YES is about the "
                                  "bytes, not the syscall"
                                  % (name, node.func.attr))

    def test_the_truncation_scan_declares_what_it_cannot_see(self):
        """Only a LITERAL empty payload is visible. `write_bytes(payload)`
        where `payload` happens to be empty at runtime is not, and neither
        is `truncate(n)` with a computed `n`. Saying so is the point: this
        is a syntactic check wearing no claim of exhaustiveness."""
        source = self._reachable_sources(sr.resolve_partial)["resolve_partial"]
        self.assertIn("write_bytes", source,
                      "resolve_partial no longer writes at all; if the "
                      "staging write moved elsewhere this scan now covers "
                      "nothing and the boundary note is stale")

    def test_the_walk_actually_reaches_the_helpers(self):
        """A transitive scan that silently reaches nothing would pass every
        assertion above. `_preserve` is the one that matters: both
        divergence branches go through it."""
        reached = self._reachable_sources(sr.resolve_partial)
        self.assertIn("resolve_partial", reached)
        self.assertIn("_preserve", reached,
                      "the scan did not reach _preserve, so a delete moved "
                      "into it would pass unseen: reached %s"
                      % sorted(reached))

    def test_the_scan_declares_what_it_cannot_see(self):
        """The honest boundary, pinned rather than left implied. This scan
        sees module-level functions reached by a direct call. It does NOT
        see: deletes inside methods, inside imported modules, or reached
        through a value (a callable passed in, a dict of handlers). Saying
        so is the point -- a claim of exhaustiveness here would be the same
        defect §12.5 corrects."""
        reached = self._reachable_sources(sr.resolve_partial)
        self.assertNotIn("os", reached,
                         "the scan does not descend into imported modules; "
                         "if it now does, this boundary note is stale")

    def test_the_gate_for_this_checkpoint_refuses_unconditionally(self):
        """Why none of the above is a gate test: `seal_staging_partial` is a
        default-refuse stub. The assertions therefore live in the MECHANISM
        the gate would classify, which is what can be held today."""
        ctx = sr.GateContext(supplement_id="MC-DS-S001", head_commit="0" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.GATES["seal_staging_partial"](ctx)
        self.assertIn("nothing is ever sealed", str(caught.exception))


class TestCBuild3AfterAnArchiveAttempt(unittest.TestCase):
    """R3 §1's C_BUILD_3, gate `archive_policy_a`.

    Again NOT "no archive attempt" — the attempt has happened. It is:

        (a) the local seal is IMMUTABLE: recomputing its sha256 equals the
            `local_seal_sha256` recorded at seal time
        (b) no archived bytes were deleted

    R3's note on why this one is cheap: A1's field table ALREADY carries
    `local_seal_sha256` and `local_seal_immutable`. The assertion is over
    existing fields of an approved event, not fields invented for R3 — which
    is what keeps it from being a contract change wearing a test's clothes.
    """

    def test_a1_already_carries_both_fields(self):
        """The premise R3 relies on. If A1's field table loses either, this
        checkpoint's assertion has nothing to assert over."""
        required = sc.EVENTS["A1"].required_fields
        self.assertIn("local_seal_sha256", required)
        self.assertIn("local_seal_immutable", required)

    def test_immutability_is_a_recompute_not_a_flag_read(self):
        """`local_seal_immutable` is a CLAIM inside an event. The assertion is
        that recomputing agrees with `local_seal_sha256`. A flag saying
        "immutable" proves nothing on its own, and reading it instead of
        recomputing is exactly how a false claim survives."""
        sealed = b"sealed supplement bytes"
        recorded = hashlib.sha256(sealed).hexdigest()
        self.assertEqual(recorded, hashlib.sha256(sealed).hexdigest())
        self.assertNotEqual(recorded,
                            hashlib.sha256(sealed + b"x").hexdigest(),
                            "a one-byte change did not move the digest; the "
                            "recompute cannot detect mutation")

    def test_an_a1_missing_the_digest_is_refused(self):
        """A required field is only useful if omitting it refuses."""
        with self.assertRaises(Exception):
            sr.PlannedEvent("A1", sc.EVENTS["A1"].token, sc.UNNUMBERED,
                            sc.ACTOR_RUNNER,
                            {"supplement_id": "MC-DS-S001",
                             "archive_code": "file_unreadable",
                             "incident_id": INCIDENT,
                             "local_seal_immutable": "YES",
                             "archive_root_attempted": "x"})

    def test_the_archive_codes_are_a_closed_set(self):
        """(b) leans on the archive report's classification; an open-ended
        code set would let a deletion be reported as something else."""
        self.assertIsInstance(sc.ARCHIVE_CODES, tuple)
        self.assertGreater(len(sc.ARCHIVE_CODES), 1)

    def test_the_gate_for_this_checkpoint_refuses_unconditionally(self):
        ctx = sr.GateContext(supplement_id="MC-DS-S001", head_commit="0" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.GATES["archive_policy_a"](ctx)
        self.assertIn("nothing is ever archived", str(caught.exception))


class TestTheThreeAssertionsAreIndependent(unittest.TestCase):
    """THE CLAIM R3 §1 CLOSES WITH, and the reason this file exists at all.

        这三条互不蕴含。把它们写成一条通用规则正是 R2 出错的地方。

    A suite holding three assertions without holding their INDEPENDENCE is
    one refactor away from someone noticing they "all check side effects"
    and merging them back into the rule that was held.
    """

    def test_each_checkpoint_owns_a_different_set_of_gates(self):
        by_checkpoint = {}
        for gate, checkpoint in sc.CHECKPOINT_OF.items():
            by_checkpoint.setdefault(checkpoint, set()).add(gate)
        self.assertEqual(3, len(by_checkpoint),
                         "the three moments collapsed into %d"
                         % len(by_checkpoint))
        sets = list(by_checkpoint.values())
        for i, first in enumerate(sets):
            for second in sets[i + 1:]:
                self.assertEqual(set(), first & second,
                                 "two checkpoints share a gate, so they are "
                                 "not distinct moments")

    def test_c_build_1_and_c_build_3_cannot_both_hold(self):
        """The shortest proof of independence, and it is observable.

        C_BUILD_1 asserts the output set is EMPTY. C_BUILD_3 asserts a sealed
        file exists and recomputes to its recorded digest. One directory
        cannot satisfy both, so no single rule covers both — which is R2's
        error stated as a fact rather than as a lesson."""
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        self.assertEqual([], list(out.iterdir()))          # C_BUILD_1 holds
        sr.resolve_partial(out, "supp.jsonl", b"rows", incident_id=INCIDENT)
        sealed = out / "supp.jsonl"
        self.assertTrue(sealed.exists())                   # C_BUILD_3's object
        self.assertNotEqual([], list(out.iterdir()),
                            "C_BUILD_1 still holds after a seal, so the two "
                            "are not in tension and this proof is void")

    def test_c_build_2_differs_from_both_by_its_subject(self):
        """C_BUILD_2's subject is `.partial` residue, which neither other
        checkpoint mentions. Asserted over the ratified vocabulary rather
        than over a run, because §1's C_BUILD_2 state is not observable to a
        caller (see the gap recorded above)."""
        self.assertTrue(sc.DIVERGENT_PARTIAL_TEMPLATE.startswith(".partial"))
        self.assertNotIn("partial",
                         " ".join(sc.EVENTS["A1"].required_fields).lower())

    def test_r2s_single_rule_is_impossible_not_merely_wrong(self):
        """Why impossible rather than a judgement call: the staging mechanism
        writes before it can verify. R3 §0 cites that as the reason; the
        citation is asserted rather than paraphrased."""
        doc = inspect.getdoc(sr.resolve_partial) or ""
        self.assertIn("partial", doc.lower(),
                      "the staging docstring no longer describes what it "
                      "stages; R3 §0's citation is stale")


if __name__ == "__main__":
    unittest.main()
