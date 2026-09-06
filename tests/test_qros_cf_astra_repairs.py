"""The six BLOCKING findings a fresh GPT-6 Astra seat reproduced, and the
settling test for each.

Every case here was REPRODUCED FIRST on the tree at 48cd510 -- the repair
followed the counterexample, not the other way round. Each test drives the
exact failure path Astra described and asserts the intended invariant, and
each is paired with the positive path so a repair that simply refuses
everything cannot pass.

F01  a modified timestamp-valid .pyc executes while governed source identity,
     dirty paths and the seam all pass
F02  a startup .pth/import hook changes semantics while every locked version
     still matches
F03  _local_manifest.json outranks the authorized manifest
F04  condition.json verified by pathname, then re-read from pathname
F05  a malformed OWNER_HOLD row is silently dropped and a start proceeds
F06  OWNER_HOLD committed between the hold check and the P3 append

Nothing here touches the real registry, the authorized job dir, the sealed
runs or site-packages: every case is a tmp_path or an injected report.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import marshal
import os
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf import execution_identity as ei          # noqa: E402
from itsf.data import manifests as M               # noqa: E402
from itsf.mc import owner_control as oc            # noqa: E402
from itsf.mc import registry_boundary as rb        # noqa: E402
from itsf.mc import supplement_registry as sreg    # noqa: E402


# ===========================================================================
# F01 — executed code must match authorized source semantics
# ===========================================================================

def test_F01_the_governed_identity_does_not_and_cannot_cover_a_pyc():
    """The root cause, stated as a fact rather than a claim: the identity is
    built from git-tracked blobs and __pycache__ is gitignored, so no cache
    file can ever appear in it."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    entries = ei.governed_entries(head)
    paths = [e[0] if isinstance(e, (tuple, list)) else str(e) for e in entries]
    assert paths, "the identity is empty; this test would prove nothing"
    assert [p for p in paths if str(p).endswith(".pyc")] == []
    assert [p for p in paths if "__pycache__" in str(p)] == []
    ignored = subprocess.run(
        ["git", "check-ignore", "src/itsf/mc/__pycache__/x.cpython-313.pyc"],
        cwd=REPO, capture_output=True, text=True)
    assert ignored.returncode == 0, "__pycache__ is no longer gitignored"


def test_F01_a_tampered_timestamp_valid_cache_executes_by_default(tmp_path):
    """ASTRA'S COUNTEREXAMPLE, reproduced. The source is never modified; only
    the cache is, and its 16-byte header is preserved so Python trusts it."""
    pkg = tmp_path / "toy"
    pkg.mkdir()
    (pkg / "__init__.py").write_bytes(b"")
    src = pkg / "semantics.py"
    src.write_bytes(b"def rth_close_minute():\n    return 960\n")
    py_compile.compile(str(src), doraise=True)
    cache = Path(importlib.util.cache_from_source(str(src)))
    header = cache.read_bytes()[:16]
    cache.write_bytes(header + marshal.dumps(
        compile("def rth_close_minute():\n    return 1\n", str(src), "exec")))
    assert src.read_bytes() == b"def rth_close_minute():\n    return 960\n"
    assert cache.read_bytes()[:16] == header
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, r'%s');"
         "import toy.semantics as s; print(s.rth_close_minute())" % tmp_path],
        capture_output=True, text=True)
    assert r.stdout.strip() == "1", "the tamper no longer reproduces: " + r.stderr[-200:]


def test_F01_the_repair_makes_the_authorized_source_semantics_execute(tmp_path):
    """SETTLING TEST, first branch of the two Astra allows: under the launch
    conditions the seam now requires, the tampered cache is not read and the
    authorized source runs."""
    pkg = tmp_path / "toy"
    pkg.mkdir()
    (pkg / "__init__.py").write_bytes(b"")
    src = pkg / "semantics.py"
    src.write_bytes(b"def rth_close_minute():\n    return 960\n")
    py_compile.compile(str(src), doraise=True)
    cache = Path(importlib.util.cache_from_source(str(src)))
    cache.write_bytes(cache.read_bytes()[:16] + marshal.dumps(
        compile("def rth_close_minute():\n    return 1\n", str(src), "exec")))
    prefix = tmp_path / "private-cache"
    env = dict(os.environ, PYTHONPYCACHEPREFIX=str(prefix))
    r = subprocess.run(
        [sys.executable, "-B", "-c",
         "import sys; sys.path.insert(0, r'%s');"
         "import toy.semantics as s; print(s.rth_close_minute())" % tmp_path],
        capture_output=True, text=True, env=env)
    assert r.stdout.strip() == "960", r.stderr[-300:]
    assert list(prefix.rglob("*.pyc")) == [], "-B wrote a cache anyway"


