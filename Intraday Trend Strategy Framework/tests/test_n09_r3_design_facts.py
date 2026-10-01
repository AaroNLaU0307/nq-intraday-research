"""N09 R3 — the facts about live code that the R3 design rests on.

WHY THIS FILE EXISTS. `ops/N09_EXECUTION_PATH_DESIGN_R3.md` is a design, and
a design makes assertions about the code it will be built on. Those
assertions rot silently: someone renames a function, widens a vocabulary, or
adds a route, and the document keeps claiming something that stopped being
true. R2 was HOLD'd partly for exactly that class of error — it attributed
the event-stratum mapping to `s0/context.py` when it lives in `s0/dataset.py`.

So every load-bearing claim R3 makes about live code is pinned here. If one
of these fails, R3's ground moved and R3 must be revised BEFORE anything is
built on it. The test names say which R3 section each claim backs.

WHAT THIS FILE IS NOT. It does not test the execution path — there is no
execution path. `BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`, and the five
C_BUILD gates all refuse unconditionally today. These tests pin the ground,
not the building.
"""

import ast
import inspect
import io
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr
from itsf.mc import day_strata_supplement as dss

REPO = Path(__file__).resolve().parents[1]


class TestRouterAIsDecidedByTheP3Boundary(unittest.TestCase):
    """R3 §2 router A: F1 vs F2 by `has_p3`, never by stage name."""

    def _failure(self, stage, gate):
        return sr.GateFailure(stage=stage, gate_name=gate,
                              error_class="SupplementRunnerError")

    def test_pre_start_gives_f1_and_post_start_gives_f2(self):
        for stage, gate in (("A_PRECHECK", "g9_hard_blocker"),
                            ("C_BUILD", "row_schema_blind")):
            pre = sr.plan_failure_event(
                self._failure(stage, gate), supplement_id="MC-DS-S001",
                incident_id="INC-0123456789ab", has_p3=False,
                attempts_dir="attempts/x")
            post = sr.plan_failure_event(
                self._failure(stage, gate), supplement_id="MC-DS-S001",
                incident_id="INC-0123456789ab", has_p3=True,
                residue_path="residue/x")
            self.assertEqual("F1", pre.short_id, f"{stage}/{gate} pre-P3")
            self.assertEqual("F2", post.short_id, f"{stage}/{gate} post-P3")

    def test_the_stage_name_does_not_change_the_route(self):
        """The same `has_p3` gives the same event across DIFFERENT stages —
        which is the whole content of the ratified P3-boundary rule and the
        thing R2 got backwards."""
        a = sr.plan_failure_event(
            self._failure("A_PRECHECK", "g9_hard_blocker"),
            supplement_id="MC-DS-S001", incident_id="INC-0123456789ab",
            has_p3=True, residue_path="residue/x")
        c = sr.plan_failure_event(
            self._failure("C_BUILD", "archive_policy_a"),
            supplement_id="MC-DS-S001", incident_id="INC-0123456789ab",
            has_p3=True, residue_path="residue/x")
        self.assertEqual(a.short_id, c.short_id)
        self.assertEqual("F2", a.short_id)


