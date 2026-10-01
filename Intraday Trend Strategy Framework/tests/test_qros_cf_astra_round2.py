"""ROUND TWO. The five findings Astra left STILL_BLOCKING after the first
repair, and the settling test for each.

Astra closed F04 and reproduced a remaining counterexample for F01, F02, F03,
F05 and F06. Every one of those five was reproduced again HERE, on the
already-repaired tree at 33f2384, before this round's fix was written -- so
each test below drives a boundary that a passing round-one repair still lost.

What was left standing, in one line each:

F01  the seam took a CENSUS of the cache directory, so an attacker who
     deletes the forged cache after it executes leaves a clean census. A
     current-state check cannot prove a historical negative.
F02  the startup pin was a FILENAME allowlist, so an allowed name carrying
     arbitrary executable content passed.
F03  only ONE caller was routed to the authorized manifest; four production
     call sites still read digests through the local-preferring entry.
F05  a malformed owner line became a refusal, but a legally-parsed line with
     a NON-CANONICAL scope (`[MC-DS-S004-]`) still applied to nothing.
F06  P3 got a lock and a compare-and-swap, and owner control got no
     sanctioned append at all -- so the lock had exactly one participant.

Two mechanisms carry the five, because F01/F02 share a root cause (a surface
that executes early, checked late) and F03/F06 each turn a per-caller choice
into a property of the boundary.

Nothing here touches the real registry, the authorized job dir or the sealed
runs. `LIVE_REGISTRY` is round one's read of the ledger, reused so this file
adds no second read, and every append case writes to a tmp_path copy.
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf import execution_identity as ei                    # noqa: E402
from itsf.data import manifests as M                         # noqa: E402
from itsf.mc import owner_control as oc                      # noqa: E402
from itsf.mc import production_inputs as pi                  # noqa: E402
from itsf.mc import registry_boundary as rb                  # noqa: E402
from itsf.mc import supplement_registry as sreg              # noqa: E402

from test_qros_cf_astra_repairs import (                     # noqa: E402
    C40, LIVE_REGISTRY, RUN_ID, _two_row_ledger)

UTC = "2026-09-07T00:00:00+00:00"


# ===========================================================================
# F01 — the proof moved BEFORE the governed imports
# ===========================================================================

class _Flags:
    """Stand-in for `sys.flags`, whose real attributes are READ-ONLY.

    `no_site` defaults to set, because these F01 cases are each about ONE
    other fact and a stub that failed the -S check first would test the
    wrong refusal. The -S fact has its own cases in
    `tests/test_qros_cf_pre_cert.py`."""

    def __init__(self, dont_write_bytecode, no_site=1):
        self.dont_write_bytecode = dont_write_bytecode
        self.no_site = no_site


@pytest.fixture
def clean_prefix(tmp_path):
    d = tmp_path / "private-pycache"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def _no_leaked_attestation(monkeypatch):
    """A test that attests must not attest for the next one."""
    monkeypatch.setattr(ei, "_LAUNCH_ATTESTATION", None, raising=False)


def _ok_modules():
    return {name: object() for name in ei.BOOTSTRAP_IMPORT_CLOSURE}


def test_F01_the_real_launch_flag_cannot_be_forged_in_process():
    """THE ROUND-ONE/ROUND-TWO DELTA, measured rather than argued.

    Round one read `sys.dont_write_bytecode` -- the plain writable mirror,
    which any in-process line can set. The attestation reads
    `sys.flags.dont_write_bytecode`, the launch flag on the read-only
    structseq. If that ever became writable this whole mechanism would be
    decoration, so the immutability is asserted and not assumed."""
    with pytest.raises((AttributeError, TypeError)):
        sys.flags.dont_write_bytecode = 1
    # and the writable mirror really is writable, which is why it is not read
    before = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        assert sys.dont_write_bytecode is True
    finally:
        sys.dont_write_bytecode = before


def test_F01_setting_only_the_writable_mirror_does_not_attest(clean_prefix,
                                                              monkeypatch):
    """The exact round-one bypass: satisfy the mutable knob and nothing else.

    This process is not launched with -B, so the read-only flag is 0 no
    matter what the mirror says."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    # pytest is launched with neither -S nor -B, so the real `sys.flags` fails
    # the no_site check FIRST. The fact under test here is the bytecode mirror,
    # so no_site is supplied as set and dont_write_bytecode is left at its real
    # (unset) value -- which is exactly the round-one bypass.
    flags = _Flags(sys.flags.dont_write_bytecode, no_site=1)
    with pytest.raises(ei.SeamRefused) as caught:
        ei.assert_governed_launch(flags=flags, prefix=str(clean_prefix),
                                  modules=_ok_modules())
    assert caught.value.args[0].startswith("launch_bytecode_writing_enabled")