def test_F01_the_seam_refuses_when_a_governed_cache_is_readable():
    """SETTLING TEST, second branch: refusal BEFORE P3. Measured on the real
    interpreter state -- the suite does not run with -B, so the report is
    legitimately negative here, which is what makes this assertion real."""
    report = ei.bytecode_report()
    assert report.from_source is False
    assert "dont_write_bytecode" in report.detail or "pycache_prefix" in report.detail
    with pytest.raises(ei.SeamRefused) as caught:
        ei.seam_recheck("0" * 40, bytecode=report,
                        environment=ei.EnvironmentReport(True, "ok"),
                        startup=ei.StartupReport(True, "ok"),
                        repo=REPO)
    assert caught.value.code in ("seam_head_moved", "seam_bytecode_cache_readable")


def test_F01_the_positive_path_still_passes():
    """A repair that refused unconditionally would be useless."""
    ok = ei.bytecode_report(dont_write=True, prefix="/private", governed_sources=[])
    assert ok.from_source is True and ok.caches_found == 0


def test_F01_a_cache_present_under_the_active_prefix_still_refuses(tmp_path):
    """The third fact the report rests on: a cache that EXISTS can be read,
    so its presence is what refuses -- not merely a missing flag."""
    src = tmp_path / "m.py"
    src.write_bytes(b"x = 1\n")
    py_compile.compile(str(src), doraise=True)
    assert Path(importlib.util.cache_from_source(str(src))).exists()
    r = ei.bytecode_report(dont_write=True, prefix="/private",
                           governed_sources=[src])
    assert r.from_source is False and r.caches_found == 1
    assert "already have a cache" in r.detail


# ===========================================================================
# F02 — startup / import environment
# ===========================================================================

def test_F02_a_pth_import_line_executes_at_startup(tmp_path):
    """ASTRA'S COUNTEREXAMPLE, reproduced in an isolated site dir."""
    (tmp_path / "hook_payload.py").write_bytes(
        b"import builtins\nbuiltins.__ITSF_HOOK_RAN__ = True\n")
    (tmp_path / "zz_hook.pth").write_bytes(b"import hook_payload\n")
    r = subprocess.run(
        [sys.executable, "-c",
         "import site, sys; sys.path.insert(0, r'%s'); site.addsitedir(r'%s');"
         "import builtins; print(getattr(builtins, '__ITSF_HOOK_RAN__', False))"
         % (tmp_path, tmp_path)],
        capture_output=True, text=True)
    assert r.stdout.strip() == "True", r.stderr[-200:]


def test_F02_version_metadata_cannot_see_such_a_hook():
    """Why the lockfile gate is the wrong instrument: it is green regardless."""
    env = ei.measure_environment()
    assert env.pinned is True and env.packages_checked >= 1


def test_F02_an_unexpected_executable_pth_is_refused(tmp_path):
    """SETTLING TEST. A synthetic executable .pth in an injected site dir."""
    (tmp_path / "zz_hook.pth").write_bytes(b"import hook_payload\n")
    r = ei.startup_report(sitedirs=[str(tmp_path)], find_spec=lambda n: None)
    assert r.pinned is False
    assert "zz_hook.pth" in r.detail
    with pytest.raises(ei.SeamRefused) as caught:
        ei.seam_recheck("0" * 40, startup=r,
                        environment=ei.EnvironmentReport(True, "ok"),
                        bytecode=ei.BytecodeReport(True, "ok"), repo=REPO)
    assert caught.value.code in ("seam_head_moved", "seam_startup_surface_unpinned")


def test_F02_a_data_only_pth_is_not_refused(tmp_path):
    """Bare path lines add import paths and execute nothing, so refusing them
    would be a machine hash by the back door -- which the finding excludes."""
    (tmp_path / "data_only.pth").write_bytes(b"../some/dir\n")
    r = ei.startup_report(sitedirs=[str(tmp_path)], find_spec=lambda n: None)
    assert r.pinned is True, r.detail


