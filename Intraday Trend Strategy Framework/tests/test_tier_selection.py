"""T-F15 (selection half): tier C is deselected from the run gate, and
tier A/B are not; an unmapped file is in the gate by default.

QROS-CF v2 §2.6 (DEC-0006 I4). The tier map is `tests/tiers.py`; the
markers are applied by `conftest.py`; the S0 run gate runs pytest with
`-m "not governance"`. A red README-index guard must not hold a run, and a
leakage test must never be deselected by accident -- both are measured
here with pytest's own collection, in a subprocess, on one small file each.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import tiers

REPO = Path(__file__).resolve().parents[1]


def _selected(*args) -> int:
    out = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q",
         "-p", "no:cacheprovider", *args],
        capture_output=True, text=True, cwd=str(REPO), encoding="utf-8")
    m = re.search(r"(\d+)\s+tests? collected|(\d+)/(\d+) tests? collected", out.stdout)
    if m:
        return int(m.group(1) or m.group(2))
    if "no tests collected" in out.stdout or "deselected" in out.stdout:
        return 0
    raise AssertionError(out.stdout[-800:] + out.stderr[-400:])


def test_the_tier_map_names_only_files_that_exist():
    listed = set(tiers.GOVERNANCE_FILES) | set(tiers.VALIDITY_FILES)
    assert len(listed) > 40, "premise: the map is populated"
    present = {p.name for p in (REPO / "tests").glob("test_*.py")}
    missing = sorted(listed - present)
    assert missing == [], missing
    assert not (set(tiers.GOVERNANCE_FILES) & set(tiers.VALIDITY_FILES))


def test_no_governance_file_reads_a_research_number_module():
    """A file marked tier C may not import the research core or the gates:
    if it did, it would be protecting a research number and belong in A/B."""
    forbidden = ("itsf.s0.stats", "itsf.s0.study", "itsf.s0.labels",
                 "itsf.s0.features", "itsf.mc.orchestrator", "itsf.mc.verdict",
                 "supplement_runner", "supplement_precheck", "production_inputs")
    offenders = []
    for name in tiers.GOVERNANCE_FILES:
        text = (REPO / "tests" / name).read_text(encoding="utf-8")
        for module in forbidden:
            if re.search(rf"^\s*(from|import)\s+.*{re.escape(module)}", text, re.M):
                offenders.append(f"{name} imports {module}")
    assert offenders == [], offenders


def test_tier_of_defaults_to_the_gate():
    assert tiers.tier_of("test_ops_index_is_complete.py") == "governance"
    assert tiers.tier_of("test_labels.py") == "validity"
    assert tiers.tier_of("test_some_new_file_nobody_mapped.py") == "safety"


def test_a_governance_file_is_deselected_from_the_gate_run():
    gov = "tests/test_ops_index_is_complete.py"
    assert _selected(gov) > 0, "premise: the file has tests"
    assert _selected(gov, "-m", "not governance") == 0


def test_a_validity_file_and_an_unmapped_file_stay_in_the_gate_run():
    for path in ("tests/test_labels.py", "tests/test_registry_witness.py"):
        assert _selected(path, "-m", "not governance") == _selected(path) > 0, path


def test_the_s0_gate_uses_exactly_this_deselection():
    text = (REPO / "scripts" / "s0_real_run.py").read_text(encoding="utf-8")
    assert 'PYTEST_GATE_DESELECT = "not governance"' in text
    assert '"-m", PYTEST_GATE_DESELECT' in text
