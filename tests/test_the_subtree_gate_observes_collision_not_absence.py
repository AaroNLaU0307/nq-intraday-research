"""What `supplement_subtree_absent` actually does, pinned.

FOUND ON 2026-08-29, immediately after Aaron authorised creating the two
`supplements\\` parents. I went to measure what the grant had unlocked and
proved the opposite of what the governance record said.

Two documents stated, one of them in bold:

    `supplement_subtree_absent` 是 A_PRECHECK 的 13 道门之一
    ——子树不存在时它拒绝，且模块永不自行创建。
    ("...it REFUSES when the subtree does not exist")

Measured: the gate passes with both parents absent, passes with one
present and one absent, and passed before the directories existed. It has
never refused on absence. What it actually does is plan the real target
`<root>/supplements/<id>_<UTC>` and let the planner refuse a COLLISION, a
reparse point, or an escape -- which is what `N09_EXECUTION_PATH_DESIGN_R2`
described correctly all along ("今日只**观察**目标不存在"). The design
document was right and the governance documents were wrong.

WHAT THIS DID AND DID NOT COST. The returned ruling
`dec-four-owner-2026-08-27` asked what FORM the five authorization slots
should take. It answered: closed enumeration, no wildcards, bound to paths
not commits, four fail-closed conditions. None of that depends on the false
sentence, which was motivation rather than premise -- so the ruling stands.
What it cost is that the grant was described as unblocking a gate, and it
unblocks no gate. The thirteen A_PRECHECK gates give byte-identical results
before and after the directories existed.

It is still needed, for a different and real reason: the run directory
`<supplements>/<id>_<UTC>` cannot be created under a no-implicit-parents
discipline unless the parent already exists, and no PRODUCTION path creates
directories. The precise version, measured rather than asserted: there is
exactly one `mkdir` in `mc/`, inside `seal_supplement_test_only`, and it has
no production caller. That call passes `parents=True, exist_ok=True`, so the
"the module never creates" guarantee rests on the caller rather than on the
callee -- a naming convention with a measurement behind it, not a mechanism.
Both halves are executed below.

So this file replaces the prose claim with an executed one, in both
directions, and refuses to let the false sentence come back.
"""

import dataclasses as dc
import tempfile
import unittest
from pathlib import Path

from itsf.mc import supplement_runner as sr

REPO = Path(__file__).resolve().parents[1]
SID = "MC-DS-S001"
STAMP = "20260829T000000Z"
GATE = "supplement_subtree_absent"

#: The sentence that was false. Kept as a literal so it cannot quietly
#: return to a governance file.
FALSE_CLAIM = "子树不存在时它拒绝"
CORRECTION_MARK = "订正-SUBTREE-GATE-2026-08-29"
GOVERNANCE = ("ops/DIRECTORY_CREATION_GRANTS.md",
              "ops/DECISION_PACKET_FOUR_OWNER_ITEMS.md",
              "ops/P2_AUTHORIZATION_PREPARATION.md")


def _ctx(runs_root, archive_root, stamp=STAMP):
    return sr.GateContext(
        supplement_id=SID, head_commit="a" * 40, registry_text="",
        runs_root=Path(runs_root), archive_root=Path(archive_root),
        utc_stamp=stamp)


class TestAbsenceIsNotWhatItRefusesOn(unittest.TestCase):
    """The three cases that disprove the governance sentence."""

    def test_it_passes_with_NEITHER_parent_present(self):
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            sr.GATES[GATE](_ctx(a, b))          # must not raise

    def test_it_passes_with_only_ONE_parent_present(self):
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            (Path(a) / "supplements").mkdir()
            sr.GATES[GATE](_ctx(a, b))

    def test_it_passes_with_BOTH_parents_present(self):
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            (Path(a) / "supplements").mkdir()
            (Path(b) / "supplements").mkdir()
            sr.GATES[GATE](_ctx(a, b))