def test_F02_sitecustomize_or_usercustomize_is_refused(tmp_path):
    for name in ei.FORBIDDEN_STARTUP_MODULES:
        r = ei.startup_report(
            sitedirs=[str(tmp_path)],
            find_spec=lambda n, _n=name: object() if n == _n else None)
        assert r.pinned is False and name in r.detail


def test_F02_the_required_packages_are_preserved():
    """The pin is the real census, not an empty set: the two .pth files the
    installed packages need are expected, and today's machine is pinned."""
    assert ei.EXPECTED_EXECUTABLE_PTH
    live = ei.startup_report()
    assert live.pinned is True, live.detail
    assert set(live.executable_pth) <= ei.EXPECTED_EXECUTABLE_PTH


# ===========================================================================
# F03 — one authorized manifest authority
# ===========================================================================

def _job_dir(tmp_path, condition_bytes, official_sha):
    d = tmp_path
    (d / "condition.json").write_bytes(condition_bytes)
    (d / "manifest.json").write_text(json.dumps({
        "job_id": "j",
        "files": [{"filename": "condition.json", "hash": "sha256:" + official_sha}]}),
        encoding="utf-8")
    return d


def test_F03_the_legacy_loader_still_prefers_local_for_fixtures(tmp_path):
    """The reproduction, and the reason the old entry is KEPT: fabricated
    fixtures depend on it. It simply may not be the production authority."""
    replacement = b'[{"date": "2020-03-16", "condition": "degraded"}]'
    d = _job_dir(tmp_path, replacement, "a" * 64)
    (d / "_local_manifest.json").write_text(json.dumps({"files": {
        "condition.json": {"sha256": hashlib.sha256(replacement).hexdigest()}}}),
        encoding="utf-8")
    man = M.load_manifest(d)
    assert "source" not in man, "the local manifest no longer wins"
    M.verify_file_against_manifest(d / "condition.json", man)   # passes


def test_F03_the_authorized_loader_ignores_the_local_manifest(tmp_path):
    """SETTLING TEST: authorized manifest unchanged + conflicting local
    manifest + replacement condition.json must refuse."""
    replacement = b'[{"date": "2020-03-16", "condition": "degraded"}]'
    d = _job_dir(tmp_path, replacement, "a" * 64)
    (d / "_local_manifest.json").write_text(json.dumps({"files": {
        "condition.json": {"sha256": hashlib.sha256(replacement).hexdigest()}}}),
        encoding="utf-8")
    man = M.load_authorized_manifest(d)
    assert man["source"] == "databento_manifest_json"
    assert man["files"]["condition.json"]["sha256"] == "a" * 64
    with pytest.raises(M.ManifestError) as caught:
        M.read_verified_bytes(d / "condition.json", man)
    assert "sha256 mismatch" in str(caught.value)


def test_F03_the_positive_path_consumes_the_authorized_bytes(tmp_path):
    good = b'[{"date": "2020-03-16", "condition": "available"}]'
    d = _job_dir(tmp_path, good, hashlib.sha256(good).hexdigest())
    (d / "_local_manifest.json").write_text(json.dumps({"files": {
        "condition.json": {"sha256": "b" * 64}}}), encoding="utf-8")
    got = M.read_verified_bytes(d / "condition.json",
                               M.load_authorized_manifest(d))
    assert got == good


def test_F03_the_production_path_uses_the_authorized_loader():
    """Structural, because the behavioural half needs the authorized job dir:
    the governed reader must not go through the local-preferring entry."""
    import inspect
    from itsf.mc import production_inputs as pi
    body = inspect.getsource(pi.build_session_schedule)
    assert "load_authorized_manifest" in body
    assert "load_manifest(" not in body
    assert "read_verified_bytes" in body


def test_F03_an_absent_official_manifest_refuses_rather_than_falling_back(tmp_path):
    (tmp_path / "_local_manifest.json").write_text(
        json.dumps({"files": {"condition.json": {"sha256": "c" * 64}}}),
        encoding="utf-8")
    with pytest.raises(M.ManifestError) as caught:
        M.load_authorized_manifest(tmp_path)
    assert "no manifest.json" in str(caught.value)


# ===========================================================================
# F04 — verify bytes, consume the same bytes
# ===========================================================================

