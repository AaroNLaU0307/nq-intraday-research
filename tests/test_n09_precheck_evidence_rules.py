"""N09 R3 §5 — the precheck evidence's four rules, each with a mechanism.

THE REVIEWER'S MEDIUM. R2 required the bundle-precheck table to land on disk
as run evidence and defined none of: serialization, landing point, seal
coverage, or what a write failure becomes on either side of P3. R3 §5 pinned
all four in prose. This is the half that was still prose.

THE ONE THAT MATTERS MOST is the last. Router A decides F1 vs F2 by the P3
boundary, which is right for gate failures — and measured here, a post-P3
failure through it returns F2. R3 §5 forbids exactly that for an evidence
write failure: after P3 the state is an INDETERMINATE half transfer, and
recording it as F2 records an unknown state as a known one.

NOTHING EXECUTES ANY OF THIS. The scaffold refuses before evidence is ever
written, so these rules describe a capability that does not exist yet. That
is deliberate: the rule lands before the capability, so the capability cannot
arrive without it.
"""

import ast
import unittest
from pathlib import Path

import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

SRC = REPO / "src" / "itsf"

from itsf.mc import supplement_contract as sc          # noqa: E402


class TestTheSerializerIsNamedAndTheSetCannotGrow(unittest.TestCase):
    """R3 §5's serialization rule, and the duplication it deliberately does
    not fix.

    R3: "本仓现存三份同体的 canonical_json … 不点名就等于默许第四份。
    三份并存本身是既有的第二份实现隐患，R3 不修它（超出本设计范围），
    只在此具名，以便它不因 N09 而扩大。"

    So the guard is a COUNT, not a zero. Three is the measured state; a
    fourth is what must not appear.
    """

    #: The four keyword arguments R3 §5 spells out.
    _REQUIRED = {"sort_keys": True, "ensure_ascii": True,
                 "allow_nan": False}

    def _canonical_json_bodies(self, *, ensure_ascii):
        """Every function whose body is a canonical `json.dumps`, FOUND BY
        ITS ARGUMENTS rather than by its name.

        By name would have missed one: R3 called the third
        `cold_reducer.canonical_json`, and it is actually `_canonical`. A
        fourth added under any name at all is caught by this; a fourth added
        under a different name would have walked past a name-based scan."""
        found = []
        for path in sorted(SRC.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                    continue
                for call in ast.walk(node):
                    if not (isinstance(call, ast.Call)
                            and getattr(call.func, "attr", "") == "dumps"):
                        continue
                    kw = {k.arg for k in call.keywords}
                    # `allow_nan` is deliberately NOT required here, and that
                    # is the finding: it is exactly where the three differ.
                    # Requiring it would have hidden the divergence by
                    # reporting a count of two.
                    if not {"sort_keys", "ensure_ascii", "separators"} <= kw:
                        continue
                    want = {k.arg: k.value for k in call.keywords}["ensure_ascii"]
                    if (isinstance(want, ast.Constant)
                            and want.value is ensure_ascii):
                        found.append("%s::%s"
                                     % (path.relative_to(SRC).as_posix(),
                                        node.name))
        return sorted(set(found))

    def test_exactly_three_serializers_use_the_mc_canonical_form(self):
        """THE COUNT IS PER CONTRACT, and the first draft of this test got
        that wrong — usefully.

        Counting every `json.dumps(sort_keys, ensure_ascii, separators)` in
        the package finds FIVE, not R3's three. The extra two are
        `runinfra.canonicalize_manifest_record` and
        `runinfra.append_manifest_record`, and they are not stray copies:
        they use `ensure_ascii=False`, deliberately, because the manifest is
        a UTF-8 artifact with its own frozen per-record schema. That is a
        DIFFERENT canonical form, not a fourth copy of this one.

        So the guard counts within the MC form. Conflating the two would
        have produced a permanently red test and, worse, an argument for
        "harmonising" two contracts that are meant to differ."""
        bodies = self._canonical_json_bodies(ensure_ascii=True)
        self.assertEqual(
            ["mc/atoms.py::canonical_json",
             "mc/cold_reducer.py::_canonical",
             "mc/day_strata_supplement.py::canonical_json"],
            bodies,
            "the set of MC canonical-JSON serializers changed. R3 §5 named "
            "the one N09 uses precisely so this set could not grow because "
            "of N09; a fourth here is that happening: %r" % bodies)

    def test_the_manifest_form_is_separate_and_deliberately_differs(self):
        """Pinned so nobody later "fixes" the inconsistency. `ensure_ascii`
        differs BY DESIGN: the MC form is ASCII-safe, the manifest form is
        UTF-8. Two contracts, not one contract implemented twice."""
        bodies = self._canonical_json_bodies(ensure_ascii=False)
        self.assertEqual(
            ["s0/runinfra.py::append_manifest_record",
             "s0/runinfra.py::canonicalize_manifest_record"],
            bodies,
            "the manifest canonical form's implementations changed: %r"
            % bodies)

    def test_r3_named_the_third_one_by_the_wrong_name(self):
        """RECORDED, not smoothed over. R3 §5 lists
        `cold_reducer.py:69` as a third `canonical_json`; the function there
        is `_canonical`. The substance — three identical bodies — is right,
        and the name is not. Pinned so a later reader who greps for
        `canonical_json` and finds two does not conclude R3 was wrong about
        the count."""
        text = (SRC / "mc" / "cold_reducer.py").read_text(encoding="utf-8")
        self.assertIn("def _canonical(", text)
        self.assertNotIn("def canonical_json(", text)

    def test_the_named_serializer_is_the_one_r3_names(self):
        self.assertEqual("itsf.mc.atoms.canonical_json",
                         sc.PRECHECK_EVIDENCE_SERIALIZER)
        from itsf.mc import atoms
        self.assertTrue(callable(atoms.canonical_json))

    def test_the_named_serializer_uses_the_spelled_out_parameters(self):
        import inspect
        from itsf.mc import atoms
        src = inspect.getsource(atoms.canonical_json)
        for key, value in self._REQUIRED.items():
            self.assertIn("%s=%s" % (key, value), src.replace(" ", ""))
        self.assertIn('separators=(",",":")', src.replace(" ", ""))

    def test_they_are_not_identical_and_this_is_where_they_differ(self):
        """MEASURED 2026-08-27, and it contradicts R3 §5.

        R3 says three 同体 (identical-bodied) serializers. They are not:

            atoms.canonical_json         allow_nan=False   -> refuses NaN
            cold_reducer._canonical      allow_nan=False   -> refuses NaN
            day_strata.canonical_json    (absent)          -> emits `NaN`

        `NaN`, `Infinity` and `-Infinity` are not valid JSON. The permissive
        one feeds `canonical_rows_digest`, the digest over supplement rows —
        so a digest could be taken over bytes that are not JSON, and a cold
        reader recomputing with either of the other two would RAISE rather
        than disagree.

        FOUND BY ACCIDENT, which is the part worth recording. The test below
        was written first, asserting "all three agree byte for byte", and it
        passed — because none of its cases contained NaN. Green for the wrong
        reason: the same defect class this repository spends its time hunting
        elsewhere, in a test written to hunt it.
        """
        from itsf.mc import atoms, cold_reducer
        from itsf.mc import day_strata_supplement as dss
        for value in (float("nan"), float("inf"), float("-inf")):
            case = {"x": value}
            with self.assertRaises(ValueError):
                atoms.canonical_json(case)
            with self.assertRaises(ValueError):
                cold_reducer._canonical(case)
            self.assertIsInstance(
                dss.canonical_json(case), str,
                "day_strata refuses too now; if that was deliberate this "
                "divergence record is stale and R3 §5 was right after all")

    def test_the_divergence_is_latent_because_no_row_field_is_a_float(self):
        """WHY IT IS NOT FIXED HERE. R3 §5 says the duplication is out of its
        scope — "R3 不修它" — and a digest function is not something to change
        on a builder's own judgement: every digest already sealed was taken
        with the current one.

        What IS in scope is proving the divergence cannot be reached today,
        and making that proof fail the moment it can. Supplement rows carry
        four fields, all strings or an integer year; no float can enter, so
        no NaN can. Add a float field and this goes red — which is exactly
        when the divergence stops being latent."""
        from itsf.mc import day_strata_supplement as dss
        self.assertEqual(("trade_date", "year", "vol_stratum",
                          "event_stratum"), dss.ROW_FIELDS,
                         "the supplement row shape changed; re-check whether "
                         "a float can now reach canonical_rows_digest, "
                         "because the permissive serializer would encode a "
                         "NaN into a sealed digest without complaint")

    def test_the_three_agree_on_every_json_valid_input(self):
        """R3 calls them 同体. On valid JSON they are — and that is the whole
        extent of it, per the test above."""
        from itsf.mc import atoms, cold_reducer
        from itsf.mc import day_strata_supplement as dss
        cases = [
            {"b": 1, "a": 2},
            {"z": [3, 2, 1], "y": {"k": "v"}},
            {"unicode": "中文", "esc": "a\"b\\c"},
            [], {}, {"nested": {"deep": {"deeper": [1, {"x": None}]}}},
            {"num": 1.5, "int": 10, "bool": True, "none": None},
        ]
        for case in cases:
            a = atoms.canonical_json(case)
            b = dss.canonical_json(case)
            c = cold_reducer._canonical(case)
            self.assertEqual(a, b, "atoms vs day_strata disagree on %r" % case)
            self.assertEqual(a, c, "atoms vs cold_reducer disagree on %r" % case)


class TestTheLandingPointAndItsSealCoverage(unittest.TestCase):
    """R3 §5's landing-point rule. The reason is the whole rule: evidence
    outside the seal inventory cannot be verified after the seal, and
    unverifiable evidence is the same as absent evidence."""

    def test_the_evidence_file_is_named_not_left_to_the_writer(self):
        self.assertEqual("mc_bundle_precheck.v1.json",
                         sc.PRECHECK_EVIDENCE_FILENAME)

    def test_the_name_carries_a_schema_version(self):
        """A versionless evidence filename is one that cannot change shape
        without silently invalidating every older run's evidence."""
        self.assertRegex(sc.PRECHECK_EVIDENCE_FILENAME, r"\.v\d+\.json$")

    def test_inventory_coverage_is_required_not_optional(self):
        self.assertIs(True, sc.PRECHECK_EVIDENCE_MUST_BE_IN_INVENTORY)

    def test_nothing_writes_it_today(self):
        """The scaffold refuses before any evidence is written, so the name
        must appear in the contract and NOWHERE as a write target. If it
        starts being written while the authorisation fields are NO, that is
        the scaffold's boundary being crossed."""
        modules = sorted(SRC.rglob("*.py"))
        self.assertGreater(len(modules), 20,
                           "the scan reached %d modules; 'nothing writes it' "
                           "over an empty scan is not a fact about the "
                           "package" % len(modules))
        writers = []
        for path in modules:
            if path.name == "supplement_contract.py":
                continue
            text = path.read_text(encoding="utf-8")
            if sc.PRECHECK_EVIDENCE_FILENAME in text:
                writers.append(path.relative_to(SRC).as_posix())
        self.assertEqual([], writers,
                         "the evidence filename appears outside the contract "
                         "in %r; the scaffold writes nothing" % writers)


class TestTheTimingIsProvableRatherThanDeclared(unittest.TestCase):
    """R3 §5: "绑定发生在 P3 之前这一点必须可证，不是声明."

    What makes it provable is a shape, not a comment: the decision takes the
    boundary as an ARGUMENT. A function that consulted a flag it had set
    itself would be declaring, not proving."""

    def test_the_binding_target_is_named(self):
        self.assertEqual("prepared.file_sha256", sc.PRECHECK_EVIDENCE_BOUND_TO)

    def test_the_binding_target_exists(self):
        """Otherwise the rule binds to nothing and reads as satisfied."""
        from itsf.mc import consumer
        import inspect
        src = inspect.getsource(consumer)
        self.assertIn("file_sha256", src)

    def test_the_decision_takes_the_boundary_as_an_argument(self):
        import inspect
        params = inspect.signature(sc.decide_evidence_write_failure).parameters
        self.assertIn("has_p3", params)
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY,
                         params["has_p3"].kind,
                         "has_p3 must be keyword-only; a positional boolean "
                         "at a call site is exactly the kind of argument that "
                         "gets passed the wrong way round")

    def test_the_decision_reads_no_state_of_its_own(self):
        """It must not consult a module global, a clock, or the filesystem —
        any of those would make the answer depend on something other than
        which side of P3 the caller is on."""
        import inspect
        src = inspect.getsource(sc.decide_evidence_write_failure)
        body = src.split('"""')[-1]
        for forbidden in ("time.", "datetime", "open(", "Path(", "os.",
                          "global "):
            self.assertNotIn(forbidden, body,
                             "the decision consults %r" % forbidden)