class TestRouterBMatrix(unittest.TestCase):
    """R3 §2 router B: the post-seal outcome matrix, including both
    INDETERMINATE cells. Every row of R3's table is one assertion here."""

    class _Report:
        def __init__(self, status, inventory=None, files=()):
            self.status, self.inventory, self.files = status, inventory, files

    class _Inv:
        def __init__(self, *v):
            (self.source_stable, self.staging_matches_source,
             self.dest_matches_source, self.source_stable_after_verify) = v

    def test_seal_failed_is_neither_p4_nor_a1(self):
        with self.assertRaises(sr.SupplementRunnerError) as cm:
            sr.decide_after_seal(local_seal_ok=False,
                                 archive_report=self._Report("archive_ok"))
        self.assertEqual("local_seal_failed", cm.exception.code)

    def test_archive_ok_gives_p4(self):
        self.assertEqual("P4", sr.decide_after_seal(
            local_seal_ok=True, archive_report=self._Report("archive_ok")))

    def test_classifiable_archive_failure_gives_a1_not_f2(self):
        """The ratified answer, and the one R2 got wrong."""
        r = self._Report("archive_failed", inventory=None)
        self.assertEqual("A1", sr.decide_after_seal(
            local_seal_ok=True, archive_report=r))

    def test_every_ruled_archive_code_is_reachable_and_routes_to_a1(self):
        cases = {
            "inventory_unavailable": self._Report("archive_failed"),
            "set_equality_refused": self._Report(
                "archive_failed", inventory=self._Inv(False, True, True, True),
                files=()),
            "set_equality_unreached": self._Report(
                "archive_failed", inventory=self._Inv(None, True, True, True),
                files=()),
        }
        for code, report in cases.items():
            self.assertEqual(code, sr.classify_archive_report(report))
            self.assertEqual("A1", sr.decide_after_seal(
                local_seal_ok=True, archive_report=report))

    def test_unclassifiable_archive_failure_is_indeterminate(self):
        """R3 §2: INDETERMINATE goes to Aaron — it must NOT quietly become
        F2 or A1. The refusal is the mechanism that makes that true."""
        r = self._Report("archive_failed",
                         inventory=self._Inv(True, True, True, True), files=())
        with self.assertRaises(sr.SupplementRunnerError) as cm:
            sr.classify_archive_report(r)
        self.assertEqual(sc.ARCHIVE_UNCLASSIFIED_CODE, cm.exception.code)

    def test_unknown_archive_status_is_indeterminate(self):
        with self.assertRaises(sr.SupplementRunnerError) as cm:
            sr.classify_archive_report(self._Report("who_knows"))
        self.assertEqual("archive_status_unknown", cm.exception.code)


class TestTheArchivePolicyGateDefect(unittest.TestCase):
    """R3 §2 names a real latent defect: `archive_policy_a` is a GATE, so a
    refusal there routes through router A to F2 — while the ratified policy
    requires A1. These tests pin the PRECONDITION, so the defect cannot be
    quietly resolved by someone editing the approved enum instead of adding
    R3's `ROUTER_OF` layer."""

    def test_archive_policy_a_is_still_a_c_build_gate(self):
        self.assertIn("archive_policy_a", sc.GATE_TABLE["C_BUILD"])

    def test_routing_it_as_an_ordinary_gate_contradicts_policy_a(self):
        """This is the defect, executed. Not a hypothetical."""
        planned = sr.plan_failure_event(
            sr.GateFailure(stage="C_BUILD", gate_name="archive_policy_a",
                           error_class="SupplementRunnerError"),
            supplement_id="MC-DS-S001", incident_id="INC-0123456789ab",
            has_p3=True, residue_path="residue/x")
        self.assertEqual("F2", planned.short_id)
        self.assertEqual("A1", sr.decide_after_seal(
            local_seal_ok=True,
            archive_report=TestRouterBMatrix._Report("archive_failed")))

    def test_the_gate_counts_r3_states(self):
        """R3 §2 says 'the other 22 gates route to A'."""
        self.assertEqual(13, len(sc.GATE_TABLE["A_PRECHECK"]))
        self.assertEqual(5, len(sc.GATE_TABLE["B_DERIVE"]))
        self.assertEqual(5, len(sc.GATE_TABLE["C_BUILD"]))
        total = sum(len(sc.GATE_TABLE[s]) for s in sc.STAGE_ENUM)
        self.assertEqual(23, total)
        self.assertEqual(23, len(sr.GATES))
        self.assertEqual(22, total - 1)