def test_F01_ASTRA_the_attestation_must_precede_every_governed_import(
        clean_prefix):
    """ASTRA'S REMAINING COUNTEREXAMPLE, closed by ORDER rather than by a
    better census.

    Astra's move was: forge a timestamp-valid cache, let it execute, delete
    it, and the later census reports clean. Reproduced on the repaired tree --
    the altered semantics ran (1 where the source says 960) and
    `bytecode_report` still answered `from_source=True`.

    No strengthening of a current-state check can see that. What closes it is
    refusing to take the proof after the fact at all: if a governed module is
    already imported when the attestation is taken, the attestation is
    worthless for that module and says so."""
    modules = _ok_modules()
    modules["itsf.mc.owner_control"] = object()
    with pytest.raises(ei.SeamRefused) as caught:
        ei.assert_governed_launch(flags=_Flags(1), prefix=str(clean_prefix),
                                  modules=modules)
    code, _, detail = caught.value.args[0].partition(":")
    assert code == "launch_governed_modules_already_imported"
    assert "itsf.mc.owner_control" in detail


def test_F01_a_cache_that_exists_under_the_active_prefix_refuses(clean_prefix):
    """The other half of the proof: nothing to read, not merely nothing
    written. A cache file under the live prefix is a readable cache."""
    (clean_prefix / "semantics.cpython-313.pyc").write_bytes(b"\x00" * 20)
    with pytest.raises(ei.SeamRefused) as caught:
        ei.assert_governed_launch(flags=_Flags(1), prefix=str(clean_prefix),
                                  modules=_ok_modules())
    assert caught.value.args[0].startswith("launch_pycache_prefix_not_empty")


def test_F01_an_unset_prefix_refuses(clean_prefix):
    with pytest.raises(ei.SeamRefused) as caught:
        ei.assert_governed_launch(flags=_Flags(1), prefix="",
                                  modules=_ok_modules())
    assert caught.value.args[0].startswith("launch_pycache_prefix_unset")


def test_F01_THE_POSITIVE_PATH_a_correct_launch_attests(clean_prefix):
    """A repair that refuses everything is not a repair."""
    att = ei.assert_governed_launch(flags=_Flags(1), prefix=str(clean_prefix),
                                    modules=_ok_modules())
    assert att.caches_under_prefix == 0
    assert att.pycache_prefix == str(clean_prefix)
    assert ei.launch_attestation() is att


def test_F01_the_seam_refuses_without_an_attestation(monkeypatch):
    """MECHANICALLY ENFORCED, not merely available. `seam_recheck` has exactly
    one production caller, so requiring the attestation there is what stops an
    unattested run before its first side effect."""
    monkeypatch.setattr(ei, "_git", lambda repo, *a: C40 + "\n")
    monkeypatch.setattr(ei, "governed_dirty_paths", lambda *a, **k: ())
    kw = dict(environment=ei.EnvironmentReport(True, "ok"),
              bytecode=ei.BytecodeReport(True, "ok"),
              startup=ei.StartupReport(True, "ok"))
    with pytest.raises(ei.SeamRefused) as caught:
        ei.seam_recheck(C40, **kw)
    assert caught.value.args[0].startswith("seam_launch_not_attested")
    # and it passes once the launch is attested
    ei.seam_recheck(C40, launch=ei.LaunchAttestation("/p", 0, "injected"), **kw)


def test_F01_the_launcher_really_attests_end_to_end():
    """The whole boundary, in a real subprocess: re-launch with the measured
    flags, attest before the governed imports, then hand over."""
    # ROOT A: the sanctioned form is now the hardened one, and the unflagged
    # form refuses by design. Both halves asserted here.
    r = subprocess.run(
        [sys.executable, "-I", "-S", "-B",
         str(REPO / "scripts" / "run_governed.py"), "itsf.mc.owner_control"],
        capture_output=True, text=True, cwd=str(REPO))
    assert r.returncode == 0, r.stderr[-2000:]
    assert "attested before any governed import" in r.stderr
    assert "holds 0 caches" in r.stderr
    bare = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_governed.py"),
         "itsf.mc.owner_control"],
        capture_output=True, text=True, cwd=str(REPO))
    assert bare.returncode != 0, "the unflagged form no longer fails closed"
    assert "not a sanctioned production launch" in bare.stderr


