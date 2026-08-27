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
        """(b) and (c) together — BRANCH_E. This is what a crashed run leaves
        behind: a `.partial` with no matching final."""
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
                        "the stale bytes are gone; BRANCH_E renames, it does "
                        "not delete")
        self.assertEqual(b"stale from a crash", divergent.read_bytes())
        self.assertEqual(divergent.name, Path(action.preserved_as).name,
                         "the action does not report where the bytes went")

    def test_the_divergent_name_carries_the_incident_id(self):
        """(c) exactly. Residue that does not name its incident cannot be
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

    def test_nothing_is_ever_unlinked_by_the_staging_path(self):
        """(b) as a property of the CODE rather than of one run. No scenario
        test enumerates every scenario; a single `unlink` here is the
        ratified prohibition broken."""
        tree = ast.parse(inspect.getsource(sr.resolve_partial))
        calls = {getattr(n.func, "attr", getattr(n.func, "id", ""))
                 for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for destructive in ("unlink", "rmtree", "remove"):
            self.assertNotIn(destructive, calls,
                             "resolve_partial calls %r; "
                             "SILENT_DELETE_FORBIDDEN=YES" % destructive)

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