def test_F04_pathname_verification_can_be_raced(tmp_path):
    """ASTRA'S COUNTEREXAMPLE, reproduced against the legacy entry."""
    good = b'[{"date": "2020-03-16", "condition": "available"}]'
    evil = b'[{"date": "2020-03-16", "condition": "degraded"}]'
    d = _job_dir(tmp_path, good, hashlib.sha256(good).hexdigest())
    man = M.load_authorized_manifest(d)
    M.verify_file_against_manifest(d / "condition.json", man)
    (d / "condition.json").write_bytes(evil)                   # the swap
    consumed = json.loads((d / "condition.json").read_text(encoding="utf-8"))
    assert consumed[0]["condition"] == "degraded"


def test_F04_verified_bytes_are_the_consumed_bytes(tmp_path):
    """SETTLING TEST: the payload is captured, so a later swap cannot change
    what was consumed."""
    good = b'[{"date": "2020-03-16", "condition": "available"}]'
    evil = b'[{"date": "2020-03-16", "condition": "degraded"}]'
    d = _job_dir(tmp_path, good, hashlib.sha256(good).hexdigest())
    man = M.load_authorized_manifest(d)
    captured = M.read_verified_bytes(d / "condition.json", man)
    (d / "condition.json").write_bytes(evil)                   # the same swap
    assert json.loads(captured.decode("utf-8"))[0]["condition"] == "available"


def test_F04_replacement_bytes_are_never_consumed(tmp_path):
    """The other legal outcome: if the swap lands BEFORE the read, the
    digest check refuses. Either way the replacement is never parsed."""
    good = b'[{"date": "2020-03-16", "condition": "available"}]'
    evil = b'[{"date": "2020-03-16", "condition": "degraded"}]'
    d = _job_dir(tmp_path, good, hashlib.sha256(good).hexdigest())
    (d / "condition.json").write_bytes(evil)
    with pytest.raises(M.ManifestError):
        M.read_verified_bytes(d / "condition.json",
                             M.load_authorized_manifest(d))


def test_F04_verify_bytes_returns_the_payload_it_checked():
    man = {"files": {"x": {"sha256": hashlib.sha256(b"hello").hexdigest()}}}
    assert M.verify_bytes_against_manifest("x", b"hello", man) == b"hello"
    with pytest.raises(M.ManifestError):
        M.verify_bytes_against_manifest("x", b"hellp", man)


# ===========================================================================
# F05 — owner tokens must fail closed
# ===========================================================================

