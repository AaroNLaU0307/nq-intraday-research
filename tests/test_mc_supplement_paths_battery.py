"""S2 — INDEPENDENT ADVERSARIAL NEGATIVE BATTERY over the N06 repair.

WHO WROTE THIS. Lane S2. This lane did NOT write
`src/itsf/mc/supplement_runner.py` or `src/itsf/mc/supplement_registry.py`
and did not write `tests/test_mc_supplement_registry.py`. Every fixture
below is built from scratch in this file so that a shared helper bug
cannot make the producer's tests and the adversary's tests wrong in the
same direction. The one thing borrowed from the N05 suite is the
TECHNIQUE — synthetic registry markdown assembled in memory, one ratified
row at a time.

WHAT IT ATTACKS. Four defects measured at the pre-repair commit
`617f7c3`:

  1. a P2 authorization naming a DIFFERENT root than the run would use
     was accepted, and so was a RELATIVE root — the gate only asked
     whether the field was non-empty;
  2. the registry accepted a numbered supplement row jumping from the
     existing highest sequence 13 straight to 99 ("increasing" was the
     whole rule);
  3. integer count fields accepted 0 and negatives (`-?[0-9]+` was the
     whole check);
  4. the subtree gate looked for a bare `supplements/<id>` path, which is
     NOT the ratified directory name `<id>_<UTC>`
     (`ND1_SUPPLEMENT_DIRECTORY_NAME=2_ID_UNDERSCORE_UTC`), so it could
     never have seen a real collision.

DISCIPLINE, absolute.
  * NOTHING is written to `ops/TRIAL_REGISTRY.md` or `EXPOSURE_LEDGER.md`.
    The registry is opened READ-ONLY, once, at import, purely to learn the
    highest sequence number the global namespace already occupies.
  * NO directory is created under `C:\\Users\\Aaron\\quant-data\\...`.
    Every path test runs inside `tmp_path`. `test_governed_supplement_
    subtrees_do_not_exist` asserts both governed `supplements` subtrees
    are still absent, and `conftest._suite_guard_real_ruled_roots`
    independently guards the ruled roots for every test in this file.
  * NO real data is read; no supplement and no MC is executed.
  * NO muted test anywhere — no conditional skip, no expected failure,
    not even one that never fires. Preconditions are ASSERTED instead, so
    an environment that cannot satisfy one goes RED rather than quiet.
    (`test_mc_supplement_integration.test_no_supplement_test_is_muted`
    globs `test_mc_supplement*.py`, so this file is inside that scan.)
  * Every planner call goes through `_plan`, which snapshots the watched
    roots before and after and fails if planning changed one byte of the
    listing — including on the refusing calls.

NOTHING HERE IS AN AUTHORIZATION. The synthetic rows carry §13.5-shaped
text only because the parser must be able to recognise one; every commit,
digest and root in them is a constant that is not any commit, digest or
root of this repository.

MEASURED FINDINGS are recorded as executable tests, never as prose.
The trailing-newline defect this lane found (Python's `$` also matches
immediately BEFORE a final newline, so a newline reached a planned
directory name) was REPAIRED by the owning lane and swept as a CLASS
across all seven anchored patterns in the two modules. Its two
characterization tests were therefore FLIPPED into refusal assertions
and moved up into sections 0, 4 and 5, and
`test_no_anchored_pattern_admits_a_trailing_newline` now checks the
whole class, so the defect cannot come back one pattern at a time.
Section 12 keeps the three residuals the owner disclosed deliberately,
still named `test_finding_*`, each carrying the loud comment that says
why it stands rather than being deleted.
"""
from __future__ import annotations

import dataclasses as _dc
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from itsf.contracts import RULED_ARCHIVE_ROOT, RULED_RUNS_ROOT
from itsf.mc import registry_boundary as _rb
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_registry as sr
from itsf.mc import supplement_runner as r

REPO = Path(__file__).resolve().parents[1]

# --- synthetic constants (none of these is a real commit/digest/root) ------

SID = "MC-DS-S001"
SID2 = "MC-DS-S002"
C40 = "0123456789abcdef0123456789abcdef01234567"
C7 = C40[:7]
D64 = "ab" * 32
INC = "INC-0123456789ab"
UTC = "20260820T000000Z"                 # the RUN stamp (directory name)
ROW_UTC = "2026-08-20T00:00:00+00:00"    # the registry row's utc cell
SEP = os.sep
SYNTH_ROOT = "C:" + SEP + "synthetic" + SEP + "never-created"
NUL = "\x00"

#: The old, pre-repair predicate for an integer field. Section 11 asserts
#: every rejected value still SATISFIES it, so the floor — not the shape
#: check — is demonstrably what refuses.
OLD_INT_PREDICATE = re.compile(r"-?[0-9]+")


# ===========================================================================
# helpers — filesystem snapshots (planning must create NOTHING)
# ===========================================================================

def _snapshot(root) -> tuple:
    """A deterministic listing of everything under `root`.

    Names, the dir/file split and every file size. Two snapshots compare
    equal only if the tree is byte-for-byte the same shape."""
    p = Path(root)
    if not p.exists():
        return ("<absent>", str(p))
    if not p.is_dir():
        return ("<file>", str(p), p.stat().st_size)
    out = []
    for dirpath, dirnames, filenames in os.walk(p):
        rel = os.path.relpath(dirpath, p)
        sizes = []
        for name in sorted(filenames):
            try:
                sizes.append((name, os.path.getsize(os.path.join(dirpath,
                                                                 name))))
            except OSError:                                   # pragma: no cover
                sizes.append((name, -1))
        out.append((rel, tuple(sorted(dirnames)), tuple(sizes)))
    return tuple(sorted(out))


def _forbid_governed(root) -> None:
    """RUNTIME lease guard: no call in this battery may plan into, or
    observe, a real governed output root. Cheaper and far harder to fool
    than scanning this file's own source text."""
    if root is None or str(root) == "":
        return
    try:
        norm = r._norm(root)
    except (OSError, ValueError):                             # pragma: no cover
        return
    for governed in (RULED_RUNS_ROOT, RULED_ARCHIVE_ROOT):
        ruled = r._norm(governed)
        assert norm != ruled and not norm.startswith(ruled + os.sep), (
            f"this battery may never point the planner at {root!r}: it is "
            f"the governed root {governed}")


def _plan(runs_root, archive_root, supplement_id, utc_stamp, watch):
    """Call the planner with before/after listings of every watched root."""
    watch = tuple(watch)
    assert watch, "every planner call in this battery must watch a root"
    _forbid_governed(runs_root)
    _forbid_governed(archive_root)
    before = tuple(_snapshot(w) for w in watch)
    try:
        outcome = ("ok", r.plan_supplement_paths(
            runs_root=runs_root, archive_root=archive_root,
            supplement_id=supplement_id, utc_stamp=utc_stamp))
    except r.SupplementRunnerError as exc:
        outcome = ("refused", exc)
    after = tuple(_snapshot(w) for w in watch)
    assert after == before, (
        "plan_supplement_paths CHANGED the filesystem; planning must "
        f"create nothing.\nbefore={before!r}\nafter ={after!r}")
    return outcome


def plan_ok(runs_root, archive_root, *, supplement_id=SID, utc_stamp=UTC,
            watch=()) -> r.PlannedPaths:
    kind, value = _plan(runs_root, archive_root, supplement_id, utc_stamp,
                        watch)
    assert kind == "ok", (
        f"expected a plan, got refusal {getattr(value, 'code', value)!r}")
    return value


def plan_code(runs_root, archive_root, *, supplement_id=SID, utc_stamp=UTC,
              watch=()) -> str:
    kind, value = _plan(runs_root, archive_root, supplement_id, utc_stamp,
                        watch)
    assert kind == "refused", (
        "expected a refusal; the planner returned a plan "
        f"({getattr(value, 'runs_target', value)})")
    return value.code