class TestAWriteFailureAfterP3IsNeverF2(unittest.TestCase):
    """THE ONE THE WHOLE SECTION IS FOR.

    R3 §5, verbatim:

        P3 之前落盘失败 -> 普通 pre-start 失败 -> 路由器 A -> F1
        P3 之后落盘失败 -> INDETERMINATE，走 Aaron
                          不追加 F2、不重试、停机上交
    """

    def test_before_p3_it_is_f1(self):
        self.assertEqual("F1", sc.decide_evidence_write_failure(has_p3=False))

    def test_after_p3_it_is_indeterminate(self):
        self.assertEqual("INDETERMINATE",
                         sc.decide_evidence_write_failure(has_p3=True))

    def test_after_p3_it_is_never_f2(self):
        """Stated as its own assertion rather than left implied by the one
        above. `INDETERMINATE` could be renamed; `not F2` is the property."""
        self.assertNotEqual("F2",
                            sc.decide_evidence_write_failure(has_p3=True))

    def test_router_a_really_would_have_said_f2(self):
        """THE PREMISE, measured rather than asserted. Without this, the rule
        above looks like a restatement of what the runner already does —
        and the reason it exists is precisely that the runner does the
        opposite for this failure class."""
        from itsf.mc import supplement_runner as sr
        failure = sr.GateFailure(stage="C_BUILD",
                                 gate_name="rows_digest_recompute",
                                 error_class="IOError",
                                 detail="precheck evidence write failed")
        planned = sr.plan_failure_event(
            failure, supplement_id="MC-DS-S001",
            incident_id="INC-0123456789ab", has_p3=True,
            attempts_dir="a", residue_path="r")
        self.assertEqual("F2", planned.short_id,
                         "Router A no longer returns F2 after P3; if that "
                         "changed, re-read whether this separate rule is "
                         "still needed rather than assuming it is")

    def test_and_before_p3_the_two_agree(self):
        """They differ on exactly one side of the boundary. If they differed
        on both, this would be a second routing policy rather than one
        exception to an existing one."""
        from itsf.mc import supplement_runner as sr
        failure = sr.GateFailure(stage="C_BUILD",
                                 gate_name="rows_digest_recompute",
                                 error_class="IOError",
                                 detail="precheck evidence write failed")
        planned = sr.plan_failure_event(
            failure, supplement_id="MC-DS-S001",
            incident_id="INC-0123456789ab", has_p3=False,
            attempts_dir="a", residue_path="r")
        self.assertEqual(planned.short_id,
                         sc.decide_evidence_write_failure(has_p3=False))

    def test_the_indeterminate_outcome_has_no_registry_event(self):
        """INDETERMINATE is not an event type and must not become one by
        accident: R3 says it goes to Aaron, and an event would be a record
        of a decision nobody made."""
        self.assertNotIn("INDETERMINATE", sc.EVENTS)


if __name__ == "__main__":
    unittest.main()