def test_F01_no_production_source_mutates_the_cache_knobs():
    """THE RESIDUAL, closed by a guard instead of left implicit.

    Facts 1 and 2 hold for later imports only while the prefix stays put.
    `sys.pycache_prefix` and `sys.dont_write_bytecode` are both writable, so
    production code assigning either would silently reopen the repository's
    own `__pycache__`. Counted by AST across every production source."""
    offenders = []
    for root in ("src", "scripts"):
        for path in sorted((REPO / root).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Assign, ast.AugAssign)):
                    continue
                targets = (node.targets if isinstance(node, ast.Assign)
                           else [node.target])
                for t in targets:
                    if (isinstance(t, ast.Attribute)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == "sys"
                            and t.attr in ("pycache_prefix",
                                           "dont_write_bytecode")):
                        offenders.append(
                            f"{path.relative_to(REPO).as_posix()}:{t.lineno} "
                            f"assigns sys.{t.attr}")
                    if (isinstance(t, ast.Subscript)
                            and isinstance(t.value, ast.Attribute)
                            and t.value.attr == "environ"
                            and isinstance(t.slice, ast.Constant)
                            and t.slice.value in ("PYTHONPYCACHEPREFIX",
                                                  "PYTHONDONTWRITEBYTECODE")):
                        offenders.append(
                            f"{path.relative_to(REPO).as_posix()}:{t.lineno} "
                            f"assigns os.environ[{t.slice.value!r}]")
    assert offenders == [], (
        "production code mutates the launch knobs the attestation depends "
        "on:\n  " + "\n  ".join(offenders))


def test_F01_the_rejected_launch_flags_are_recorded_with_the_reason():
    """REWRITTEN AT THE PRE-CERT REPAIR, and the rewrite is the correction.

    This used to assert that `-S` "cannot be used" because `import pandas`
    fails under it, and pinned that as a decision. The measurement was real
    and the conclusion drawn from it was wrong: `-S` ALONE fails, `-S` plus
    the site directories on `sys.path` does not. So `-S` is now required
    rather than rejected, and it is what closes R1 and R2 by prevention.

    A test that pins a wrong conclusion is worse than no test, because it
    argues against fixing it. Kept, inverted, with the reason on the record."""
    assert ei.LAUNCH_FLAGS_REQUIRED == ("-S", "-B", "PYTHONPYCACHEPREFIX")
    doc = ei.assert_governed_launch.__doc__ or ""
    assert "read-only" in doc
    launcher = (REPO / "scripts" / "run_governed.py").read_text(encoding="utf-8")
    assert "-S" in launcher, "the launcher does not name the mechanism it uses"
    # -I and -E stay REJECTED, and their reasons are recorded where the
    # required-flags decision itself lives, not duplicated into the launcher.
    where = (REPO / "src" / "itsf" / "execution_identity.py").read_text(
        encoding="utf-8")
    for flag in ("-I", "-E"):
        assert flag in where, f"{flag}'s rejection is no longer recorded"
    assert "ignores PYTHONPYCACHEPREFIX" in where


# ===========================================================================
# F02 — trust by bytes, not by filename
# ===========================================================================

def _sitedir(tmp_path, name, body: bytes):
    d = tmp_path / "site"
    d.mkdir(exist_ok=True)
    (d / name).write_bytes(body)
    return d


def test_F02_ASTRA_an_allowed_name_with_changed_content_refuses(tmp_path):
    """ASTRA'S REMAINING COUNTEREXAMPLE. Reproduced on the repaired tree:
    `a1_coverage.pth` -- an ALLOWED filename -- rewritten to import an
    attacker's module executed at startup while `startup_report` answered
    `pinned=True`. A filename is not an identity."""
    name = sorted(ei.EXPECTED_EXECUTABLE_PTH)[0]
    d = _sitedir(tmp_path, name, b"import hook_payload\n")
    r = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert r.pinned is False
    assert "changed content" in r.detail and name in r.detail


def test_F02_THE_POSITIVE_PATH_pinned_bytes_pass(tmp_path, monkeypatch):
    """Matching bytes under a pinned name are accepted -- otherwise the
    required startup surface this machine genuinely needs would refuse."""
    name = sorted(ei.EXPECTED_EXECUTABLE_PTH)[0]
    body = b"import pip_system_certs.bootstrap\n"
    monkeypatch.setattr(ei, "EXPECTED_EXECUTABLE_PTH",
                        {name: hashlib.sha256(body).hexdigest()})
    d = _sitedir(tmp_path, name, body)
    r = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert r.pinned is True, r.detail
    assert r.executable_pth == (name,)


def test_F02_an_unlisted_executable_pth_still_refuses(tmp_path):
    d = _sitedir(tmp_path, "attacker.pth", b"import evil\n")
    r = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert r.pinned is False and "unexpected executable .pth" in r.detail


def test_F02_a_data_only_pth_is_listed_but_not_refused(tmp_path):
    """Unchanged from round one, asserted so the byte pin did not widen into
    refusing bare path lines, which cannot execute."""
    d = _sitedir(tmp_path, "paths.pth", b"/some/dir\n")
    r = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert r.pinned is True and r.executable_pth == ()