def _make_junction(link: Path, target: Path) -> bool:
    """Windows directory junction (no elevation needed, unlike a symlink).

    Returns True only if the link really came into existence. The caller
    NEVER skips on False — it proves the same refusal through the
    `_is_reparse` seam instead."""
    if os.name != "nt":                                       # pragma: no cover
        try:
            os.symlink(str(target), str(link), target_is_directory=True)
            return link.exists()
        except OSError:
            return False
    try:
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link),
                               str(target)], capture_output=True, text=True,
                              timeout=60)
    except (OSError, subprocess.SubprocessError):             # pragma: no cover
        return False
    return done.returncode == 0 and link.exists()


def _drop_junction(link: Path) -> None:
    """Remove the LINK, never its target (`os.rmdir` unlinks a junction)."""
    try:
        os.rmdir(str(link))
    except OSError:                                           # pragma: no cover
        pass


# ===========================================================================
# helpers — synthetic registry markdown, built here, never on disk
# ===========================================================================

_HEADER = ("| # | utc | event | commit | actor | note |",
           "|---|---|---|---|---|---|")

_ACTORS = {
    sc.ACTOR_MAIN_AGENT: "main agent",
    sc.ACTOR_AARON: sc.ACTOR_AARON,
    sc.ACTOR_AARON_OR_MAIN_AGENT: sc.ACTOR_AARON,
    sc.ACTOR_RUNNER: sc.ACTOR_RUNNER,
    sc.ACTOR_VERIFIER: "fresh Sol verifier",
}

#: A minimally COMPLETE note for each event this battery needs. Values are
#: the smallest legal ones, so a negative test that changes exactly one
#: field cannot be passing for an unrelated reason.
_NOTE_FIELDS = {
    "P1": {"ir_basis": "IR-29b Option B",
           "schema": "mc_day_strata_supplement.v1",
           "non_authorization_disclaimer": "this row is not an authorization"},
    "P2": {"supplement_id": SID, "authorized_commit": C40,
           "output_root": SYNTH_ROOT},
    "P2S": {"supersedes_event_sequence": "1",
            "superseded_authorized_commit": C40,
            "reason_code": "PRESTART_FIX", "incident_id": INC,
            "successor_authorized_commit": C40,
            "same_id_reauthorization": "YES"},
    "P4": {"sealed_sha256": D64, "rows_digest": D64,
           "day_universe_digest": D64, "source_input_sha256": D64,
           "method_version": "mc_day_strata_supplement.v1",
           "n_rows": "1", "archive": sr.ARCHIVE_OK},
    "A2": {"recovery_authorization_doc": "ops/SYNTHETIC_RECOVERY.md",
           "source_and_archive_exact_inventory_match": "YES",
           "per_file_sha256_match": "YES", "n_files": "1",
           "local_seal_sha256_unchanged": "YES", "incident_id": INC},
    "AX": {"archive_code": sc.ARCHIVE_CODES[0], "attempts_count": "1",
           "incident_id": INC, "aaron_ruling_doc": "ops/SYNTHETIC_RULING.md",
           "local_seal_sha256": D64, "local_seal_immutable": "YES"},
    "P5": {"rederivation_reproduced": "YES",
           "headline_replay_identity": "PASS", "n_cells": "1",
           "attestation_sha256": D64},
    "T1": {"successor_supplement_id": SID2, "predecessor_supplement_id": SID,
           "superseded_at_event": "1", "reason_code": "POST_START_FAILURE",
           "schema": "mc_day_strata_supplement.v1",
           "non_authorization_disclaimer": "this row is not an authorization"},
}


def row(short: str, *, sid: str = SID, seq=None, over=None) -> str:
    """One ratified six-cell registry row. NOT an authorization."""
    spec = sc.EVENTS[short]
    numbered = spec.row_class == sc.NUMBERED
    if seq is None:
        seq = "1" if numbered else sc.UNNUMBERED_SEQ_TOKEN
    values = dict(_NOTE_FIELDS[short])
    if over:
        values.update(over)
    body = "; ".join(f"{k}: {v}" for k, v in values.items())
    head = (sr.execution_sentence_header(sid) + " ") if short == "P2" else ""
    commit = C40 if numbered else C7
    return (f"| {seq} | {ROW_UTC} | **{spec.token}** | {commit} "
            f"| {_ACTORS[spec.actor]} | [{sid}] {head}{body} |")


def doc(*lines: str) -> str:
    return "\n".join(["# SYNTHETIC registry — NOT ops/TRIAL_REGISTRY.md", "",
                      *_HEADER, *lines, ""])


def row_refusal(line: str) -> sr.Refusal:
    """Row-layer validation only. Asserts a refusal and returns it."""
    events, refusal = sr.parse_supplement_events(doc(line))
    assert refusal is not None, "expected a row refusal; the row was accepted"
    assert events == (), "a refused parse must yield NO events"
    assert refusal.code in sr.REFUSAL_CODES, refusal.code
    return refusal


def row_accepted(line: str) -> sr.SupplementEvent:
    events, refusal = sr.parse_supplement_events(doc(line))
    assert refusal is None, f"unexpected row refusal: {refusal}"
    assert len(events) == 1
    return events[0]


# --- the real registry, READ-ONLY, for the global sequence namespace only ---

# REPOINTED 2026-08-31 by migration Route A. This used to build the path
# from REPO -- the framework repository -- and after S5 that location
# holds a TOMBSTONE. The tombstone parses cleanly and yields zero rows,
# so `real_highest_sequence` did not error; it reported an empty
# namespace. A test reading the wrong file and passing is worse than one
# that fails, and only the assert on "no numbered rows" caught it.
REAL_REGISTRY_PATH = _rb.REGISTRY_REPO_ROOT / _rb.REGISTRY_PATH
REAL_REGISTRY_TEXT = REAL_REGISTRY_PATH.read_text(encoding="utf-8")
assert _rb.REGISTRY_TOMBSTONE_MARKER not in REAL_REGISTRY_TEXT, (
    "the path this battery calls the real registry is a tombstone; "
    "it parses to zero rows and every sequence test below would be "
    "reasoning about an empty namespace")


def real_highest_sequence() -> int:
    rows, refusal = sr.parse_registry_rows(REAL_REGISTRY_TEXT)
    assert refusal is None, f"the real registry does not parse: {refusal}"
    values = [int(x.seq) for x in rows
              if re.fullmatch(r"[0-9]+", x.seq or "")]
    assert values, "the real registry has no numbered rows"
    return max(values)


def seq_outcome(value) -> str:
    """Append ONE synthetic P1 (a non-authorization proposal row) to the
    real registry text IN MEMORY and report the resolver's verdict."""
    text = REAL_REGISTRY_TEXT + "\n" + row("P1", seq=str(value)) + "\n"
    chains, refusal = sr.resolve_supplement_chains(text)
    if refusal is None:
        assert sorted(chains) == [SID]
        return "OK"
    assert chains == {}, "a refused resolution must yield NO chains"
    assert refusal.code in sr.REFUSAL_CODES, refusal.code
    return refusal.code


# ===========================================================================
# helpers — runner gate contexts (own stand-ins, not the N04 suite's)
# ===========================================================================

HEAD40 = "a" * 40


@_dc.dataclass(frozen=True)
class StubP2:
    actor: str = sc.ACTOR_AARON
    authorized_commit: str = HEAD40
    output_root: str = ""


@_dc.dataclass(frozen=True)
class StubChain:
    live_authorizations: tuple = ()
    problem: str = ""
    retired: bool = False