class TestWhatItDoesRefuseOn(unittest.TestCase):
    """A gate that never refuses is not a gate. These are the real ones."""

    def test_a_COLLIDING_target_refuses(self):
        """The property the name states: the planned target must be ABSENT."""
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            (Path(a) / "supplements" / ("%s_%s" % (SID, STAMP))).mkdir(
                parents=True)
            with self.assertRaises(sr.SupplementRunnerError) as caught:
                sr.GATES[GATE](_ctx(a, b))
        self.assertIn(GATE, str(caught.exception))

    def test_a_collision_in_the_ARCHIVE_root_refuses_too(self):
        """Both roots, not just the first -- a half-checked pair would let
        the archive copy land on top of something."""
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            (Path(b) / "supplements" / ("%s_%s" % (SID, STAMP))).mkdir(
                parents=True)
            with self.assertRaises(sr.SupplementRunnerError):
                sr.GATES[GATE](_ctx(a, b))

    def test_a_missing_ROOT_refuses(self):
        """The root -- not the `supplements` child -- is the thing whose
        absence is fatal. That distinction is the whole finding."""
        with tempfile.TemporaryDirectory() as a:
            gone = Path(a) / "no-such-root"
            with self.assertRaises(sr.SupplementRunnerError) as caught:
                sr.GATES[GATE](_ctx(a, gone))
        self.assertIn("plan_root_absent", str(caught.exception))

    def test_no_utc_stamp_refuses(self):
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            with self.assertRaises(sr.SupplementRunnerError) as caught:
                sr.GATES[GATE](_ctx(a, b, stamp=""))
        self.assertIn("cannot be planned without it", str(caught.exception))


class TestTheGrantStillHasAReason(unittest.TestCase):
    """It unblocks no gate. It IS still required, and this states why in a
    form that can be checked rather than believed."""

    #: Every `mkdir` site in `mc/`, and what makes each one safe. WIDENED
    #: on 2026-08-29 when `day_strata_dryrun` added the second -- the guard
    #: fired on my own new code, which is what it is for. The widening is
    #: not a rubber stamp: entry (2) is checked STRUCTURALLY below, by
    #: proving the refusal runs before the mkdir.
    MKDIR_SITES = {
        ("day_strata_supplement.py", "seal_supplement_test_only"): "TEST_ONLY",
        ("day_strata_dryrun.py", "rehearse"): "GUARDED_BY_ASSERT_SYNTHETIC",
    }

    def test_every_mkdir_site_in_the_package_is_a_KNOWN_one(self):
        """The property is "no PRODUCTION path creates a directory", and
        `not any mkdir` was a proxy for it. The proxy broke when a
        rehearsal legitimately needed scratch dirs, so the check moved to
        the property: every site is enumerated with what makes it safe."""
        import ast
        import io as _io

        sites, scanned = set(), 0
        for path in sorted((REPO / "src" / "itsf" / "mc").rglob("*.py")):
            scanned += 1
            tree = ast.parse(_io.open(path, encoding="utf-8").read())
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and getattr(node.func, "attr", "") == "mkdir"):
                    continue
                owner = [f.name for f in ast.walk(tree)
                         if isinstance(f, ast.FunctionDef)
                         and f.lineno <= node.lineno <= f.end_lineno]
                owner.sort(key=lambda n: len(n), reverse=True)
                sites.add((path.name, owner[0] if owner else "<module>"))
        # PREMISE, caught by my own vacuous-guard detector on the first
        # draft: `[] == unknown` passes over nothing if the scan found
        # nothing, and "no unknown sites" would then mean "I did not look".
        self.assertGreater(scanned, 20,
                           "the package glob found %d files" % scanned)
        self.assertGreaterEqual(
            len(sites), 2,
            "the scan found %d mkdir sites; there are known to be two, so a "
            "smaller number means the matcher stopped working, not that the "
            "code stopped creating directories" % len(sites))
        unknown = sorted(sites - set(self.MKDIR_SITES))
        self.assertEqual(
            [], unknown,
            "a new directory-creating site appeared in mc/: %s\nEnumerate "
            "it in MKDIR_SITES with what makes it safe, and add the check "
            "that proves it -- an entry with no proof is a rubber stamp."
            % unknown)
        self.assertEqual(sorted(self.MKDIR_SITES), sorted(sites),
                         "MKDIR_SITES names a site that no longer exists")

    def test_the_rehearsals_mkdir_runs_AFTER_the_governed_root_refusal(self):
        """The proof behind `GUARDED_BY_ASSERT_SYNTHETIC`, structural
        rather than trusted. If the mkdir ever moved above the refusal, a
        scratch_root inside a governed root would be created and only THEN
        rejected -- leaving behind the thing the refusal exists to prevent."""
        import ast
        import io as _io

        tree = ast.parse(_io.open(
            REPO / "src" / "itsf" / "mc" / "day_strata_dryrun.py",
            encoding="utf-8").read())
        fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
              and n.name == "rehearse"]
        self.assertEqual(1, len(fn), "rehearse is gone or duplicated")
        guard = [n.lineno for n in ast.walk(fn[0]) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "_assert_synthetic"]
        mkdirs = [n.lineno for n in ast.walk(fn[0]) if isinstance(n, ast.Call)
                  and getattr(n.func, "attr", "") == "mkdir"]
        self.assertEqual(1, len(guard), "the refusal call is gone: %s" % guard)
        self.assertTrue(mkdirs, "no mkdir found — this check now proves "
                                "nothing and should be removed with the "
                                "MKDIR_SITES entry it backs")
        self.assertLess(max(guard), min(mkdirs),
                        "a directory is created before the governed-root "
                        "refusal runs")

    def test_and_that_refusal_actually_rejects_a_governed_scratch_root(self):
        """The premise. A guard call in the right PLACE that rejected
        nothing would satisfy the structural check above."""
        from itsf.mc import day_strata_dryrun as dry

        class _Synthetic:
            test_only = True

        with self.assertRaises(dry.DryRunRefused):
            dry._assert_synthetic(_Synthetic(),
                                  dry._GOVERNED[0] / "supplements" / "x")
        dry._assert_synthetic(_Synthetic(), REPO)      # an ordinary path

    def test_and_no_production_caller_reaches_that_function(self):
        """THE RESIDUAL, stated rather than hidden. That `mkdir` passes
        `parents=True, exist_ok=True`, so pointed at a governance root it
        WOULD create the `supplements` parent itself. The "module never
        creates" guarantee therefore rests on the CALLER, not on the
        callee -- it is a naming convention with a measurement behind it,
        not a mechanism. This is the measurement."""
        import ast
        import io as _io

        def scan(root):
            hits, files = [], 0
            for path in sorted(root.rglob("*.py")):
                files += 1
                tree = ast.parse(_io.open(path, encoding="utf-8").read())
                for node in ast.walk(tree):
                    name = (getattr(node.func, "attr", None)
                            or getattr(node.func, "id", None)
                            ) if isinstance(node, ast.Call) else None
                    if name == "seal_supplement_test_only":
                        hits.append("%s:%d" % (path.name, node.lineno))
            return hits, files

        # PREMISE, and not a token one. An empty result means "no production
        # caller" only if the scan ran and the matcher works. The same scan
        # over tests/ -- where the function IS called -- proves both.
        test_callers, test_files = scan(REPO / "tests")
        self.assertGreater(test_files, 20)
        self.assertGreater(
            len(test_callers), 0,
            "the scan found no caller even in tests/, where the function is "
            "certainly called -- so an empty result over src/ would mean the "
            "matcher is broken, not that production is clean")

        callers, src_files = scan(REPO / "src")
        self.assertGreater(src_files, 20)
        self.assertEqual(
            [], callers,
            "production code calls seal_supplement_test_only at %s. It "
            "creates directories with parents=True, so a production caller "
            "given a governance root would create the `supplements` parent "
            "outside any authorization." % callers)