def test_F02_an_absent_pinned_file_is_not_a_problem(tmp_path):
    """Nothing executes, so nothing is wrong. The pin is a ceiling on what
    may run, not a requirement that it run."""
    d = tmp_path / "empty-site"
    d.mkdir()
    r = ei.startup_report(sitedirs=[str(d)], find_spec=lambda n: None)
    assert r.pinned is True and r.executable_pth == ()


def test_F02_the_pin_matches_this_machines_real_startup_surface():
    """A wrong digest would refuse every governed run. Measured against the
    live site directories, so a committed typo fails here and not at a seam."""
    live = ei.startup_report()
    assert live.pinned is True, live.detail
    assert set(live.executable_pth) <= set(ei.EXPECTED_EXECUTABLE_PTH)
    for name, want in ei.EXPECTED_EXECUTABLE_PTH.items():
        assert len(want) == 64 and want == want.lower()


# ===========================================================================
# F03 — manifest authority belongs to the directory, not the caller
# ===========================================================================

def _job(tmp_path, *, official=None, local=None):
    d = tmp_path / "job"
    d.mkdir(parents=True, exist_ok=True)
    if official is not None:
        (d / "manifest.json").write_text(json.dumps(official), encoding="utf-8")
    if local is not None:
        (d / "_local_manifest.json").write_text(json.dumps(local),
                                                encoding="utf-8")
    return d


OFFICIAL = {"job_id": "j", "files": [
    {"filename": "official.dbn.zst", "hash": "sha256:" + "a" * 64}]}
LOCAL_WITH_EXTRA = {"files": {"official.dbn.zst": {"sha256": "a" * 64},
                             "replacement.dbn.zst": {"sha256": "b" * 64}}}


def test_F03_ASTRA_case_A_a_local_manifest_beside_an_official_one_refuses(
        tmp_path):
    """ASTRA'S REMAINING COUNTEREXAMPLE, case A. Reproduced on the repaired
    tree: the official manifest listed `official.dbn.zst` alone and the
    PRODUCTION SELECTOR returned `replacement.dbn.zst`, because four call
    sites still read the local-preferring entry."""
    d = _job(tmp_path, official=OFFICIAL, local=LOCAL_WITH_EXTRA)
    with pytest.raises(M.ManifestError) as caught:
        M.load_manifest(d)
    assert "never an override" in str(caught.value)


def test_F03_case_B_the_production_selector_returns_only_authorized_files(
        tmp_path):
    """The selector `load_bars_by_date` feeds, which documented "only files
    the AUTHORIZED manifest lists are read" while a planted manifest could
    add one."""
    d = _job(tmp_path, official=OFFICIAL, local=LOCAL_WITH_EXTRA)
    # The selector names the AUTHORIZED entry, so the planted local manifest
    # is not merely outranked -- it is not consulted at all, and the file it
    # tried to introduce never reaches the loader.
    assert pi._manifest_data_files(d) == ["official.dbn.zst"]
    assert "replacement.dbn.zst" not in pi._manifest_data_files(d)
    # and the conflicted directory is still REFUSED on the production read
    # path, by the shared entry `dbn_loader.load_real` uses per file.
    with pytest.raises(M.ManifestError) as caught:
        M.load_manifest(d)
    assert "never an override" in str(caught.value)
    clean = _job(tmp_path / "clean", official=OFFICIAL)
    assert pi._manifest_data_files(clean) == ["official.dbn.zst"]


def test_F03_case_C_the_production_caller_inventory_is_complete(tmp_path):
    """AARON'S REQUIREMENT: the inventory, classified, and mechanically
    enforced so a NEW production caller cannot appear unclassified.

    PRODUCTION_AUTHORIZED  names the authorized entry directly.
    SHARED                 serves production AND fixture directories, and is
                           safe because authority is now decided by the
                           DIRECTORY -- one change closed all of these at once,
                           which is the property round one lacked.
    """
    authorized = {
        "src/itsf/mc/production_inputs.py": 2,      # selector + condition.json
    }
    shared = {
        "src/itsf/data/dbn_loader.py": 1,
        "src/itsf/data/cost_calibration_loader.py": 3,
        "scripts/run_data_qa.py": 1,
    }
    found_auth, found_shared = {}, {}
    for root in ("src", "scripts"):
        for path in sorted((REPO / root).rglob("*.py")):
            if path.name == "manifests.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            a = s = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func,
                                                             ast.Attribute):
                    if node.func.attr == "load_authorized_manifest":
                        a += 1
                    elif node.func.attr == "load_manifest":
                        s += 1
            rel = path.relative_to(REPO).as_posix()
            if a:
                found_auth[rel] = a
            if s:
                found_shared[rel] = s
    assert found_auth == authorized, (
        "the set of AUTHORIZED-entry callers changed; classify it")
    assert found_shared == shared, (
        "a production caller of the shared manifest entry appeared or moved; "
        "classify it PRODUCTION_AUTHORIZED or NON_PRODUCTION/FIXTURE")