class TestTheScaffoldStillRefuses(unittest.TestCase):
    """R3 §6: BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY. Every C_BUILD gate
    refuses unconditionally today. If one of these starts passing, something
    was built that R3 does not authorise."""

    def test_all_five_c_build_gates_refuse_unconditionally(self):
        ctx = sr.GateContext(supplement_id="MC-DS-S001", head_commit="0" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        for name in sc.GATE_TABLE["C_BUILD"]:
            with self.assertRaises(sr.SupplementRunnerError,
                                   msg=f"{name} did not refuse"):
                sr.GATES[name](ctx)


class TestTheStructuralOnlyCallGraph(unittest.TestCase):
    """R3 §4. The allowed producers must exist; the prohibited ones must
    still be prohibited FOR THE STATED REASON, not by assertion."""

    def test_the_allowed_producers_exist_where_r3_says(self):
        from itsf.s0 import context as s0ctx
        from itsf.s0 import dataset as s0ds
        self.assertTrue(callable(s0ctx.build_universe))
        self.assertTrue(callable(s0ds.build_vol20_regime_mapping_from_universe))
        self.assertTrue(callable(s0ds.build_event_stratum_map))

    def test_the_vol_producer_reads_no_bars(self):
        """R3 quotes this docstring as the path's structural-only evidence.
        If the docstring claim is removed, R3's evidence is gone."""
        from itsf.s0 import dataset as s0ds
        doc = inspect.getdoc(s0ds.build_vol20_regime_mapping_from_universe)
        self.assertIn("Nothing here reads bars", doc)

    def test_build_s0_dataset_really_does_compute_labels(self):
        """R3 prohibits `build_s0_dataset` BECAUSE it calls `compute_day`,
        which computes labels. Pin the reason, not the verdict — if the
        reason ever stops holding, the prohibition needs rethinking rather
        than inheriting."""
        from itsf.s0 import dataset as s0ds
        src = inspect.getsource(s0ds.build_s0_dataset)
        called = {n.func.id for n in ast.walk(ast.parse(src.strip()))
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("compute_day", called)
        self.assertIn("d_open_from_ret_open30",
                      inspect.getsource(s0ds.compute_day))

    def test_the_real_chain_path_high_3_named_still_reaches_it(self):
        """Sol's High #3: `RealChain._ensure` imports `build_s0_dataset`.
        That is why R3 must name the loader path explicitly instead of
        saying 'reuse the production path'."""
        src = io.open(REPO / "scripts" / "s0_real_run.py",
                      encoding="utf-8").read()
        self.assertIn("from itsf.s0.dataset import build_s0_dataset", src)


class TestStratumVocabularies(unittest.TestCase):
    """R3 §4 requires comparison BY SET — the two tuples differ in order."""

    def test_the_two_event_vocabularies_are_set_equal_but_not_order_equal(self):
        from itsf.s0 import dataset as s0ds
        self.assertEqual(set(s0ds.EVENT_STRATA), set(dss.EVENT_STRATA))
        self.assertNotEqual(tuple(s0ds.EVENT_STRATA), tuple(dss.EVENT_STRATA),
                            "orders coincided — R3's by-set requirement is "
                            "now untested by this assertion; re-derive it")

    def test_the_row_schema_is_the_four_structural_fields(self):
        self.assertEqual(("trade_date", "year", "vol_stratum", "event_stratum"),
                         dss.ROW_FIELDS)
        self.assertEqual(("T1", "T2", "T3", "vol_na"), dss.VOL_STRATA)


class TestCanonicalJsonIsNamed(unittest.TestCase):
    """R3 §5 names `atoms.canonical_json` precisely because three same-body
    copies exist. Pin the count: if a fourth appears, R3's naming is no
    longer sufficient to prevent a second implementation."""

    def test_exactly_the_three_known_copies_exist(self):
        found = sorted(
            p.relative_to(REPO).as_posix()
            for p in (REPO / "src" / "itsf" / "mc").glob("*.py")
            if "sort_keys=True, ensure_ascii=True" in
            io.open(p, encoding="utf-8").read())
        self.assertEqual(
            ["src/itsf/mc/atoms.py", "src/itsf/mc/cold_reducer.py",
             "src/itsf/mc/day_strata_supplement.py"], found,
            "the canonical_json copy set changed — R3 §5 names one of three")

    def test_the_named_one_is_importable_and_canonical(self):
        from itsf.mc.atoms import canonical_json
        self.assertEqual('{"a":1,"b":2}', canonical_json({"b": 2, "a": 1}))


class TestTheAuthorizationBoundaryR3RestsOn(unittest.TestCase):
    """R3 §6 takes the default-refuse branch because of these eight fields.
    If any flips to YES, R3's scope choice must be revisited — by Aaron, not
    by inheritance."""

    EIGHT = ("SUPPLEMENT_EXECUTION_AUTHORIZED", "REAL_DATA_READ_AUTHORIZED",
             "DIRECTORY_CREATION_AUTHORIZED", "WRITE_PROBE_AUTHORIZED",
             "REGISTRY_EVENT_APPEND_AUTHORIZED",
             "EXPOSURE_EVENT_APPEND_AUTHORIZED", "MC_EXECUTION_AUTHORIZED",
             "STRATEGY_BUILD_AUTHORIZED")

    def test_all_eight_are_still_no_in_the_ratification_record(self):
        text = io.open(REPO / "ops" / "ND1_PROFILE_RATIFICATION.md",
                       encoding="utf-8").read()
        for field in self.EIGHT:
            self.assertIn(f"{field}=NO", text,
                          f"{field} is no longer NO — R3 §6 must be revisited")


if __name__ == "__main__":
    unittest.main()