LIVE_REGISTRY = (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(encoding="utf-8")
RUN_ID = "MC-DS-S004"
C40 = "a" * 40

MALFORMED_HOLDS = {
    "missing_final_pipe":
        "| 90 | 2026-09-07T00:00:00+00:00 | OWNER_HOLD | " + C40
        + " | Aaron | [GLOBAL] reason: stop everything",
    "extra_pipe_inside_reason":
        "| 90 | 2026-09-07T00:00:00+00:00 | OWNER_HOLD | " + C40
        + " | Aaron | [GLOBAL] reason: stop | everything |",
    "too_few_cells":
        "| 90 | OWNER_HOLD | Aaron | [GLOBAL] reason: stop |",
    "malformed_actor_token_still_recognizable":
        "| 90 | 2026-09-07T00:00:00+00:00 | OWNER_HOLD | " + C40
        + " | | [GLOBAL] reason: stop",
}


@pytest.mark.parametrize("label", sorted(MALFORMED_HOLDS))
def test_F05_a_malformed_hold_refuses_and_never_reads_as_no_hold(label):
    """SETTLING TEST. Before the repair each of these returned NO ACTIVE
    HOLDS: the shared row parser never yielded the line, so the owner's hold
    disappeared. Now the intent is detected before anything is discarded."""
    text = LIVE_REGISTRY + MALFORMED_HOLDS[label] + "\n"
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.active_holds(text, RUN_ID)
    assert caught.value.code in ("owner_control_row_unreadable",
                                 "owner_control_row_malformed",
                                 "owner_control_actor_not_owner")
    with pytest.raises(oc.OwnerControlRefusal):
        oc.assert_no_owner_hold(text, RUN_ID)


@pytest.mark.parametrize("label", sorted(MALFORMED_HOLDS))
def test_F05_a_malformed_hold_blocks_p3_and_writes_no_byte(tmp_path, label):
    """The consequence that matters: registry bytes unchanged, and no P3."""
    import test_mc_supplement_registry as T
    from itsf import contracts
    T.ROOT = str(contracts.RULED_RUNS_ROOT)
    reg = T.Reg()
    reg.commit[T.SID] = C40
    for short in ("P1", "P2"):
        reg.add(short, sid=T.SID)
    path = tmp_path / "TRIAL_REGISTRY.md"
    body = reg.text() + MALFORMED_HOLDS[label] + "\n"
    path.write_bytes(body.encode("utf-8"))
    frozen = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(T.SID, head_commit=C40,
                              utc_stamp="2026-09-07T00:00:01+00:00", path=path)
    assert caught.value.code in ("p3_owner_control_row_unreadable",
                                 "p3_owner_hold_in_force",
                                 "p3_chain_does_not_resolve")
    assert path.read_bytes() == frozen
    assert "SUPPLEMENT_RUN_STARTED" not in path.read_text(encoding="utf-8")


def test_F05_a_WELL_FORMED_hold_is_still_read_as_a_hold():
    """The positive path: the repair must not have turned every hold into a
    parse refusal."""
    good = ("| 90 | 2026-09-07T00:00:00+00:00 | OWNER_HOLD | " + C40
            + " | Aaron | [GLOBAL] reason: stop everything |")
    holds = oc.active_holds(LIVE_REGISTRY + good + "\n", RUN_ID)
    assert len(holds) == 1 and holds[0].scope == "GLOBAL"
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.assert_no_owner_hold(LIVE_REGISTRY + good + "\n", RUN_ID)
    assert caught.value.code == "owner_hold_in_force"


def test_F05_the_live_registry_carries_no_owner_row_and_still_parses():
    """The other positive path, on the real ledger: no owner intent, no
    refusal, no hold."""
    assert oc.owner_intent_lines(LIVE_REGISTRY) == ()
    assert oc.active_holds(LIVE_REGISTRY, RUN_ID) == ()
    oc.assert_no_owner_hold(LIVE_REGISTRY, RUN_ID)


def test_F05_intent_is_read_from_the_raw_text_not_the_parser():
    """The mechanism, pinned: a line the shared parser drops is still seen."""
    dropped = MALFORMED_HOLDS["missing_final_pipe"]
    rows, refusal = sreg.parse_registry_rows(dropped + "\n")
    owner_rows = [r for r in rows if "OWNER" in r.event]
    assert owner_rows == [] and refusal is None, "the parser now yields it"
    assert len(oc.owner_intent_lines(dropped + "\n")) == 1


# ===========================================================================
# F06 — atomic owner-hold check + P3 append
# ===========================================================================

HOLD_ROW = ("| 90 | 2026-09-07T00:00:00+00:00 | OWNER_HOLD | " + C40
            + " | Aaron | [GLOBAL] reason: stop |")


def _two_row_ledger(path):
    import test_mc_supplement_registry as T
    from itsf import contracts
    T.ROOT = str(contracts.RULED_RUNS_ROOT)
    reg = T.Reg()
    reg.commit[T.SID] = C40
    for short in ("P1", "P2"):
        reg.add(short, sid=T.SID)
    path.write_bytes(reg.text().encode("utf-8"))
    return T.SID


def test_F06_case_A_a_hold_committed_before_the_write_refuses(tmp_path, monkeypatch):
    """ASTRA'S BOUNDARY, deterministically interleaved: the hold lands after
    every check has decided and before the append. Legal order A -- the hold
    wins serialization, so P3 must refuse and write nothing."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = _two_row_ledger(path)
    original = rb._compare_and_append

    def interleave(target, decided, addition):
        target.write_bytes(target.read_bytes() + (HOLD_ROW + "\n").encode("utf-8"))
        return original(target, decided, addition)

    monkeypatch.setattr(rb, "_compare_and_append", interleave)
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40,
                              utc_stamp="2026-09-07T00:00:01+00:00", path=path)
    assert caught.value.code == "p3_registry_changed_under_decision"
    text = path.read_text(encoding="utf-8")
    assert "SUPPLEMENT_RUN_STARTED" not in text, "P3 bytes were written"
    assert "OWNER_HOLD" in text, "the interleaved hold was lost"


def test_F06_case_B_when_nothing_interleaves_the_start_commits(tmp_path):
    """Legal order B: the append wins serialization, so P3 is committed."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = _two_row_ledger(path)
    row = rb.append_run_started(sid, head_commit=C40,
                                utc_stamp="2026-09-07T00:00:02+00:00", path=path)
    text = path.read_text(encoding="utf-8")
    assert row in text
    chain = sreg.resolve_supplement_chain(text, sid)
    assert chain.started is True and "P3" in chain.short_ids


def test_F06_case_B_a_hold_appended_AFTER_p3_does_not_unauthorize_it(tmp_path):
    """The other half of order B: a later hold is ordered after STARTED and
    does not retroactively make the started event unauthorized."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = _two_row_ledger(path)
    rb.append_run_started(sid, head_commit=C40,
                          utc_stamp="2026-09-07T00:00:02+00:00", path=path)
    path.write_bytes(path.read_bytes() + (HOLD_ROW + "\n").encode("utf-8"))
    text = path.read_text(encoding="utf-8")
    chain = sreg.resolve_supplement_chain(text, sid)
    assert chain.started is True and "P3" in chain.short_ids
    assert oc.active_holds(text, sid), "the later hold is not readable"
    lines = text.splitlines()
    p3_at = next(i for i, l in enumerate(lines) if "SUPPLEMENT_RUN_STARTED" in l)
    hold_at = next(i for i, l in enumerate(lines) if "OWNER_HOLD" in l)
    assert p3_at < hold_at, "the committed order is not STARTED-then-HOLD"


def test_F06_the_decision_and_the_append_share_one_version(tmp_path):
    """The invariant itself: ANY change under the decision refuses, not just
    a hold. A repair that special-cased OWNER_HOLD would leave the race."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = _two_row_ledger(path)
    original = rb._compare_and_append

    def interleave(target, decided, addition):
        target.write_bytes(target.read_bytes() + b"| + | x | NOTE | y | z | w |\n")
        return original(target, decided, addition)

    import unittest.mock as mock
    with mock.patch.object(rb, "_compare_and_append", interleave):
        with pytest.raises(rb.AppendRefused) as caught:
            rb.append_run_started(sid, head_commit=C40,
                                  utc_stamp="2026-09-07T00:00:03+00:00",
                                  path=path)
    assert caught.value.code == "p3_registry_changed_under_decision"
    assert "SUPPLEMENT_RUN_STARTED" not in path.read_text(encoding="utf-8")


def _code_only(func) -> str:
    """`func`'s source with comments and docstrings stripped.

    The first version of the test below grepped the raw source and matched the
    COMMENT that describes the removed line -- the guard read the commentary
    instead of the code, which is the exact defect class this repository has
    been bitten by before. Counted on the AST instead."""
    import ast
    import inspect
    import textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    for node in ast.walk(tree):
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Module))
                and node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))


