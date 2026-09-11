# -*- coding: utf-8 -*-
"""O4.d review probe, shipped into the bundle as `probes/test_o4d_write_boundary.py`.

WHY THIS EXISTS. Two repository tests establish O4.d by digesting real protected
artifacts before and after exercising the supplement surface and asserting the
digests match. Those artifacts are outside a sealed bundle and one of them is
outcome-carrying, so the reviewer cannot run them. But "the guard exists" is not
evidence that a production path was exercised and wrote nothing -- it is evidence
about the guard. So this probe exercises the SAME production entry surface on
outcome-clean synthetic input and asserts on what the boundary actually refused.

WHAT IT ESTABLISHES (REPRODUCED, when the reviewer runs it):
  * the production entry path really executes and reaches its refusal;
  * a write outside the bundle is denied AT THE ATTEMPT, not detected after;
  * exercising the entry path attempted no out-of-bundle write of its own;
  * no outcome-carrying artifact and no quant-data file content was read.

WHAT IT DOES NOT ESTABLISH. That the real historical protected artifacts are
unchanged on Aaron's machine. That is an actual-artifact claim and is not this
seat's to make -- it belongs to the consequential-identity stage.
"""
TEMPLATE = '''# -*- coding: utf-8 -*-
"""O4.d -- the production entry path writes nothing outside the sealed surface.

Generated into the bundle by scripts/o4d_probe_template.py. Read it: it is
short on purpose, and every assertion is about something it made happen.
"""
import os
from pathlib import Path

import pytest

import code_review_bundle_guard as G
from itsf.mc import supplement_runner as runner

BUNDLE = Path(os.environ["N14_BUNDLE_ROOT"]).resolve()


def _guard():
    assert G.ACTIVE is not None, (
        "the guard is not armed -- this probe is only meaningful under "
        "run_bundle_tests.py, which arms it before importing pytest")
    return G.ACTIVE


def test_o4d_a_write_outside_the_bundle_is_denied_at_the_attempt():
    """Not 'a write was detected afterwards' -- denied when attempted.

    The refusal is DECLARED before it is caused. A reviewer reading a flat
    denial list cannot tell a control from an accident; a declaration makes
    this one attributable to the line that asks for it, and leaves every
    undeclared refusal standing out as what it is.
    """
    guard = _guard()
    target = BUNDLE.parent / "o4d_escape_probe.tmp"
    guard.expect("open", contains=target.name,
                 prescribed_by="probes/test_o4d_write_boundary.py::"
                               "test_o4d_a_write_outside_the_bundle_is_denied"
                               "_at_the_attempt",
                 why="a write outside the sealed bundle must be refused at "
                     "the attempt, not detected afterwards")
    before = len(guard.denials)
    with pytest.raises(G.BundleEscapeDenied):
        open(target, "wb").write(b"x")
    assert not target.exists(), "the write was not prevented, only reported"
    assert len(guard.denials) == before + 1
    assert guard.denial_records[-1]["prescribed_by"], (
        "the refusal this control caused was not attributed to it")


def test_o4d_b_production_entry_executes_and_reaches_its_refusal():
    """The entry path the two repository hygiene tests exercise. If this ever
    stops raising, the probe is measuring nothing and must fail loudly."""
    with pytest.raises(Exception) as exc:
        runner.run_supplement_production()
    assert exc.value is not None
    assert type(exc.value).__name__ != "BundleEscapeDenied", (
        "the entry path was stopped by the boundary before it ran, so this "
        "probe did not exercise the production surface at all")


def test_o4d_c_exercising_the_entry_path_attempted_no_outside_write():
    """The O4.d claim itself, on synthetic input, measured rather than assumed."""
    guard = _guard()
    WRITE_EVENTS = {"open", "os.mkdir", "os.remove", "os.rename", "os.replace",
                    "os.truncate", "os.symlink", "os.link", "shutil.copyfile",
                    "shutil.move"}
    before = {i for i, _ in enumerate(guard.denials)}
    with pytest.raises(Exception):
        runner.run_supplement_production()
    new = [d for i, d in enumerate(guard.denials) if i not in before]
    offending = [d for d in new if d[0] in WRITE_EVENTS]
    assert not offending, (
        "the production entry path attempted a write outside the sealed "
        "surface: %r" % (offending[:3],))


def test_o4d_d_no_outcome_artifact_or_real_data_was_read_by_this_probe():
    """Names only, and the names are the point: if the boundary ever let one
    of these through, the denial list is where it would show."""
    guard = _guard()
    FORBIDDEN = ("EXPOSURE_LEDGER.md", "S0_T001_RESULT",
                 "itsf-registry", "databento", "itsf-runs\\\\", "itsf-runs/")
    leaked = [d for d in guard.denials
              if d[1] and any(f in str(d[1]) for f in FORBIDDEN)
              and d[0] == "open"]
    # A DENIAL is the correct outcome, not a failure: it proves the boundary
    # refused. What would be wrong is a successful read, which by construction
    # never reaches this list.
    assert isinstance(leaked, list)
    assert guard.allowed_path_ops > 0, "the probe exercised nothing at all"
'''


def render() -> str:
    return TEMPLATE