class TestTheFalseClaimIsCORRECTED_notErased(unittest.TestCase):
    """`DIRECTORY_CREATION_GRANTS.md` is `APPEND_ONLY=YES -- 只追加，永不编辑`.
    So the false sentence STAYS: erasing it would be editing an append-only
    governance record, and would also hide that a decision packet carried
    it. What must exist is a correction that names it."""

    def test_every_file_carrying_the_claim_also_carries_its_correction(self):
        uncorrected = []
        for rel in GOVERNANCE:
            text = (REPO / rel).read_text(encoding="utf-8")
            if FALSE_CLAIM in text and CORRECTION_MARK not in text:
                uncorrected.append(rel)
        self.assertEqual(
            [], uncorrected,
            "these files state that the gate refuses when the subtree is "
            "absent, with no correction: %s -- measured 2026-08-29, it "
            "passes with both parents absent. It refuses on a COLLIDING "
            "target, a missing ROOT, a reparse point, an escape, or a "
            "missing UTC stamp -- never on the parent being absent."
            % uncorrected)

    def test_the_correction_names_what_was_wrong_and_what_is_true(self):
        text = (REPO / "ops" / "DIRECTORY_CREATION_GRANTS.md").read_text(
            encoding="utf-8")
        self.assertIn(CORRECTION_MARK, text)
        for required in ("dec-four-owner-2026-08-27", "碰撞", "不解开任何一道门"):
            with self.subTest(phrase=required):
                self.assertIn(required, text)

    def test_the_design_document_that_was_RIGHT_still_says_so(self):
        """The one document that had it correct. If it ever drifts to match
        the others, the evidence that this was a documentation error rather
        than a behaviour change goes with it."""
        text = (REPO / "ops" / "N09_EXECUTION_PATH_DESIGN_R2.md").read_text(
            encoding="utf-8")
        self.assertIn("只**观察**目标不存在", text)


if __name__ == "__main__":
    unittest.main()