def test_F03_case_D_a_fixture_directory_still_works(tmp_path):
    """A repair that broke every fabricated fixture would not be a repair.
    Measured before the change: zero `_local_manifest.json` files exist
    anywhere on this machine and every real job dir is official-only, so
    only fixtures are affected and they keep their behaviour."""
    d = _job(tmp_path, local={"files": {"bars.csv": {"sha256": "c" * 64}}})
    assert M.load_manifest(d)["files"]["bars.csv"]["sha256"] == "c" * 64


def test_F03_an_official_only_directory_reads_through_one_parser(tmp_path):
    """`load_manifest` delegates the official shape to the authorized entry,
    so the two cannot drift into two readings of the same bytes."""
    d = _job(tmp_path, official=OFFICIAL)
    assert M.load_manifest(d) == M.load_authorized_manifest(d)


def test_F04_PRESERVED_verification_and_consumption_share_one_payload(tmp_path):
    """F04 IS CLOSED AND MUST STAY CLOSED. `manifests.py` and
    `production_inputs.py` were both touched this round, so its verified
    invariant -- the bytes verified by hash are the bytes consumed -- is
    re-driven here against the adversarial replacement."""
    d = tmp_path / "cond"
    d.mkdir()
    good = b'{"status": "available"}'
    target = d / "condition.json"
    target.write_bytes(good)
    manifest = {"files": {"condition.json": {
        "sha256": hashlib.sha256(good).hexdigest()}}}
    assert M.read_verified_bytes(target, manifest) == good
    target.write_bytes(b'{"status": "degraded"}')
    with pytest.raises(M.ManifestError):
        M.read_verified_bytes(target, manifest)


# ===========================================================================
# F05 — one definition of a run id, and an unrecognized scope REFUSES
# ===========================================================================

def _owner_row(scope, *, token=oc.OWNER_HOLD, seq=90, extra=""):
    return ("| %d | %s | %s | %s | Aaron | [%s] %sreason: stop |"
            % (seq, UTC, token, C40, scope, extra))


BAD_SCOPES = {
    "trailing_hyphen": "MC-DS-S004-",
    "truncated_id": "MC-DS-S00",
    "extra_suffix": "MC-DS-S004X",
    "illegal_prefix": "XX-DS-S004",
}


@pytest.mark.parametrize("label", sorted(BAD_SCOPES))
def test_F05_ASTRA_a_non_canonical_scope_refuses(label):
    """ASTRA'S REMAINING COUNTEREXAMPLE. Reproduced on the repaired tree: each
    of these parsed as ONE legal owner row and then yielded ZERO applicable
    holds against MC-DS-S004 with no refusal. Aaron files a hold, the parser
    accepts it, the run starts anyway. `_SCOPE_RE`'s `[A-Z][A-Z0-9-]*` was a
    third grammar for ids two modules already define exactly."""
    text = LIVE_REGISTRY + _owner_row(BAD_SCOPES[label]) + "\n"
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(text)
    assert caught.value.code == "owner_control_scope_unrecognized"
    # and the refusal reaches the caller that matters
    with pytest.raises(oc.OwnerControlRefusal):
        oc.active_holds(text, RUN_ID)
    with pytest.raises(oc.OwnerControlRefusal):
        oc.assert_no_owner_hold(text, RUN_ID)


@pytest.mark.parametrize("label", sorted(BAD_SCOPES))
def test_F05_a_non_canonical_scope_blocks_p3_and_writes_nothing(
        tmp_path, label):
    """AARON'S REQUIREMENT: malformed -> REFUSE, registry unchanged, no P3."""
    path = tmp_path / (label + "_TRIAL_REGISTRY.md")
    sid = _two_row_ledger(path)
    path.write_bytes(path.read_bytes()
                     + (_owner_row(BAD_SCOPES[label]) + "\n").encode("utf-8"))
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "p3_owner_control_row_unreadable"
    assert path.read_bytes() == before, "the registry was modified"
    assert "SUPPLEMENT_RUN_STARTED" not in path.read_text(encoding="utf-8")


def test_F05_a_malformed_scoped_release_refuses():
    """A release whose scope is non-canonical cannot silently fail to release
    the hold it names."""
    hold = _owner_row(RUN_ID, seq=90)
    rel = _owner_row("MC-DS-S004-", token=oc.OWNER_RELEASE, seq=91,
                     extra="releases_event_sequence: 90; ")
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(LIVE_REGISTRY + hold + "\n" + rel + "\n")
    assert caught.value.code == "owner_control_scope_unrecognized"


def test_F05_THE_POSITIVE_PATH_a_valid_scoped_hold_is_in_force():
    text = LIVE_REGISTRY + _owner_row(RUN_ID) + "\n"
    holds = oc.active_holds(text, RUN_ID)
    assert len(holds) == 1 and holds[0].scope == RUN_ID
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.assert_no_owner_hold(text, RUN_ID)
    assert caught.value.code == "owner_hold_in_force"


