"""The supplement's inputs must be S0-T001's inputs, not a second authority.

WHAT WENT WRONG. `MC-DS-S001` reached P4 and was then refused by an
INDEPENDENT verifier: `headline_replay_mismatch`, 8 of 2842 days carrying a
stratum label different from the one S0-T001 stratified on. The chain was
retired (F3) and `MC-DS-S002` registered as its successor.

THE ROOT CAUSE WAS NOT THOSE EIGHT DAYS. The supplement is a RECONSTRUCTION
of the table S0-T001 used -- there is nothing to inherit, because the S0 seal
says so itself ("the per-day vol labels are producer-derived, with no
close-series atom here to re-derive them"). A reconstruction is only worth
anything if it reproduces what it reconstructs, and this one was built on a
NEW, separately-written input path that differed from S0-T001's in three
ways at once:

    roll intervals    frozen gate1/symbology CSV   vs  live DBN + coalesce
    event calendar    UNSCHEDULED_FOMC + raw_multi vs  both left EMPTY
    session schedule  exchange close, condition    vs  capped 960, degraded
                      .json                            re-derived from bars

Two independently-correct derivations of one input are still two
authorities, and roll transitions move vol20, which moves the tercile
boundaries, which moves the label of any day sitting near one.

WHAT THIS FILE LOCKS. Not the eight dates -- they appear nowhere here, and a
test that pinned them would be a patch wearing a regression's clothes. What
is pinned is the PROVENANCE: each builder reads what S0-T001 read, and
`src/` grew no second source of truth.

DUPLICATION, DISCLOSED. `src/` may not import `scripts/`, so
`UNSCHEDULED_FOMC` and the symbology path are restated in
`mc/production_inputs.py`. The drift tests below read both back out of
`scripts/s0_real_run.py` by AST, so the copies cannot part company silently.
Extracting a shared loader is N09-v2 work and deliberately not done here.
"""

import ast
import csv
import json
import unittest
from pathlib import Path

from itsf.mc import production_inputs as pi

REPO = Path(__file__).resolve().parents[1]
S0_SCRIPT = REPO / "scripts" / "s0_real_run.py"


def _s0_assign(name):
    """The literal value assigned to `name` at module level in the S0 run
    script, read without importing it."""
    tree = ast.parse(S0_SCRIPT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return node.value
    raise AssertionError("%s is not assigned at module level in %s -- the "
                         "drift check has nothing to compare against"
                         % (name, S0_SCRIPT.name))


def _code_of(fn):
    """A function's source with its docstring and comments removed.

    MEASURED THE HARD WAY: the first version of these guards grepped the raw
    source, so a docstring that NAMES the thing it stopped doing ("it used to
    cap at RTH_CLOSE_MINUTE") counted as still doing it. A guard that reads
    prose is testing the prose.
    """
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(fn).lstrip())
    node = tree.body[0]
    body = node.body[1:] if (isinstance(node.body[0], ast.Expr)
                             and isinstance(node.body[0].value, ast.Constant)
                             and isinstance(node.body[0].value.value, str)
                             ) else node.body
    return chr(10).join(ast.unparse(stmt) for stmt in body)