def ctx(*, declared="", runs_root=None, archive_root=None, utc_stamp=UTC,
        live=None) -> r.GateContext:
    if live is None:
        live = (StubP2(output_root=str(declared)),)
    return r.GateContext(supplement_id=SID, head_commit=HEAD40,
                         registry_text="", runs_root=runs_root,
                         archive_root=archive_root, utc_stamp=utc_stamp,
                         chain=StubChain(live_authorizations=live))


def gate_ok(name: str, context, watch=()) -> None:
    _forbid_governed(context.runs_root)
    _forbid_governed(context.archive_root)
    before = tuple(_snapshot(w) for w in watch)
    r.GATES[name](context)
    assert tuple(_snapshot(w) for w in watch) == before, (
        f"gate {name!r} changed the filesystem")


def gate_refusal(name: str, context, watch=()) -> r.SupplementRunnerError:
    _forbid_governed(context.runs_root)
    _forbid_governed(context.archive_root)
    before = tuple(_snapshot(w) for w in watch)
    with pytest.raises(r.SupplementRunnerError) as caught:
        r.GATES[name](context)
    assert tuple(_snapshot(w) for w in watch) == before, (
        f"refusing gate {name!r} changed the filesystem")
    assert caught.value.code == f"gate_refused:{name}", caught.value.code
    return caught.value


def roots(tmp_path: Path) -> tuple:
    runs = tmp_path / "runs"
    arch = tmp_path / "arch"
    runs.mkdir()
    arch.mkdir()
    return runs, arch


# ===========================================================================
# 0 — preconditions, ASSERTED (this battery never skips)
# ===========================================================================

def test_governed_supplement_subtrees_exist_by_grant_and_are_empty():
    """WAS `..._do_not_exist`, and the rename is the point.

    Absence was the ruling's CONDITION only "before the authorization is
    executed". Aaron authorized both paths verbatim on 2026-08-29 and they
    were created manually with pre/post exact-set evidence in
    `ops/DIRECTORY_CREATION_GRANTS.md` §4. Absence would now be the defect.

    The property this test actually protected -- that no code path creates
    or writes into them -- is asserted in the stronger form that survives:
    they exist, a USED grant records why, and they hold nothing.
    `not exists()` would have passed from here on while a test quietly
    wrote files into them; emptiness catches exactly that."""
    from _governed_subtrees import assert_governed_subtrees_are_empty
    assert_governed_subtrees_are_empty(Path(__file__).resolve().parents[1])


def test_platform_precondition_posix_root_is_not_absolute():
    """Python 3.13 `ntpath`: `/foo/bar` is NOT absolute. Every negative
    below that relies on a relative path depends on this."""
    assert os.name == "nt", f"this battery is pinned to Windows, got {os.name}"
    assert not os.path.isabs("/foo/bar")
    assert os.path.isabs("C:" + SEP + "x")
    # Finding 4 (fresh Sol N06): this battery depends on Python 3.13's
    # ntpath.isabs semantics — a rooted path with no drive stopped
    # counting as absolute — so `>= (3, 11)` understated the real
    # contract and three tests fail on 3.12. Pinned here and in
    # `.python-version`.
    assert sys.version_info >= (3, 13)


def test_ratified_names_are_what_the_code_uses():
    """`ND1_OUTPUT_ROOT_OPTION=A` + `ND1_SUPPLEMENT_DIRECTORY_NAME=
    2_ID_UNDERSCORE_UTC` + `REUSE_EXISTING_ROOTS_WITH_supplements_SUBTREE`."""
    assert r.SUPPLEMENTS_SUBDIR == "supplements"
    assert r.UTC_STAMP_RE.pattern == r"^\d{8}T\d{6}Z\Z"
    assert sc.SUPPLEMENT_ID_PATTERN.pattern == r"^MC-DS-S[0-9]{3}\Z"


#: Every anchored VALIDATING pattern in the two modules, each with one
#: input that MUST match. The `\Z` sweep is only meaningful
#: if it is checked as a CLASS rather than one pattern at a time.
ANCHORED_PATTERNS = (
    ("SUPPLEMENT_ID_PATTERN", sc.SUPPLEMENT_ID_PATTERN, SID),
    ("HEX40_RE", sc.HEX40_RE, C40),
    ("HEX7_RE", sc.HEX7_RE, C7),
    ("HEX64_RE", sc.HEX64_RE, D64),
    ("INCIDENT_RE", sc.INCIDENT_RE, INC),
    ("REASON_CODE_RE", sc.REASON_CODE_RE, "PRESTART_FIX"),
    ("UTC_STAMP_RE", r.UTC_STAMP_RE, UTC),
)


def test_no_anchored_pattern_admits_a_trailing_newline():
    r"""THE SWEPT CLASS. Python's `$` matches at the end of the string
    OR immediately before a final newline, so a `$`-anchored grammar
    accepted "<valid>\n" and the newline then travelled into a
    planned directory name. This lane reached and reported two of these
    (`UTC_STAMP_RE`, `SUPPLEMENT_ID_PATTERN`); all seven carried the
    identical defect and were swept together to `\Z`.

    Asserted as a CLASS, against the COMPILED objects rather than the
    source text, so one pattern regressing to `$` fails here even while
    the other six stay correct."""
    assert len(ANCHORED_PATTERNS) == 7
    for name, pattern, good in ANCHORED_PATTERNS:
        assert pattern.pattern.endswith(r"\Z"), (
            f"{name} is not \\Z-anchored: {pattern.pattern!r}")
        assert "$" not in pattern.pattern, (name, pattern.pattern)
        assert pattern.match(good), (name, good)
        for tail in ("\n", "\r\n", "\n\n", "\nX", "\r", "\u2028"):
            assert not pattern.match(good + tail), (
                f"{name} still admits {good + tail!r}")
            assert not pattern.match(tail + good), (
                f"{name} still admits {tail + good!r}")


def test_the_anchored_pattern_table_covers_both_modules():
    """A new anchored public pattern added upstream must JOIN the table
    above rather than escape the class check."""
    listed = {pattern.pattern for _, pattern, _ in ANCHORED_PATTERNS}
    found = []
    for module in (sc, r):
        for attr in dir(module):
            if attr.startswith("_"):
                continue
            value = getattr(module, attr)
            if not isinstance(value, re.Pattern):
                continue
            if not value.pattern.startswith("^"):
                continue
            found.append(f"{module.__name__}.{attr}")
            assert value.pattern in listed, (
                f"{module.__name__}.{attr} is an anchored public "
                "pattern that this battery does not sweep")
    assert len(found) == len(ANCHORED_PATTERNS), found


def test_real_registry_authorizes_nothing_and_is_only_read():
    chains, refusal = sr.resolve_supplement_chains(REAL_REGISTRY_TEXT)
    assert refusal is None, f"the real registry does not resolve: {refusal}"
    assert chains == {}, (
        "the real registry already carries a supplement chain — this "
        "battery assumes it carries none")
    assert real_highest_sequence() >= 13, (
        "the registry is append-only, so its highest sequence can only "
        "grow from the measured 13")


# ===========================================================================
# 1 — POSITIVE: a coherent plan, stated field by field
# ===========================================================================

def test_coherent_plan_matches_the_ratified_directory_name(tmp_path):
    runs, arch = roots(tmp_path)
    planned = plan_ok(runs, arch, watch=(tmp_path,))

    assert planned.dir_name == f"{SID}_{UTC}"
    assert planned.supplement_id == SID and planned.utc_stamp == UTC
    assert planned.runs_target.name == planned.archive_target.name
    assert planned.runs_target.name == planned.dir_name

    assert r._strictly_under(planned.runs_target, runs)
    assert r._strictly_under(planned.archive_target, arch)
    assert not r._strictly_under(planned.runs_target, arch)
    assert not r._strictly_under(planned.archive_target, runs)

    # `archive_sealed_run` appends the directory name itself, so it must
    # be handed the PARENT — `<archive_root>/supplements` — not the target.
    assert planned.archive_parent == arch / r.SUPPLEMENTS_SUBDIR
    assert planned.archive_parent / planned.dir_name == planned.archive_target
    assert planned.runs_target == runs / r.SUPPLEMENTS_SUBDIR / planned.dir_name

    # and NOTHING of it exists
    for path in (planned.runs_target, planned.archive_target,
                 planned.archive_parent, runs / r.SUPPLEMENTS_SUBDIR):
        assert not path.exists(), f"the planner created {path}"