def test_F06_there_is_exactly_one_read_behind_the_decision():
    """Structural: the second independent `target.read_bytes()` that created
    the window is gone, and the append goes through the CAS."""
    body = _code_only(rb.append_run_started)
    assert body.count("target.read_bytes()") == 1, body
    assert "decided = target.read_bytes()" in body
    assert "_compare_and_append(target, decided" in body
    assert "target.write_bytes(" not in body, \
        "append_run_started writes directly again, bypassing the CAS"


def test_F06_the_cas_is_the_only_writer_and_it_compares_first():
    """And the CAS itself: it reads under the lock, compares, then writes."""
    body = _code_only(rb._compare_and_append)
    assert "_AppendLock(target)" in body
    assert "now = target.read_bytes()" in body
    assert body.index("if now != decided") < body.index("target.write_bytes(")
    assert "decided + addition" in body


def test_F06_the_append_is_serialized_by_an_exclusive_lock(tmp_path):
    """The lock exists, is exclusive, is released, and a waiter refuses
    rather than proceeding unserialized."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    path.write_bytes(b"x\n")
    lock = path.with_name(path.name + rb.LOCK_SUFFIX)
    with rb._AppendLock(path):
        assert lock.exists()
        import time
        saved = rb.LOCK_TIMEOUT_SECONDS
        try:
            rb.LOCK_TIMEOUT_SECONDS = 0.05
            t0 = time.monotonic()
            with pytest.raises(rb.AppendRefused) as caught:
                with rb._AppendLock(path):
                    pass
            assert caught.value.code == "p3_append_lock_unavailable"
            assert time.monotonic() - t0 < 5
        finally:
            rb.LOCK_TIMEOUT_SECONDS = saved
    assert not lock.exists(), "the lock outlived its holder"


def test_F06_the_real_registry_is_untouched_by_this_file():
    """Nothing above may have written to the governed registry."""
    assert (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(
        encoding="utf-8") == LIVE_REGISTRY
    assert not (rb.REGISTRY_REPO_ROOT / (rb.REGISTRY_PATH + rb.LOCK_SUFFIX)).exists()