def test_F05_THE_POSITIVE_PATH_a_valid_global_hold_is_in_force():
    text = LIVE_REGISTRY + _owner_row(oc.GLOBAL_SCOPE) + "\n"
    assert len(oc.active_holds(text, RUN_ID)) == 1


def test_F05_THE_POSITIVE_PATH_a_valid_matching_release_lifts_it():
    hold = _owner_row(RUN_ID, seq=90)
    rel = _owner_row(RUN_ID, token=oc.OWNER_RELEASE, seq=91,
                     extra="releases_event_sequence: 90; ")
    text = LIVE_REGISTRY + hold + "\n" + rel + "\n"
    assert oc.active_holds(text, RUN_ID) == ()
    oc.assert_no_owner_hold(text, RUN_ID)


def test_F05_both_authoritative_families_are_routed():
    """`active_holds` is called with an MC-R### id from `registry_integrity`
    and a MC-DS-S### id from the runner and the P3 boundary. A validator that
    knew one family would refuse legitimate holds in the other."""
    assert oc.canonical_run_id_family("MC-DS-S004") == "supplement"
    assert oc.canonical_run_id_family("MC-R001") == "mc"
    assert oc.canonical_run_id_family("MC-DS-S004-") is None
    text = LIVE_REGISTRY + _owner_row("MC-R001") + "\n"
    assert len(oc.active_holds(text, "MC-R001")) == 1


def test_F05_the_scope_grammar_is_not_respelled():
    """THE MECHANISM: the families come from the modules that own them, so a
    change to either pattern cannot leave this module disagreeing."""
    from itsf.mc import mc_contract as mcc
    from itsf.mc import supplement_contract as sc
    assert dict(oc.RUN_ID_FAMILIES)["supplement"] is sc.SUPPLEMENT_ID_PATTERN
    assert dict(oc.RUN_ID_FAMILIES)["mc"] is mcc.RUN_ID_RE
    assert "A-Z0-9-" not in oc._SCOPE_RE.pattern, "a third grammar came back"


def test_F05_the_query_side_is_swept_too():
    """Not just the reported instance. Asking about `MC-DS-S004-` would miss a
    real `[MC-DS-S004]` hold exactly as surely as the row defect did."""
    text = LIVE_REGISTRY + _owner_row(RUN_ID) + "\n"
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.active_holds(text, "MC-DS-S004-")
    assert caught.value.code == "owner_control_query_run_id_unrecognized"


# ===========================================================================
# F06 — the lock now has both participants
# ===========================================================================

def test_F06_no_public_writer_takes_its_event_as_a_parameter():
    """The n09 guard's rule, honoured rather than relaxed.

    Its words are "a writer that took the token as a PARAMETER would be a
    general registry writer wearing a narrow name", and the owner append's
    first shape did exactly that. `_append_owner_row` is now private so each
    exported entry names one event. Reshaping the code was the right move;
    relaxing the guard to admit it was not."""
    import inspect
    for fn in (rb.append_owner_hold, rb.append_owner_release,
               rb.append_run_started):
        params = inspect.signature(fn).parameters
        for forbidden in ("event", "token", "event_type", "note", "row"):
            assert forbidden not in params, f"{fn.__name__} takes {forbidden}"
    assert not hasattr(rb, "append_owner_control_row")