def test_plan_is_pure_and_repeatable(tmp_path):
    runs, arch = roots(tmp_path)
    first = plan_ok(runs, arch, watch=(tmp_path,))
    second = plan_ok(runs, arch, watch=(tmp_path,))
    assert first == second, "the planner is not a pure function of its inputs"


def test_positive_correct_next_sequence_resolves():
    expected = real_highest_sequence() + 1
    assert seq_outcome(expected) == "OK", (
        f"the next global sequence value {expected} must be accepted")


# ===========================================================================
# 2 — planning creates NOTHING, including on every refusal
# ===========================================================================

def test_planning_creates_nothing_on_success_and_on_every_refusal(tmp_path):
    """`_plan` asserts the before/after listing on EVERY call; this test
    drives one success and one of each refusal family through it."""
    runs, arch = roots(tmp_path)
    afile = tmp_path / "a-file"
    afile.write_text("x", encoding="utf-8")

    plan_ok(runs, arch, watch=(tmp_path,))
    for kwargs in (
            dict(runs_root=runs, archive_root=arch, supplement_id="nope"),
            dict(runs_root=runs, archive_root=arch, utc_stamp="nope"),
            dict(runs_root="", archive_root=arch),
            dict(runs_root="relative", archive_root=arch),
            dict(runs_root=tmp_path / "absent", archive_root=arch),
            dict(runs_root=afile, archive_root=arch),
            dict(runs_root=runs, archive_root=runs),
    ):
        kwargs.setdefault("watch", (tmp_path,))
        plan_code(**kwargs)

    assert not (runs / r.SUPPLEMENTS_SUBDIR).exists()
    assert not (arch / r.SUPPLEMENTS_SUBDIR).exists()


# ===========================================================================
# 3 — every root defect refuses under its OWN code
# ===========================================================================

def test_relative_root_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    assert plan_code(runs_root="runs", archive_root=arch,
                     watch=(tmp_path,)) == "plan_root_not_absolute"
    assert plan_code(runs_root=runs, archive_root=Path("arch"),
                     watch=(tmp_path,)) == "plan_root_not_absolute"


def test_posix_style_rooted_path_is_not_absolute_here(tmp_path):
    runs, arch = roots(tmp_path)
    assert plan_code(runs_root="/quant-data/itsf-runs", archive_root=arch,
                     watch=(tmp_path,)) == "plan_root_not_absolute"


def test_bare_drive_letter_is_not_absolute(tmp_path):
    runs, arch = roots(tmp_path)
    assert plan_code(runs_root="C:", archive_root=arch,
                     watch=(tmp_path,)) == "plan_root_not_absolute"


def test_missing_root_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    assert plan_code(runs_root=tmp_path / "not-there", archive_root=arch,
                     watch=(tmp_path,)) == "plan_root_absent"
    assert plan_code(runs_root=runs, archive_root=tmp_path / "not-there",
                     watch=(tmp_path,)) == "plan_root_absent"


def test_blank_and_none_roots_are_refused(tmp_path):
    runs, arch = roots(tmp_path)
    for bad in ("", None):
        assert plan_code(runs_root=bad, archive_root=arch,
                         watch=(tmp_path,)) == "plan_root_missing"
        assert plan_code(runs_root=runs, archive_root=bad,
                         watch=(tmp_path,)) == "plan_root_missing"


def test_file_where_a_root_should_be_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    afile = tmp_path / "not-a-directory"
    afile.write_bytes(b"x")
    assert plan_code(runs_root=afile, archive_root=arch,
                     watch=(tmp_path,)) == "plan_root_not_a_directory"
    assert plan_code(runs_root=runs, archive_root=afile,
                     watch=(tmp_path,)) == "plan_root_not_a_directory"


def test_reparse_point_root_is_refused(tmp_path):
    """A junction root is the substitution `_norm` deliberately refuses to
    hide (it uses `abspath`, not `resolve`). If the OS will not let this
    process create a junction, the same refusal is proved through the
    `_is_reparse` seam — never skipped."""
    runs, arch = roots(tmp_path)
    link = tmp_path / "junction-root"
    made = _make_junction(link, runs)
    try:
        if made:
            assert r._is_reparse(link), (
                "the junction was created but the reparse probe missed it")
            assert plan_code(runs_root=link, archive_root=arch,
                             watch=(runs, arch)) == "plan_root_is_reparse_point"
            assert plan_code(runs_root=runs, archive_root=link,
                             watch=(runs, arch)) == "plan_root_is_reparse_point"
        else:
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(r, "_is_reparse", lambda p: Path(p) == runs)
                assert plan_code(
                    runs_root=runs, archive_root=arch,
                    watch=(tmp_path,)) == "plan_root_is_reparse_point"
    finally:
        if made:
            _drop_junction(link)
            assert not link.exists()


def test_reparse_seam_is_wired_into_the_planner(tmp_path, monkeypatch):
    """Deterministic companion to the junction test: whatever the OS
    allows, the planner must consult `_is_reparse` for both roots."""
    runs, arch = roots(tmp_path)
    seen = []

    def spy(path):
        seen.append(Path(path))
        return False

    monkeypatch.setattr(r, "_is_reparse", spy)
    plan_ok(runs, arch, watch=(tmp_path,))
    assert runs in seen and arch in seen, seen


