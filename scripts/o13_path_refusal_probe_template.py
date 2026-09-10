# -*- coding: utf-8 -*-
"""O13.b / O13.c review probe, shipped as `probes/test_o13_path_refusals.py`.

WHY THIS EXISTS. `tests/test_mc_supplement_paths_battery.py` is the deepest
refusal battery in the subsystem, and it CANNOT BE COLLECTED inside a sealed
bundle: at import (its line 321) it reads
`C:\\Users\\Aaron\\quant-data\\itsf-registry\\ops\\TRIAL_REGISTRY.md`, and
`src/itsf/mc/registry_boundary.py` freezes that root as an exact string that
migration Route A step S6 declares "FROZEN AND NOT OVERRIDABLE FROM THE
ENVIRONMENT". There is no seam to redirect and the frozen implementation may
not be edited, so the read cannot be satisfied, faked or bypassed on any
machine that is not Aaron's. The file therefore travels as SOURCE ONLY.

WHAT WAS ACTUALLY LOST, measured rather than guessed. Coverage of
`src/itsf/mc` was taken over the full selection and again over the selection
with the battery removed. The delta is 27 statements in two modules. Six of
them (`supplement_runner._default_resolver`) come from two deselected tests
that resolve the REAL ledger -- an actual-artifact claim that belongs to
RUN-IDENTITY VERIFICATION at N15, not here. The remaining 21 are pure
refusal branches with no registry dependency whatsoever, and this probe
re-establishes every one of them by execution:

  supplement_runner.plan_supplement_paths   lines 205-206, 208-210, 214,
      217-218, 220, 222, 224, 241-242, 249-250
  supplement_runner._g_output_root_structure          lines 413-414
  supplement_registry._check_field_values             lines 904-905, 911-912

WHAT THIS IS NOT. It is not the battery and does not claim to be: the
battery asserts 72 properties and this asserts the twelve refusal codes the
bundle would otherwise lose. The battery's source is in `tree/tests/` and
reading it is part of the review. What this probe adds over reading is
EXECUTION -- that these branches are reachable and that each refuses under
the code the obligation names, on synthetic input, inside the boundary.
"""
TEMPLATE = '''# -*- coding: utf-8 -*-
"""O13.b / O13.c -- a mismatched or substituted path input is REFUSED.

Generated into the bundle by scripts/o13_path_refusal_probe_template.py to
replace execution of `tree/tests/test_mc_supplement_paths_battery.py`, which
cannot be collected here: it reads the real registry at import through a
frozen, deliberately non-overridable path. That file's SOURCE is in the
bundle and you are expected to read it. This runs the refusal branches its
absence would otherwise leave unexecuted.

Nothing below touches a real root, a real registry or a real commit. Every
constant is synthetic and every target lives under pytest's tmp_path, which
is inside the sealed bundle.
"""
import os
from pathlib import Path

import pytest

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_registry as sr
from itsf.mc import supplement_runner as r

SID = "MC-DS-S001"
C40 = "0123456789abcdef0123456789abcdef01234567"
UTC = "20260820T000000Z"
ROW_UTC = "2026-08-20T00:00:00+00:00"
SEP = os.sep
SYNTH_ROOT = "C:" + SEP + "synthetic" + SEP + "never-created"
NUL = "\\x00"


def roots(tmp_path):
    """Two real, distinct, absolute directories that are not governed."""
    runs = tmp_path / "runs-root"
    arch = tmp_path / "archive-root"
    runs.mkdir()
    arch.mkdir()
    return runs, arch


def plan_code(**kw) -> str:
    """Call the production planner and return the refusal code.

    Planning must CREATE NOTHING, so the call is bracketed by a listing of
    the sandbox and the two are compared -- a refusal that left a directory
    behind is a different defect wearing the right code."""
    watch = Path(kw.pop("watch"))

    def snap():
        return sorted(p.relative_to(watch).as_posix()
                      for p in watch.rglob("*"))

    before = snap()
    try:
        plan = r.plan_supplement_paths(**kw)
    except r.SupplementRunnerError as exc:
        assert snap() == before, "a refusal changed the filesystem"
        return exc.code
    raise AssertionError("expected a refusal; got a plan for %s"
                         % (plan.runs_target,))


# ---------------------------------------------------------------- grammar

def test_o13_a_supplement_id_not_matching_the_pattern_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    for bad in ("", "MC-DS-S1", "mc-ds-s001", "MC-DS-S001\\n", " MC-DS-S001"):
        assert plan_code(runs_root=runs, archive_root=arch,
                         supplement_id=bad, utc_stamp=UTC,
                         watch=tmp_path) == "plan_supplement_id_pattern", bad


def test_o13_b_malformed_utc_stamp_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    for bad in ("", "20260820", "2026-08-20T00:00:00Z", UTC + "\\n", UTC + " "):
        assert plan_code(runs_root=runs, archive_root=arch,
                         supplement_id=SID, utc_stamp=bad,
                         watch=tmp_path) == "plan_utc_stamp_malformed", bad


# ------------------------------------------------------------------ roots

def test_o13_c_a_missing_blank_or_none_root_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    for bad in (None, ""):
        assert plan_code(runs_root=bad, archive_root=arch,
                         supplement_id=SID, utc_stamp=UTC,
                         watch=tmp_path) == "plan_root_missing"
        assert plan_code(runs_root=runs, archive_root=bad,
                         supplement_id=SID, utc_stamp=UTC,
                         watch=tmp_path) == "plan_root_missing"


def test_o13_d_a_relative_root_is_refused(tmp_path):
    """A relative root names a directory that depends on the runner's
    working directory, so it can never be the one governed place the
    evidence may land."""
    runs, arch = roots(tmp_path)
    for bad in ("runs", "." + SEP + "runs", ".." + SEP + "runs", "C:"):
        assert plan_code(runs_root=bad, archive_root=arch,
                         supplement_id=SID, utc_stamp=UTC,
                         watch=tmp_path) == "plan_root_not_absolute", bad


def test_o13_e_an_absent_root_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    gone = tmp_path / "not-there"
    assert not gone.exists()
    assert plan_code(runs_root=gone, archive_root=arch,
                     supplement_id=SID, utc_stamp=UTC,
                     watch=tmp_path) == "plan_root_absent"


def test_o13_f_a_file_where_a_root_should_be_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    afile = tmp_path / "a-file"
    afile.write_bytes(b"not a directory")
    assert plan_code(runs_root=afile, archive_root=arch,
                     supplement_id=SID, utc_stamp=UTC,
                     watch=tmp_path) == "plan_root_not_a_directory"


# --------------------------------------------------------------- reparse

def _link(link: Path, target: Path) -> bool:
    """A real directory link if this process may make one. NEVER a
    subprocess: the bundle boundary denies that family outright, and
    `mklink` is how the repository battery does it. On refusal the caller
    proves the same property through the `_is_reparse` seam instead."""
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        return False
    return link.exists()


def test_o13_g_a_reparse_point_root_is_refused(tmp_path):
    """`_norm` uses `abspath`, not `resolve`, so a junction root is a
    substitution the planner must refuse rather than silently follow."""
    runs, arch = roots(tmp_path)
    link = tmp_path / "link-root"
    if _link(link, runs):
        assert r._is_reparse(link), "the link exists but the probe missed it"
        assert plan_code(runs_root=link, archive_root=arch,
                         supplement_id=SID, utc_stamp=UTC,
                         watch=tmp_path) == "plan_root_is_reparse_point"
    else:
        # Windows needs Developer Mode or elevation for a symlink. Prove the
        # branch through the seam AND prove the planner consults the seam
        # for BOTH roots, which together is what the junction case shows.
        seen = []

        def spy(p):
            seen.append(Path(p))
            return Path(p) == runs

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(r, "_is_reparse", spy)
            assert plan_code(runs_root=runs, archive_root=arch,
                             supplement_id=SID, utc_stamp=UTC,
                             watch=tmp_path) == "plan_root_is_reparse_point"
        assert runs in seen, seen


def test_o13_h_a_reparse_parent_is_refused(tmp_path):
    """`<root>/supplements` being a link is a redirect of the evidence and
    refuses under its own distinct code."""
    runs, arch = roots(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    parent = runs / r.SUPPLEMENTS_SUBDIR
    if _link(parent, elsewhere):
        assert plan_code(runs_root=runs, archive_root=arch,
                         supplement_id=SID, utc_stamp=UTC,
                         watch=tmp_path) == "plan_parent_is_reparse_point"
    else:
        parent.mkdir(parents=True)
        real_parent = parent.resolve()

        def spy(p):
            return Path(p).resolve() == real_parent

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(r, "_is_reparse", spy)
            assert plan_code(runs_root=runs, archive_root=arch,
                             supplement_id=SID, utc_stamp=UTC,
                             watch=tmp_path) == "plan_parent_is_reparse_point"


def test_o13_i_two_roots_that_resolve_to_one_path_collide(tmp_path):
    """Same root under a different spelling is still one directory, and
    one directory cannot be both the live and the archived copy."""
    runs, _arch = roots(tmp_path)
    other = Path(str(runs) + SEP + "." + SEP)
    assert plan_code(runs_root=runs, archive_root=other,
                     supplement_id=SID, utc_stamp=UTC,
                     watch=tmp_path) == "plan_targets_collide"


# ------------------------------------------------------- the binding gate

def test_o13_j_the_precheck_gate_refuses_a_root_that_was_not_supplied(
        tmp_path):
    """`_g_output_root_structure` is BINDING since the N06 repair: the root
    Aaron authorized must be the root the runner is about to use. Absent is
    the first way that can fail."""
    runs, arch = roots(tmp_path)

    def ctx(**kw):
        # `registry_text` is the EMPTY STRING on purpose: this gate reads
        # only the two roots, and an empty synthetic registry makes that
        # visible instead of merely asserted.
        return r.GateContext(supplement_id=SID, head_commit=C40,
                             registry_text="", **kw)

    with pytest.raises(Exception) as exc:
        r._g_output_root_structure(ctx(runs_root=None, archive_root=arch))
    assert "runs_root" in str(exc.value), str(exc.value)
    with pytest.raises(Exception) as exc:
        r._g_output_root_structure(ctx(runs_root=runs, archive_root=None))
    assert "archive_root" in str(exc.value), str(exc.value)


# ----------------------------------------------- the authorized-root field

_HEADER = ("| # | utc | event | commit | actor | note |",
           "|---|---|---|---|---|---|")


def _p2_row(output_root: str) -> str:
    """One synthetic P2 row. NOT an authorization: it never reaches a real
    registry and the commit is sixteen repetitions of `0123456789abcdef`
    truncated to forty characters, which is not any commit in this tree."""
    fields = {"supplement_id": SID, "authorized_commit": C40,
              "output_root": output_root}
    body = "; ".join("%s: %s" % (k, v) for k, v in fields.items())
    head = sr.execution_sentence_header(SID) + " "
    return ("| 1 | %s | **%s** | %s | %s | [%s] %s%s |"
            % (ROW_UTC, sc.EVENTS["P2"].token, C40, sc.ACTOR_AARON, SID,
               head, body))


def _row_refusal(output_root: str) -> sr.Refusal:
    text = "\\n".join(["# SYNTHETIC registry -- built here, NOT the governed ledger", "",
                       *_HEADER, _p2_row(output_root), ""])
    events, refusal = sr.parse_supplement_events(text)
    assert refusal is not None, "expected a refusal; the row was accepted"
    assert events == (), "a refused parse must yield NO events"
    return refusal


def test_o13_k_an_output_root_with_a_null_byte_is_refused():
    root = "C:" + SEP + "quant-data" + NUL + SEP + "itsf-runs"
    assert _row_refusal(root).code == "output_root_not_normalisable"


def test_o13_l_a_relative_authorized_output_root_is_refused():
    for bad in ("runs", "." + SEP + "runs", "/quant-data/itsf-runs", "/",
                "C:", "itsf-runs"):
        assert _row_refusal(bad).code == "output_root_not_absolute", bad


def test_o13_n_the_production_resolver_seam_is_wired_and_needs_no_real_text():
    """The N05 seam, exercised on a SYNTHETIC registry.

    `tests/test_mc_supplement_integration.py` closes this seam by feeding
    `_default_resolver` the real ledger's bytes. Reading the real ledger is
    an actual-artifact claim and is deselected here for that reason -- but
    the seam property itself is content-agnostic: the runner must discover
    a callable resolver on `supplement_registry` and hand it whatever text
    it was given, or refuse. That is what this shows, with no real bytes
    anywhere near it."""
    text = "\\n".join(["# SYNTHETIC registry -- built here, NOT the governed ledger", "",
                       *_HEADER, ""])
    chain = r._default_resolver(text, SID)
    assert chain is not None
    assert type(chain).__name__ == "ChainResolution"
    for attr in ("problem", "live_authorizations", "retired"):
        assert hasattr(chain, attr), "seam is missing %s" % attr
    assert sr.resolve_supplement_chain is not None


def test_o13_m_the_synthetic_control_is_accepted():
    """The negative tests above are only evidence if the same row with a
    good root passes. Otherwise they could all be failing upstream of the
    field check for a reason that has nothing to do with the root."""
    text = "\\n".join(["# SYNTHETIC registry -- built here, NOT the governed ledger", "",
                       *_HEADER, _p2_row(SYNTH_ROOT), ""])
    events, refusal = sr.parse_supplement_events(text)
    assert refusal is None, "the control row was refused: %s" % (refusal,)
    assert len(events) == 1
    assert events[0].output_root == SYNTH_ROOT
'''


def render() -> str:
    return TEMPLATE