def test_F06_ASTRA_owner_control_now_has_a_sanctioned_append(tmp_path):
    """ASTRA'S REMAINING COUNTEREXAMPLE, stated as its premise: the sidecar
    lock protects P3 only if every competing writer respects it, and owner
    control had NO sanctioned append function at all -- so a hold was filed by
    ad hoc file mutation, taking no lock and reading no decided snapshot."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    row = rb.append_owner_hold(
        scope=oc.GLOBAL_SCOPE, reason="stop the run",
        head_commit=C40, utc_stamp=UTC, path=path)
    text = path.read_text(encoding="utf-8")
    assert row in text
    holds = oc.active_holds(text, "MC-DS-S001")
    assert len(holds) == 1 and holds[0].reason == "stop the run"


def test_F06_the_owner_append_uses_the_SAME_serialization_primitive():
    """Not a second mechanism. Both writers take `_AppendLock` and both
    compare against their own decided bytes -- counted on the AST, because a
    docstring claiming it is not the same as code doing it."""
    src = (REPO / "src" / "itsf" / "mc" / "registry_boundary.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    writers = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body = ast.dump(ast.Module(body=node.body, type_ignores=[]))
            if "'write_bytes'" in body:
                writers[node.name] = True
            if "'_compare_and_append'" in body:
                writers.setdefault("_calls:" + node.name, True)
    # UPDATED AT THE PRE-CERT F06 REPAIR: the one physical write moved into
    # `serialized_append`, the boundary a supported writer in ANOTHER module can
    # reach. `_compare_and_append` is now its compare-and-swap caller. Same
    # single write, one function further out -- see
    # tests/test_qros_cf_f06_writer_completeness.py for the cross-module half,
    # which is the property this file cannot see from inside one module.
    physical = {n for n in writers if not n.startswith("_calls:")}
    assert physical == {"_physical_serialized_write"}, (
        "a registry write appeared outside the one serialized primitive: "
        f"{sorted(physical)}")
    callers = {n[len("_calls:"):] for n in writers if n.startswith("_calls:")}
    # OWNER-SEMANTICS REPAIR: `append_run_started` commits through
    # `serialized_start_append`, where the decisive hold decision is taken, so
    # the compare-and-swap's in-module callers are the owner path plus the
    # start entry.
    # MEASURED, not assumed: `serialized_start_append` reaches the physical
    # write through `serialized_append`, not through the compare-and-swap, so
    # the CAS's only remaining in-module caller is the owner path. I asserted
    # the wrong set first and the scan corrected me.
    assert callers == {"_append_owner_row"}, (
        f"the set of serialized appenders changed: {sorted(callers)}")


def test_F06_case_A_a_hold_landing_under_the_decision_refuses_p3(tmp_path,
                                                                 monkeypatch):
    """Legal order 1: the hold wins serialization -> no start is written."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = _two_row_ledger(path)
    original = rb.serialized_start_append
    state = {"fired": False}

    def interleave(target, addition, *, run_id, decided=None):
        # One-shot: the owner append below goes through the same primitive,
        # which is the point of the repair and would otherwise recurse.
        if not state["fired"]:
            state["fired"] = True
            rb.append_owner_hold(
                scope=oc.GLOBAL_SCOPE, reason="stop",
                head_commit=C40, utc_stamp=UTC, path=target)
        return original(target, addition, run_id=run_id, decided=decided)

    # OWNER-SEMANTICS REPAIR: the interleave point moved to the start entry,
    # and the refusal is now the OWNER one rather than the stale-snapshot one.
    # That is the correction: the operator is told an owner stopped them, not
    # that the file happened to move.
    monkeypatch.setattr(rb, "serialized_start_append", interleave)
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "start_refused_owner_hold_in_force"
    text = path.read_text(encoding="utf-8")
    assert "SUPPLEMENT_RUN_STARTED" not in text
    assert "OWNER_HOLD" in text, "the interleaved hold was lost"


def test_F06_case_B_a_p3_landing_under_the_owners_decision_refuses_the_hold(
        tmp_path, monkeypatch):
    """Legal order 2, and the half round one could not express: the owner's
    append is now the one that refuses, so a hold is never applied to a stale
    snapshot. The owner re-reads and re-files."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = _two_row_ledger(path)
    original = rb._compare_and_append
    state = {"fired": False}

    def interleave(target, decided, addition):
        if not state["fired"]:
            state["fired"] = True
            rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC,
                                  path=target)
        return original(target, decided, addition)

    monkeypatch.setattr(rb, "_compare_and_append", interleave)
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_owner_hold(
            scope=oc.GLOBAL_SCOPE, reason="stop",
            head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "p3_registry_changed_under_decision"
    assert "OWNER_HOLD" not in path.read_text(encoding="utf-8")


def test_F06_case_C_the_owner_append_refuses_rather_than_writing_unlocked(
        tmp_path):
    """The lock is load-bearing for BOTH writers, not just P3."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    held = path.with_name(path.name + rb.LOCK_SUFFIX)
    held.write_bytes(b"")
    import itsf.mc.registry_boundary as _rb
    old = _rb.LOCK_TIMEOUT_SECONDS
    try:
        _rb.LOCK_TIMEOUT_SECONDS = 0.05
        with pytest.raises(rb.AppendRefused) as caught:
            rb.append_owner_hold(
                scope=oc.GLOBAL_SCOPE, reason="stop",
                head_commit=C40, utc_stamp=UTC, path=path)
        assert caught.value.code == "p3_append_lock_unavailable"
    finally:
        _rb.LOCK_TIMEOUT_SECONDS = old
        held.unlink()
    assert "OWNER_HOLD" not in path.read_text(encoding="utf-8")