class TestRollProvenance(unittest.TestCase):

    def test_it_reads_the_frozen_symbology_csv_s0_used(self):
        self.assertTrue(pi.SYMBOLOGY_CSV.is_file(), pi.SYMBOLOGY_CSV)
        self.assertEqual(("gate1", "symbology", "nq_v0_mapping.csv"),
                         pi.SYMBOLOGY_CSV.parts[-3:])

    def test_that_path_is_the_one_the_s0_script_names(self):
        node = _s0_assign("SYMBOLOGY_CSV")
        parts = {n.value for n in ast.walk(node)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        self.assertEqual(set(pi.SYMBOLOGY_CSV.parts[-3:]), parts)

    def test_every_interval_carries_the_frozen_rows_four_fields(self):
        rows = list(csv.DictReader(
            open(pi.SYMBOLOGY_CSV, newline="", encoding="utf-8")))
        got = pi.build_roll_intervals()
        self.assertEqual(len(rows), len(got))
        for row, interval in zip(rows, got):
            with self.subTest(start=row["start_date_utc"]):
                self.assertEqual(row["start_date_utc"],
                                 interval.start_date_utc)
                self.assertEqual(row["end_date_utc_excl"],
                                 interval.end_date_utc_excl)
                self.assertEqual(row["raw_symbol"], interval.raw_symbol)
                self.assertEqual(int(row["instrument_id"]),
                                 interval.instrument_id)

    def test_raw_symbol_is_populated_not_defaulted_away(self):
        """The previous version constructed `RollInterval` with three
        keywords, so every `raw_symbol` was the empty default -- a silent
        field loss that no shape check would have caught."""
        self.assertTrue(all(i.raw_symbol for i in pi.build_roll_intervals()))

    def test_the_live_vendor_derivation_is_no_longer_the_authority(self):
        body = _code_of(pi.build_roll_intervals)
        for second_source in ("read_vendor_intervals", "coalesce",
                              "DBNStore", "metadata"):
            self.assertNotIn(second_source, body, second_source)


class TestEventProvenance(unittest.TestCase):

    def test_unscheduled_fomc_matches_the_s0_constant_exactly(self):
        node = _s0_assign("UNSCHEDULED_FOMC")
        s0 = tuple(n.value for n in ast.walk(node)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str))
        self.assertEqual(s0, tuple(pi.UNSCHEDULED_FOMC))
        self.assertEqual(frozenset(s0),
                         pi.build_event_calendar().unscheduled_fomc_dates)

    def test_raw_multi_is_derived_from_the_event_type_column(self):
        kinds = {}
        with open(pi.F10_EVENTS_CSV, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                kinds.setdefault(row["date_et"], set()).add(row["event_type"])
        self.assertEqual(
            frozenset(d for d, k in kinds.items() if len(k) > 1),
            pi.build_event_calendar().raw_multi_event_dates)

    def test_neither_field_is_empty_any_more(self):
        cal = pi.build_event_calendar()
        self.assertTrue(cal.unscheduled_fomc_dates)
        self.assertTrue(cal.raw_multi_event_dates)


class TestSessionProvenance(unittest.TestCase):

    def test_the_close_minute_is_uncapped(self):
        body = _code_of(pi.build_session_schedule)
        self.assertNotIn("RTH_CLOSE_MINUTE", body)
        self.assertNotIn("min(", body)
        sched = pi.build_session_schedule("2021-11-29", "2021-12-01")
        self.assertEqual({1020}, set(sched.close_minute.values()))

    def test_degraded_is_the_vendors_condition_file(self):
        sched = pi.build_session_schedule("2010-06-06", "2021-12-31")
        condition = json.loads(
            (pi.AUTHORIZED_JOB_DIR / pi.CONDITION_JSON_NAME
             ).read_text(encoding="utf-8"))
        self.assertEqual(
            frozenset(r["date"] for r in condition
                      if r["condition"] != "available"),
            sched.vendor_degraded_dates)

    def test_the_condition_predicate_is_the_one_s0_uses(self):
        """S0 takes every date whose condition is NOT "available" -- not
        "== degraded". A third condition value would change the set, and
        matching on the wrong side of that is how the two paths drift."""
        body = _code_of(pi.build_session_schedule)
        self.assertIn("!= 'available'", body)


class TestNoDateSpecificRepair(unittest.TestCase):
    """The verifier's eight dates are a SYMPTOM. If any of them is written
    into the source, the repair has become a patch."""

    #: Derived, not typed: any ISO date literal at all in the three builders
    #: is suspect, because none of them should need one.
    def test_the_builders_contain_no_date_literals(self):
        import inspect
        import re
        for fn in (pi.build_roll_intervals, pi.build_event_calendar,
                   pi.build_session_schedule):
            with self.subTest(builder=fn.__name__):
                body = "\n".join(l for l in inspect.getsource(fn).splitlines()
                                 if not l.strip().startswith("#"))
                # docstrings are prose; strip the first one
                body = re.sub(r'""".*?"""', "", body, flags=re.S)
                self.assertEqual([], re.findall(r"\d{4}-\d{2}-\d{2}", body))

    def test_the_module_names_no_stratum_value(self):
        source = Path(pi.__file__).read_text(encoding="utf-8")
        for label in ("T1", "T2", "T3", "vol_stratum", "event_stratum"):
            self.assertNotIn('"%s"' % label, source, label)

    def test_the_only_date_constant_is_the_ratified_unscheduled_list(self):
        """`UNSCHEDULED_FOMC` IS dates -- but it is IR-13's ratified
        enumeration copied from S0, not a repair, which is why it is pinned
        to the S0 constant above rather than to the verifier's findings."""
        import ast
        import re
        tree = ast.parse(Path(pi.__file__).read_text(encoding="utf-8"))
        docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                      if isinstance(n, (ast.Module, ast.FunctionDef,
                                        ast.ClassDef))
                      and n.body and isinstance(n.body[0], ast.Expr)
                      and isinstance(n.body[0].value, ast.Constant)
                      and isinstance(n.body[0].value.value, str)}
        found = set()
        for n in ast.walk(tree):
            if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and id(n) not in docstrings):
                found |= set(re.findall(r"\d{4}-\d{2}-\d{2}", n.value))
        self.assertEqual(set(pi.UNSCHEDULED_FOMC), found)


class TestNothingElseMoved(unittest.TestCase):

    def test_the_public_api_is_unchanged(self):
        self.assertEqual(
            ["AUTHORIZED_JOB_DIR", "AUTHORIZED_MANIFEST_SHA256",
             "F10_EVENTS_CSV", "verify_authorized_job_dir",
             "load_bars_by_date", "build_event_calendar",
             "build_session_schedule", "build_roll_intervals",
             "acquire_production_inputs"], list(pi.__all__))

    def test_the_stratification_algorithm_was_not_touched(self):
        """The repair is upstream of `build_universe`; the algorithm itself
        is out of scope and stays byte-identical."""
        import subprocess
        out = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--",
             "src/itsf/s0/", "src/itsf/data/symbology.py",
             "scripts/s0_real_run.py"],
            cwd=REPO, capture_output=True, text=True).stdout.split()
        self.assertEqual([], out,
                         "the repair modified files it was scoped out of: %r"
                         % out)


if __name__ == "__main__":
    unittest.main()