def test_reparse_parent_is_refused(tmp_path):
    """`<runs_root>/supplements` itself being a junction is a redirect of
    the evidence and must refuse under its own code."""
    runs, arch = roots(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    link = runs / r.SUPPLEMENTS_SUBDIR
    made = _make_junction(link, elsewhere)
    try:
        if made:
            assert plan_code(runs_root=runs, archive_root=arch,
                             watch=(elsewhere, arch)) == \
                "plan_parent_is_reparse_point"
        else:
            link.mkdir(parents=True)
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(r, "_is_reparse", lambda p: Path(p) == link)
                assert plan_code(runs_root=runs, archive_root=arch,
                                 watch=(arch,)) == \
                    "plan_parent_is_reparse_point"
    finally:
        if made:
            _drop_junction(link)


# ===========================================================================
# 4 — malformed UTC stamps
# ===========================================================================

@pytest.mark.parametrize("stamp", [
    "",                       # empty
    "20260820T00000Z",        # one digit short
    "20260820T0000000Z",      # one digit long
    "2026082T000000Z",        # short date
    "20260820T000000",        # no trailing Z
    "20260820t000000Z",       # lowercase separator
    "20260820T000000z",       # lowercase Z
    "20260820-000000Z",       # wrong separator
    "2026-08-20T00:00:00Z",   # ISO-8601 instead of the compact stamp
    "2026-08-20T00:00:00+00:00",   # the registry ROW stamp, not the run one
    "abcdefghTijklmnZ",       # non-numeric
    "2026082 T000000Z",       # embedded space
    " 20260820T000000Z",      # leading space
    "20260820T000000Z ",      # trailing space
    "20260820T000000Z\t",     # trailing tab
    "20260820T000000Z/../x",  # traversal appended
])
def test_malformed_utc_stamp_is_refused(tmp_path, stamp):
    runs, arch = roots(tmp_path)
    assert plan_code(runs, arch, utc_stamp=stamp,
                     watch=(tmp_path,)) == "plan_utc_stamp_malformed"


def test_trailing_newline_utc_stamp_is_refused(tmp_path):
    r"""FLIPPED. This lane reported that `$` let "20260820T000000Z\n"
    through and that the newline then reached `dir_name`. After the
    `\Z` sweep it is a refusal under its own code, and nothing is
    planned."""
    runs, arch = roots(tmp_path)
    for stamp in (UTC + "\n", UTC + "\r\n", UTC + "\n\n", UTC + "\nX",
                  "\n" + UTC, UTC + "\r", UTC + "\u2028"):
        assert plan_code(runs, arch, utc_stamp=stamp,
                         watch=(tmp_path,)) == "plan_utc_stamp_malformed"
    assert not (runs / r.SUPPLEMENTS_SUBDIR).exists()
    assert not (arch / r.SUPPLEMENTS_SUBDIR).exists()


def test_none_utc_stamp_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    assert plan_code(runs, arch, utc_stamp=None,
                     watch=(tmp_path,)) == "plan_utc_stamp_malformed"


# ===========================================================================
# 5 — malformed supplement ids
# ===========================================================================

@pytest.mark.parametrize("bad_id", [
    "",
    "MC-DS-S1",               # too few digits
    "MC-DS-S0001",            # too many digits
    "mc-ds-s001",             # lowercase
    "MC-DS-S00A",             # non-digit
    "MC_DS_S001",             # underscores
    " MC-DS-S001",
    "MC-DS-S001 ",
    "MC-DS-S001_20260820T000000Z",     # the directory name, not the id
    ".." + SEP + "MC-DS-S001",         # traversal
    "MC-DS-S001" + SEP + "..",
    "MC-DS-S001/../..",
    "C:" + SEP + "MC-DS-S001",         # an absolute path as an id
    "S0-T001",                         # an S0 trial id
])
def test_malformed_supplement_id_is_refused(tmp_path, bad_id):
    runs, arch = roots(tmp_path)
    assert plan_code(runs, arch, supplement_id=bad_id,
                     watch=(tmp_path,)) == "plan_supplement_id_pattern"


def test_trailing_newline_supplement_id_is_refused(tmp_path):
    r"""FLIPPED, id side: "MC-DS-S001\n" no longer satisfies the
    CLOSED id namespace, so it can never become the `<id>` half of a
    `<id>_<UTC>` directory name."""
    runs, arch = roots(tmp_path)
    for bad_id in (SID + "\n", SID + "\r\n", SID + "\n\n", SID + "\nX",
                   "\n" + SID, SID + "\r", SID + "\u2028"):
        assert plan_code(runs, arch, supplement_id=bad_id,
                         watch=(tmp_path,)) == "plan_supplement_id_pattern"
    assert not (runs / r.SUPPLEMENTS_SUBDIR).exists()


def test_no_newline_can_reach_a_planned_directory_name(tmp_path):
    """FLIPPED, end to end. The exact pair that used to yield a
    `dir_name` carrying a newline now yields refusals and NO plan, while
    the clean pair still plans a newline-free name."""
    runs, arch = roots(tmp_path)
    assert plan_code(runs, arch, supplement_id=SID + "\n",
                     utc_stamp=UTC + "\n",
                     watch=(tmp_path,)) == "plan_supplement_id_pattern"
    assert plan_code(runs, arch, utc_stamp=UTC + "\n",
                     watch=(tmp_path,)) == "plan_utc_stamp_malformed"
    planned = plan_ok(runs, arch, watch=(tmp_path,))
    assert planned.dir_name == f"{SID}_{UTC}"
    for part in (planned.dir_name, planned.runs_target.name,
                 planned.archive_target.name):
        assert not any(ch in part for ch in "\r\n\u2028\u2029"), part


def test_none_supplement_id_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    assert plan_code(runs, arch, supplement_id=None,
                     watch=(tmp_path,)) == "plan_supplement_id_pattern"


# ===========================================================================
# 6 — an existing target refuses; the OLD bare path does NOT
# ===========================================================================

def test_existing_exact_runs_target_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    (runs / r.SUPPLEMENTS_SUBDIR / f"{SID}_{UTC}").mkdir(parents=True)
    assert plan_code(runs, arch, watch=(tmp_path,)) == "plan_target_exists"


def test_existing_exact_archive_target_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    (arch / r.SUPPLEMENTS_SUBDIR / f"{SID}_{UTC}").mkdir(parents=True)
    assert plan_code(runs, arch, watch=(tmp_path,)) == "plan_target_exists"


def test_existing_target_as_a_file_is_also_refused(tmp_path):
    """A FILE at the target path is a collision too — `exists()`, not
    `is_dir()`, is the right predicate and this pins it."""
    runs, arch = roots(tmp_path)
    (runs / r.SUPPLEMENTS_SUBDIR).mkdir()
    (runs / r.SUPPLEMENTS_SUBDIR / f"{SID}_{UTC}").write_bytes(b"x")
    assert plan_code(runs, arch, watch=(tmp_path,)) == "plan_target_exists"


def test_the_old_bare_supplements_id_path_does_not_block(tmp_path):
    """THE PINNED DEFECT. At 617f7c3 the subtree gate looked for
    `supplements/<id>`, which the ratified naming never produces. A
    directory sitting exactly there is NOT the planned target and must not
    be mistaken for one — that is why the old check could never fire."""
    runs, arch = roots(tmp_path)
    stale_runs = runs / r.SUPPLEMENTS_SUBDIR / SID
    stale_arch = arch / r.SUPPLEMENTS_SUBDIR / SID
    stale_runs.mkdir(parents=True)
    stale_arch.mkdir(parents=True)

    planned = plan_ok(runs, arch, watch=(tmp_path,))
    assert planned.runs_target != stale_runs
    assert planned.archive_target != stale_arch
    assert planned.runs_target.name == f"{SID}_{UTC}"
    assert stale_runs.exists() and stale_arch.exists(), (
        "planning must not have touched the stale directories either")


def test_a_neighbouring_stamp_does_not_block(tmp_path):
    """A different run of the SAME id is a sibling, not a collision."""
    runs, arch = roots(tmp_path)
    (runs / r.SUPPLEMENTS_SUBDIR / f"{SID}_20260819T235959Z").mkdir(
        parents=True)
    planned = plan_ok(runs, arch, watch=(tmp_path,))
    assert planned.dir_name == f"{SID}_{UTC}"


# ===========================================================================
# 7 — containment and non-collision
# ===========================================================================

def test_runs_and_archive_targets_never_collide(tmp_path):
    runs, _ = roots(tmp_path)
    assert plan_code(runs_root=runs, archive_root=runs,
                     watch=(tmp_path,)) == "plan_targets_collide"


def test_same_root_by_a_different_spelling_still_collides(tmp_path):
    """`_norm` is case- and separator-normalising, so a re-spelt duplicate
    root cannot smuggle two 'different' targets onto one path."""
    runs, _ = roots(tmp_path)
    alias = Path(str(runs).upper())
    assert plan_code(runs_root=runs, archive_root=alias,
                     watch=(tmp_path,)) == "plan_targets_collide"
    alias2 = runs / "sub" / ".."
    (runs / "sub").mkdir()
    assert plan_code(runs_root=runs, archive_root=alias2,
                     watch=(tmp_path,)) == "plan_targets_collide"


def test_both_targets_are_strictly_under_their_own_root(tmp_path):
    runs, arch = roots(tmp_path)
    planned = plan_ok(runs, arch, watch=(tmp_path,))
    for target, root in ((planned.runs_target, runs),
                         (planned.archive_target, arch)):
        assert r._strictly_under(target, root)
        assert Path(r._norm(root)) in Path(r._norm(target)).parents
        assert r._norm(target) != r._norm(root)
    assert r._norm(planned.runs_target) != r._norm(planned.archive_target)


def test_nested_roots_still_keep_each_target_under_its_own_root(tmp_path):
    """archive_root INSIDE runs_root is legal but must not merge them."""
    runs, _ = roots(tmp_path)
    arch = runs / "nested-archive"
    arch.mkdir()
    planned = plan_ok(runs, arch, watch=(tmp_path,))
    assert r._strictly_under(planned.archive_target, arch)
    assert planned.runs_target != planned.archive_target
    assert planned.archive_parent == arch / r.SUPPLEMENTS_SUBDIR


def test_escape_attempts_are_stopped_by_the_id_and_stamp_grammar(tmp_path):
    """Containment is enforced UPSTREAM: no traversal survives the id or
    stamp pattern, so `plan_target_escapes_root` is defence in depth."""
    runs, arch = roots(tmp_path)
    for bad_id in ("..", "..." + SEP + "..", SID + SEP + ".." + SEP + ".."):
        assert plan_code(runs, arch, supplement_id=bad_id,
                         watch=(tmp_path,)) == "plan_supplement_id_pattern"
    for bad_stamp in (".." + SEP + "..", UTC + SEP + ".."):
        assert plan_code(runs, arch, utc_stamp=bad_stamp,
                         watch=(tmp_path,)) == "plan_utc_stamp_malformed"


# ===========================================================================
# 8 — output-root binding (the P2 field must be the root actually used)
# ===========================================================================

def test_output_root_binding_accepts_only_the_coherent_case(tmp_path):
    runs, arch = roots(tmp_path)
    gate_ok("output_root_structure",
            ctx(declared=str(runs), runs_root=runs, archive_root=arch),
            watch=(tmp_path,))


def test_authorized_root_naming_a_different_root_is_refused(tmp_path):
    """THE PINNED DEFECT. At 617f7c3 the gate only asked whether the field
    was non-empty, so an authorization naming the ARCHIVE root — or any
    other directory — was accepted while the run used the governed runs
    root regardless."""
    runs, arch = roots(tmp_path)
    other = tmp_path / "somewhere-else"
    other.mkdir()
    for declared in (str(arch), str(other), str(tmp_path),
                     str(runs.parent), str(runs / "child"),
                     RULED_RUNS_ROOT):
        exc = gate_refusal("output_root_structure",
                           ctx(declared=declared, runs_root=runs,
                               archive_root=arch), watch=(tmp_path,))
        assert "is not the runs_root" in str(exc), str(exc)


def test_relative_authorized_root_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    for declared in ("runs", "." + SEP + "runs", "/quant-data/itsf-runs",
                     "C:", ".."):
        exc = gate_refusal("output_root_structure",
                           ctx(declared=declared, runs_root=runs,
                               archive_root=arch), watch=(tmp_path,))
        assert "is not absolute" in str(exc), str(exc)


def test_blank_authorized_root_is_refused(tmp_path):
    runs, arch = roots(tmp_path)
    for declared in ("", "   ", "\t"):
        exc = gate_refusal("output_root_structure",
                           ctx(declared=declared, runs_root=runs,
                               archive_root=arch), watch=(tmp_path,))
        assert "names no output root" in str(exc), str(exc)


def test_no_live_authorization_fails_closed_at_the_binding_gate(tmp_path):
    """`_live_p2` returns None for zero and for two live rows; the gate
    must read that as 'no output root', never as 'nothing to check'."""
    runs, arch = roots(tmp_path)
    for live in ((), (StubP2(output_root=str(runs)),
                      StubP2(output_root=str(runs)))):
        exc = gate_refusal("output_root_structure",
                           ctx(runs_root=runs, archive_root=arch, live=live),
                           watch=(tmp_path,))
        assert "names no output root" in str(exc), str(exc)


def test_binding_gate_still_checks_the_runs_and_archive_roots(tmp_path):
    runs, arch = roots(tmp_path)
    missing = tmp_path / "absent"
    afile = tmp_path / "afile"
    afile.write_bytes(b"x")
    cases = (
        (None, arch, "was not supplied"),
        (runs, None, "was not supplied"),
        (Path("relative"), arch, "is not an absolute path"),
        (missing, arch, "does not exist"),
        (afile, arch, "is not a directory"),
        (runs, afile, "is not a directory"),
    )
    for runs_root, archive_root, expected in cases:
        exc = gate_refusal("output_root_structure",
                           ctx(declared=str(runs), runs_root=runs_root,
                               archive_root=archive_root), watch=(tmp_path,))
        assert expected in str(exc), (expected, str(exc))


def test_binding_gate_writes_nothing_not_even_a_probe(tmp_path):
    """`ND1_WRITE_PROBE_AUTHORIZED=NO` — unlike
    `runinfra.validate_output_roots_operational`, this gate must not drop
    a probe file into either root."""
    runs, arch = roots(tmp_path)
    before = _snapshot(tmp_path)
    gate_ok("output_root_structure",
            ctx(declared=str(runs), runs_root=runs, archive_root=arch),
            watch=(tmp_path,))
    assert _snapshot(tmp_path) == before
    assert list(runs.iterdir()) == [] and list(arch.iterdir()) == []


# --- the subtree gate now plans the EXACT target ---------------------------

def test_subtree_gate_accepts_a_clean_pair(tmp_path):
    runs, arch = roots(tmp_path)
    gate_ok("supplement_subtree_absent",
            ctx(declared=str(runs), runs_root=runs, archive_root=arch),
            watch=(tmp_path,))


def test_subtree_gate_refuses_without_a_utc_stamp(tmp_path):
    runs, arch = roots(tmp_path)
    exc = gate_refusal("supplement_subtree_absent",
                       ctx(declared=str(runs), runs_root=runs,
                           archive_root=arch, utc_stamp=""),
                       watch=(tmp_path,))
    assert "no UTC stamp supplied" in str(exc), str(exc)


def test_subtree_gate_sees_the_exact_ratified_target(tmp_path):
    runs, arch = roots(tmp_path)
    (runs / r.SUPPLEMENTS_SUBDIR / f"{SID}_{UTC}").mkdir(parents=True)
    exc = gate_refusal("supplement_subtree_absent",
                       ctx(declared=str(runs), runs_root=runs,
                           archive_root=arch), watch=(tmp_path,))
    assert "plan_target_exists" in str(exc), str(exc)


def test_subtree_gate_is_not_fooled_by_the_old_bare_path(tmp_path):
    """The 617f7c3 shape must NOT block: `supplements/<id>` is not a
    target any ratified run would ever write."""
    runs, arch = roots(tmp_path)
    (runs / r.SUPPLEMENTS_SUBDIR / SID).mkdir(parents=True)
    (arch / r.SUPPLEMENTS_SUBDIR / SID).mkdir(parents=True)
    gate_ok("supplement_subtree_absent",
            ctx(declared=str(runs), runs_root=runs, archive_root=arch),
            watch=(tmp_path,))


def test_subtree_gate_forwards_every_planner_refusal(tmp_path):
    runs, arch = roots(tmp_path)
    afile = tmp_path / "afile"
    afile.write_bytes(b"x")
    for runs_root, archive_root, fragment in (
            (Path("relative"), arch, "plan_root_not_absolute"),
            (tmp_path / "absent", arch, "plan_root_absent"),
            (afile, arch, "plan_root_not_a_directory"),
            (runs, runs, "plan_targets_collide"),
    ):
        exc = gate_refusal("supplement_subtree_absent",
                           ctx(declared=str(runs), runs_root=runs_root,
                               archive_root=archive_root), watch=(tmp_path,))
        assert fragment in str(exc), (fragment, str(exc))


# ===========================================================================
# 9 — the GLOBAL sequence is the NEXT value, not merely a larger one
# ===========================================================================

def test_next_value_is_accepted_and_nothing_else_is():
    highest = real_highest_sequence()
    expected = highest + 1
    assert seq_outcome(expected) == "OK"

    # the exact 617f7c3 counterexample: 13 -> 99 was "increasing"
    assert seq_outcome(expected + 85) == "supplement_seq_not_next_value"
    assert seq_outcome(expected + 1) == "supplement_seq_not_next_value"
    assert seq_outcome(expected + 2) == "supplement_seq_not_next_value"
    assert seq_outcome(10 ** 6) == "supplement_seq_not_next_value"


def test_reusing_or_undercutting_an_existing_sequence_is_refused():
    highest = real_highest_sequence()
    # every value at or below the highest is already occupied by a real
    # row, so the duplicate code — not the next-value code — is correct.
    for value in (highest, highest - 1, 1, 5):
        assert seq_outcome(value) == "supplement_seq_duplicate", value


def test_zero_and_negative_sequence_cells_are_refused():
    assert seq_outcome(0) == "supplement_seq_not_next_value"
    # a '-1' cell is not an integer sequence at all under `[0-9]+`
    text = REAL_REGISTRY_TEXT + "\n" + row("P1", seq="-1") + "\n"
    chains, refusal = sr.resolve_supplement_chains(text)
    assert refusal is not None and chains == {}
    assert refusal.code == "supplement_seq_not_integer", refusal.code


def test_two_appended_rows_must_be_consecutive():
    highest = real_highest_sequence()
    good = (REAL_REGISTRY_TEXT + "\n"
            + row("P1", seq=str(highest + 1)) + "\n"
            + row("P1", sid=SID2, seq=str(highest + 2)) + "\n")
    chains, refusal = sr.resolve_supplement_chains(good)
    assert refusal is None, f"unexpected refusal: {refusal}"
    assert sorted(chains) == [SID, SID2]

    gapped = (REAL_REGISTRY_TEXT + "\n"
              + row("P1", seq=str(highest + 1)) + "\n"
              + row("P1", sid=SID2, seq=str(highest + 3)) + "\n")
    chains, refusal = sr.resolve_supplement_chains(gapped)
    assert chains == {} and refusal is not None
    assert refusal.code == "supplement_seq_not_next_value", refusal.code

    repeated = (REAL_REGISTRY_TEXT + "\n"
                + row("P1", seq=str(highest + 1)) + "\n"
                + row("P1", sid=SID2, seq=str(highest + 1)) + "\n")
    chains, refusal = sr.resolve_supplement_chains(repeated)
    assert chains == {} and refusal is not None
    assert refusal.code == "supplement_seq_duplicate", refusal.code


def test_a_purely_synthetic_namespace_starts_at_one():
    """With no prior numbered row the expected value is 1, not 0 and not
    'anything larger than nothing'."""
    assert sr.resolve_supplement_chains(doc(row("P1", seq="1")))[1] is None
    for bad in ("0", "2", "14", "99"):
        chains, refusal = sr.resolve_supplement_chains(doc(row("P1", seq=bad)))
        assert chains == {} and refusal is not None, bad
        assert refusal.code == "supplement_seq_not_next_value", (bad,
                                                                 refusal.code)


def test_a_supplement_row_may_not_renumber_around_a_non_supplement_row():
    """SEQUENCE_NAMESPACE=GLOBAL: an S0-shaped numbered row occupies the
    slot, so the supplement row after it must take the next one."""
    s0 = (f"| 1 | {ROW_UTC} | **RUN_AUTHORIZED** | {C40} | Aaron "
          "| synthetic non-supplement row |")
    chains, refusal = sr.resolve_supplement_chains(doc(s0, row("P1", seq="2")))
    assert refusal is None, f"unexpected refusal: {refusal}"
    assert sorted(chains) == [SID]
    for bad in ("1", "3", "87"):
        chains, refusal = sr.resolve_supplement_chains(
            doc(s0, row("P1", seq=bad)))
        assert chains == {} and refusal is not None, bad
        assert refusal.code in ("supplement_seq_not_next_value",
                                "supplement_seq_duplicate"), refusal.code


# ===========================================================================
# 10 — integer floors: every count counts a thing that exists
# ===========================================================================

INT_FLOOR_CASES = (
    ("P4", "n_rows"),
    ("P5", "n_cells"),
    ("A2", "n_files"),
    ("AX", "attempts_count"),
    ("P2S", "supersedes_event_sequence"),
    ("T1", "superseded_at_event"),
)


def test_every_int_min_field_is_covered_by_this_battery():
    """If a floor is added upstream this goes RED instead of leaving the
    new field silently untested."""
    assert set(sr._INT_MIN) == {key for _, key in INT_FLOOR_CASES}
    assert set(sr._INT_MIN.values()) == {1}


@pytest.mark.parametrize("short,key", INT_FLOOR_CASES)
@pytest.mark.parametrize("value", ["0", "-1", "-7", "-000", "00",
                                   "-99999999999999999999"])
def test_integer_field_below_minimum(short, key, value):
    """THE PINNED DEFECT. `-?[0-9]+` was the whole check at 617f7c3, so
    each value below is asserted to SATISFY the old predicate first — the
    floor, not the shape check, is what refuses it."""
    assert OLD_INT_PREDICATE.fullmatch(value), (
        f"{value!r} does not satisfy the pre-repair predicate, so this "
        "case would not prove the floor is what refuses")
    if value not in ("0", "00", "-000"):
        assert int(value) < 0
    refusal = row_refusal(row(short, over={key: value}))
    assert refusal.code == "integer_field_below_minimum", (
        f"{short}.{key}={value}: {refusal.code}")
    assert key in str(refusal), str(refusal)


@pytest.mark.parametrize("short,key", INT_FLOOR_CASES)
def test_smallest_legal_integer_value_is_accepted(short, key):
    event = row_accepted(row(short, over={key: "1"}))
    assert event.fields[key] == "1"


@pytest.mark.parametrize("short,key", INT_FLOOR_CASES)
def test_non_integers_still_refuse_under_the_shape_code(short, key):
    """The floor must not have swallowed the older, coarser check."""
    for value in ("1.5", "1e3", "one", "+1", "1 1", "0x1", "١", "1_0",
                  "- 1", "1-", "٣"):
        refusal = row_refusal(row(short, over={key: value}))
        assert refusal.code == "integer_field_not_integer", (value,
                                                             refusal.code)


@pytest.mark.parametrize("short,key", INT_FLOOR_CASES)
def test_surrounding_whitespace_in_an_integer_field_is_stripped(short, key):
    """Measured, and pinned so it is a decision rather than an accident:
    `_parse_fields` strips the value, so `n_rows:  1 ` is the integer 1
    and is ACCEPTED. Padding therefore cannot be used to smuggle a value
    past either the shape check or the floor."""
    assert row_accepted(row(short, over={key: " 1"})).fields[key] == "1"
    assert row_accepted(row(short, over={key: "1  "})).fields[key] == "1"
    refusal = row_refusal(row(short, over={key: "  0  "}))
    assert refusal.code == "integer_field_below_minimum", refusal.code


# ===========================================================================
# 11 — the authorized `output_root` field
# ===========================================================================

def test_absolute_output_root_is_accepted():
    event = row_accepted(row("P2"))
    assert event.output_root == SYNTH_ROOT


@pytest.mark.parametrize("value", [
    "runs",
    "." + SEP + "runs",
    ".." + SEP + "quant-data",
    "quant-data" + SEP + "itsf-runs",
    "/quant-data/itsf-runs",      # rooted but driveless: not absolute here
    "/",
    "C:",                          # a drive with no root
    "itsf-runs",
])
def test_relative_output_root_is_refused(value):
    """THE PINNED DEFECT. A relative root names a directory that depends
    on the runner's working directory — it can never be the one governed
    place the evidence may land."""
    refusal = row_refusal(row("P2", over={"output_root": value}))
    assert refusal.code == "output_root_not_absolute", (value, refusal.code)


def test_null_byte_output_root_is_refused():
    value = "C:" + SEP + "quant-data" + NUL + SEP + "itsf-runs"
    refusal = row_refusal(row("P2", over={"output_root": value}))
    assert refusal.code == "output_root_not_normalisable", refusal.code


def test_blank_output_root_is_refused_before_it_reaches_its_own_code():
    """A blank root IS refused — but under `field_value_empty`, because
    `_parse_fields` strips and rejects an empty value before
    `_check_field_values` ever runs. See `test_finding_output_root_blank_
    is_unreachable`."""
    for value in ("", "   ", "\t", " \u00a0 ", "\u2003"):
        refusal = row_refusal(row("P2", over={"output_root": value}))
        assert refusal.code == "field_value_empty", (repr(value),
                                                     refusal.code)


def test_line_boundary_characters_in_a_note_fail_closed():
    """`str.splitlines()` also breaks on vertical tab, form feed,
    the file/group/record separators, NEL, LINE SEPARATOR and
    PARAGRAPH SEPARATOR, so one of those inside a note tears the row
    in two. Policy B must catch the wreckage rather than let half a
    row through -- measured for each separator."""
    for ch in ("\u000b", "\u000c", "\u001c", "\u001d", "\u001e",
               "\u0085", "\u2028", "\u2029"):
        for value in (ch, "C:" + SEP + "a" + ch + "b"):
            refusal = row_refusal(row("P2", over={"output_root": value}))
            assert refusal.code == "supplement_row_malformed", (
                repr(value), refusal.code)


def test_traversal_in_output_root_is_normalised_not_rejected():
    """`..` segments are collapsed by `normpath`, so an absolute root that
    walks upward is accepted in its normalised form. Pinned deliberately:
    the binding gate re-normalises with the same rule, so the two agree."""
    value = ("C:" + SEP + "quant-data" + SEP + "x" + SEP + ".." + SEP
             + "itsf-runs")
    event = row_accepted(row("P2", over={"output_root": value}))
    assert os.path.normpath(event.output_root) == \
        "C:" + SEP + "quant-data" + SEP + "itsf-runs"


def test_p2_row_and_sentence_commit_must_agree():
    """Guards the fixture itself: the P2 rows above are internally
    consistent, so an output_root refusal is never a mislabelled commit
    mismatch."""
    refusal = row_refusal(row("P2", over={"authorized_commit": "b" * 40}))
    assert refusal.code == "p2_row_commit_cell_ne_sentence_commit", refusal.code


# ===========================================================================
# 12 — DISCLOSED RESIDUALS (characterization records that STAND)
# ===========================================================================
#
# The trailing-newline finding that used to live here was REPAIRED, and
# swept as a class across all seven anchored patterns, so its two tests
# were flipped into refusals and moved up into sections 0, 4 and 5.
#
# What remains are the three residuals the owning lane disclosed
# DELIBERATELY rather than changed: two unreachable-by-construction
# branches kept as defence in depth, and one gate-code scheme working as
# designed (an F1 row records `gate_name`; the detail string separates
# the causes). Each stays pinned so it is a recorded decision rather
# than an untested branch — better than deleting the code.

def test_finding_output_root_blank_code_is_unreachable():
    """FINDING (low). `output_root_blank` is declared in `REFUSAL_CODES`
    and raised in `_check_field_values`, but NOTHING can reach it:
    `_parse_fields` already `.strip()`s the value and refuses an empty one
    with `field_value_empty`, and `.strip()` is idempotent, so
    `raw = value.strip()` can never be falsy by the time the output_root
    branch runs. `_check_field_values` has exactly one caller
    (`_classify_and_validate`), so there is no second route.

    SHOULD BE: either the blank case is reported under its own code, or
    the code is retired. This test pins the gap so it cannot be forgotten
    — a blank root IS still refused, which is why this is low, not high."""
    assert "output_root_blank" in sr.REFUSAL_CODES
    for value in ("", " ", "\t", "\u00a0", " \u2003 "):
        line = row("P2", over={"output_root": value})
        events, refusal = sr.parse_supplement_events(doc(line))
        assert refusal is not None, repr(value)
        assert refusal.code != "output_root_blank", (
            "output_root_blank became reachable — good; flip this test to "
            "assert it directly")
        assert refusal.code in ("field_value_empty",
                                "output_root_not_absolute"), (repr(value),
                                                              refusal.code)


def test_finding_escape_and_basename_codes_have_no_reachable_input():
    """FINDING (informational). `plan_target_escapes_root` and
    `plan_basename_divergence` cannot fire through the public signature:
    both targets are built from ONE `dir_name` that has already passed the
    id and stamp grammars, so the basenames are equal by construction and
    no traversal segment survives. They are defence in depth, not live
    checks — nothing in this battery could reach them, and this test
    records that honestly rather than leaving a silent coverage hole."""
    for bad_id in ("..", "." + SEP + "..", SID + SEP + "x"):
        assert not sc.SUPPLEMENT_ID_PATTERN.match(bad_id), bad_id
    for bad_stamp in ("..", UTC + SEP + "..", SEP):
        assert not r.UTC_STAMP_RE.match(bad_stamp), bad_stamp
    src = Path(r.__file__).read_text(encoding="utf-8")
    assert "plan_target_escapes_root" in src
    assert "plan_basename_divergence" in src


def test_finding_binding_gate_collapses_distinct_causes_into_one_code():
    """FINDING (informational). `_g_output_root_structure` raises
    `gate_refused:output_root_structure` for eight different causes —
    missing root, relative root, absent root, non-directory, reparse
    point, blank authorization, relative authorization, and the
    root-mismatch the repair added. An F1 row records `gate_name`, so the
    registry cannot distinguish 'Aaron authorized the wrong root' from
    'the disk is missing'. The detail string carries it; the CODE does
    not."""
    src = Path(r.__file__).read_text(encoding="utf-8")
    body = src.split("def _g_output_root_structure(")[1]
    body = body.split("\ndef ")[0]
    assert body.count('_fail("A_PRECHECK", "output_root_structure"') >= 8, (
        body.count('_fail("A_PRECHECK", "output_root_structure"'))


# ===========================================================================
# 13 — closing invariant
# ===========================================================================

def test_the_lease_guard_itself_refuses_a_governed_root():
    """`_forbid_governed` is the runtime lease: every planner call and
    every gate call in this file passes both roots through it. Proven
    here so the guard cannot rot into a no-op that silently permits a
    governed root."""
    for governed in (RULED_RUNS_ROOT, RULED_ARCHIVE_ROOT):
        for candidate in (governed, governed.lower(),
                          governed + SEP + "supplements",
                          Path(governed) / "supplements" / f"{SID}_{UTC}"):
            with pytest.raises(AssertionError, match="governed root"):
                _forbid_governed(candidate)
    # ...and lets an unrelated absolute path through
    _forbid_governed(SYNTH_ROOT)
    _forbid_governed(None)
    _forbid_governed("")


def test_every_planner_entry_point_in_this_file_is_lease_guarded(tmp_path):
    runs, arch = roots(tmp_path)
    calls = []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys.modules[__name__], "_forbid_governed",
                   lambda root: calls.append(root))
        plan_ok(runs, arch, watch=(tmp_path,))
        gate_ok("output_root_structure",
                ctx(declared=str(runs), runs_root=runs, archive_root=arch),
                watch=(tmp_path,))
    assert calls.count(runs) == 2 and calls.count(arch) == 2, calls


def test_governed_subtrees_still_empty_after_the_battery():
    """The battery plans hundreds of paths. None may leave a byte behind."""
    from _governed_subtrees import assert_governed_subtrees_are_empty
    assert_governed_subtrees_are_empty(Path(__file__).resolve().parents[1])