def test_F06_case_D_a_second_owner_append_sees_the_first(tmp_path):
    """Two holds in sequence: the second derives the NEXT sequence rather
    than colliding, and both are readable."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    first = rb.append_owner_hold(
        scope=oc.GLOBAL_SCOPE, reason="one",
        head_commit=C40, utc_stamp=UTC, path=path)
    second = rb.append_owner_hold(
        scope="MC-DS-S001", reason="two",
        head_commit=C40, utc_stamp=UTC, path=path)
    seqs = [int(r.split("|")[1].strip()) for r in (first, second)]
    assert seqs[1] == seqs[0] + 1, f"sequence is not contiguous: {seqs}"
    assert len(oc.active_holds(path.read_text(encoding="utf-8"),
                               "MC-DS-S001")) == 2


def test_F06_case_E_a_release_lifts_the_hold_and_is_verified_after_the_write(
        tmp_path):
    """THE POSITIVE PATH for the release direction, and the post-write check
    that makes it honest: the function asks `owner_control` whether the hold
    is actually gone."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    hold = rb.append_owner_hold(
        scope=oc.GLOBAL_SCOPE, reason="stop",
        head_commit=C40, utc_stamp=UTC, path=path)
    seq = int(hold.split("|")[1].strip())
    rb.append_owner_release(
        scope=oc.GLOBAL_SCOPE, reason="resume",
        head_commit=C40, utc_stamp=UTC, releases_event_sequence=seq, path=path)
    text = path.read_text(encoding="utf-8")
    assert oc.active_holds(text, "MC-DS-S001") == ()
    oc.assert_no_owner_hold(text, "MC-DS-S001")


def test_F06_case_F_a_reason_that_would_forge_a_boundary_refuses(tmp_path):
    """Refused BEFORE the bytes are in the ledger, not discovered by the
    parser afterwards."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    before = path.read_bytes()
    for bad in ("stop | now", "stop; now", "stop\nnow"):
        with pytest.raises(rb.AppendRefused) as caught:
            rb.append_owner_hold(
                scope=oc.GLOBAL_SCOPE, reason=bad,
                head_commit=C40, utc_stamp=UTC, path=path)
        assert caught.value.code == "owner_append_reason_breaks_the_row"
    assert path.read_bytes() == before


def test_F06_case_G_the_owner_append_validates_scope_actor_and_shape(tmp_path):
    """Every refusal is deterministic and nothing is written. The scope check
    is the SAME routing F05 installed -- one definition of a run id."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    before = path.read_bytes()
    cases = [
        (dict(token="OWNER_MAYBE", scope=oc.GLOBAL_SCOPE),
         "owner_append_token_unknown"),
        (dict(scope="MC-DS-S004-"), "owner_append_scope_unrecognized"),
        (dict(head_commit="abc"), "owner_append_commit_not_40hex"),
        (dict(utc_stamp="yesterday"), "owner_append_utc_malformed"),
        (dict(reason="   "), "owner_append_reason_empty"),
        (dict(token=oc.OWNER_RELEASE), "owner_append_release_names_no_hold"),
        (dict(releases_event_sequence=5), "owner_append_hold_names_a_release"),
    ]
    for override, code in cases:
        kw = dict(token=oc.OWNER_HOLD, scope=oc.GLOBAL_SCOPE, reason="stop",
                  head_commit=C40, utc_stamp=UTC, path=path)
        kw.update(override)
        token = kw.pop("token")
        with pytest.raises(rb.AppendRefused) as caught:
            rb._append_owner_row(token, **kw)
        assert caught.value.code == code, f"{override} -> {caught.value.code}"
    assert path.read_bytes() == before


def test_F06_the_owner_append_refuses_on_an_unreadable_ledger(tmp_path):
    """Appending a hold onto a ledger whose existing owner rows cannot be read
    would decide nothing -- F05's refusal reaches this writer too."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    path.write_bytes(path.read_bytes()
                     + (_owner_row("MC-DS-S004-") + "\n").encode("utf-8"))
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_owner_hold(
            scope=oc.GLOBAL_SCOPE, reason="stop",
            head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "owner_append_existing_rows_unreadable"
    assert path.read_bytes() == before


def test_F06_the_sequence_is_derived_not_typed(tmp_path):
    """`SEQUENCE_NAMESPACE=GLOBAL` means the NEXT value. An owner filing a
    hold under pressure is the last person who should hand-type one."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    _two_row_ledger(path)
    rows, refusal = sreg.parse_registry_rows(
        path.read_text(encoding="utf-8"))
    assert refusal is None
    expected = rb._next_global_sequence(rows)
    row = rb.append_owner_hold(
        scope=oc.GLOBAL_SCOPE, reason="stop",
        head_commit=C40, utc_stamp=UTC, path=path)
    assert int(row.split("|")[1].strip()) == expected
    after = sreg.resolve_supplement_chain(
        path.read_text(encoding="utf-8"), "MC-DS-S001")
    assert not getattr(after, "problem", ""), "the owner row broke the chain"


def test_F06_nothing_here_wrote_to_the_real_registry():
    """The guard this file must carry, given what it exercises."""
    assert (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(
        encoding="utf-8") == LIVE_REGISTRY
