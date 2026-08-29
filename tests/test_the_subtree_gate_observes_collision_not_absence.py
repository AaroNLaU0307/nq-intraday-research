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

    def test_the_only_mkdir_in_the_package_is_a_test_only_function(self):
        """Measured, and it is the sharper version of "the module never
        creates". There IS a `mkdir` in `mc/` -- in
        `seal_supplement_test_only`, whose name declares its scope. Nothing
        on the production path creates a directory, which is why the parent
        must be granted rather than conjured."""
        import ast
        import io as _io

        sites = []
        for path in sorted((REPO / "src" / "itsf" / "mc").rglob("*.py")):
            src = _io.open(path, encoding="utf-8").read()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and getattr(node.func, "attr", "") == "mkdir"):
                    continue
                owner = [f.name for f in ast.walk(tree)
                         if isinstance(f, ast.FunctionDef)
                         and f.lineno <= node.lineno <= f.end_lineno]
                owner.sort(key=len, reverse=True)
                sites.append((path.name, owner[0] if owner else "<module>"))
        self.assertEqual([("day_strata_supplement.py",
                           "seal_supplement_test_only")], sites,
                         "a new directory-creating site appeared: %s" % sites)

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
