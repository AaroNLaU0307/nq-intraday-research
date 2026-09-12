"""The real-MC authorization boundary, as behaviour.

The gate used to be an unconditional refusal: `authorize_real_mc` raised on
every call, so nothing below it could be reached and nothing below it could
be checked either. It now VALIDATES the Owner's authorization against the
run it is about to start, and still refuses by default.

Every test here asserts a FINAL OBSERVABLE -- the refusal a caller gets, or
the mapping the gate returns. No real MC is executed, no `.dbn.zst` is
opened, no protected Development outcome is read, and no run output, registry
row or exposure row is created: the authorization fixture is written into
`tmp_path` and the gate is pointed at it.
"""
import json

import pytest

from itsf.mc import consumer as mcc
from itsf.s0.handoff import McConsumerAbsent

RUN_ID = "MC-R001"
COMMIT = "a" * 40
SUPPLEMENT = "b" * 64


def _authorization(**over):
    row = {
        "run_id": RUN_ID,
        "authorized_commit": COMMIT,
        "sealed_supplement_sha256": SUPPLEMENT,
        "prereg_sha256": mcc._prereg_sha256(),
        "authorized_by": mcc.MC_AUTHORIZATION_ACTOR,
        "sentence": mcc.MC_AUTHORIZATION_SENTENCE.format(
            run_id=RUN_ID, commit=COMMIT),
    }
    row.update(over)
    return row


def _write(tmp_path, row, name="MC_RUN_AUTHORIZATION.json"):
    """Write the fixture where the gate will look, and return its rel path.

    `authorize_real_mc` resolves `path` against the repository root, so the
    fixture is placed under a directory the test owns and addressed
    relatively from there.
    """
    import itsf.mc.consumer as _c
    from pathlib import Path
    repo = Path(_c.__file__).resolve().parents[3]
    rel = tmp_path.relative_to(repo) if str(tmp_path).startswith(str(repo)) \
        else None
    if rel is None:                       # tmp_path is outside the repo
        pytest.skip("tmp_path is not under the repository root")
    target = tmp_path / name
    target.write_text(json.dumps(row), encoding="utf-8")
    return str(rel / name).replace("\\", "/")


@pytest.fixture()
def authorized(tmp_path_factory, request):
    """A well-formed authorization on disk, inside the repository tree."""
    from pathlib import Path
    import itsf.mc.consumer as _c
    repo = Path(_c.__file__).resolve().parents[3]
    d = repo / ".pytest-mc-auth" / request.node.name
    d.mkdir(parents=True, exist_ok=True)
    yield d
    for p in sorted(d.rglob("*"), reverse=True):
        p.unlink() if p.is_file() else p.rmdir()
    d.rmdir()
    try:                      # and the shared root, once the last test leaves
        d.parent.rmdir()
    except OSError:
        pass


# == 1. no authorization -> the real entrypoint refuses, and refuses first ==

def test_without_authorization_the_gate_refuses():
    with pytest.raises(McConsumerAbsent, match="NOT authorized"):
        mcc.authorize_real_mc(
            "", run_id=RUN_ID, authorized_commit=COMMIT,
            sealed_supplement_sha256=SUPPLEMENT,
            path="ops/NO_SUCH_AUTHORIZATION.json")


def test_the_historical_one_argument_call_still_refuses():
    """A caller that shows the gate nothing cannot be authorized by it."""
    with pytest.raises(McConsumerAbsent, match="NOT authorized"):
        mcc.authorize_real_mc("")
    with pytest.raises(McConsumerAbsent, match="refusal stands"):
        mcc.authorize_real_mc("**MC_RUN_AUTHORIZED**")


def test_the_production_entrypoint_refuses_before_reading_anything(
        monkeypatch):
    """THE property that makes an unauthorized call free: nothing is read.

    TWO refusals guard this entry and either is a correct outcome. Outside
    the trusted launch boundary `assert_real_run_allowed` fires first --
    which is where these tests run, so that is what is normally observed.
    Inside it, the Owner-authorization gate fires. What the test pins is
    that neither the bundle nor the prepared-input battery is reached,
    whichever refusal arrives.
    """
    import scripts.mc_real_run as entry
    from itsf.guards import RunBlockedError

    opened = []

    def explode(*_a, **_kw):
        opened.append("read")
        raise AssertionError("data was read before the entry refused")

    import itsf.mc.bundle_precheck as bp
    monkeypatch.setattr(bp, "precheck_bundle_on_disk", explode)
    monkeypatch.setattr(mcc, "prepare_mc_input", explode)

    with pytest.raises((McConsumerAbsent, RunBlockedError)):
        entry.main(bundle_root=str(entry.REPO))
    assert opened == [], "something was read before the entry refused"


def test_the_entrypoint_binds_the_trusted_launch_gate():
    """It is a sanctioned real-run entry, so it reaches
    `assert_real_run_allowed` with the production defaults -- the same
    binding every other sanctioned entry has."""
    import inspect
    import scripts.mc_real_run as entry
    body = inspect.getsource(entry.main)
    assert "assert_real_run_allowed()" in body
    assert body.index("assert_real_run_allowed()") < body.index(
        "precheck_bundle_on_disk")


def test_the_entrypoint_refuses_without_a_bundle_root():
    """No pinned governed bundle root exists, and the entrypoint does not
    invent one."""
    import scripts.mc_real_run as entry
    assert entry.main() == 2


# == 2. malformed / wrong run identity ====================================

def test_a_different_run_id_refuses(authorized):
    rel = _write(authorized, _authorization())
    with pytest.raises(McConsumerAbsent, match="run id"):
        mcc.authorize_real_mc("", run_id="MC-R999",
                              authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_a_non_hex_commit_refuses(authorized):
    rel = _write(authorized, _authorization(authorized_commit="not-40-hex"))
    with pytest.raises(McConsumerAbsent, match="40-character"):
        mcc.authorize_real_mc("", run_id=RUN_ID,
                              authorized_commit="not-40-hex",
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_a_non_owner_actor_refuses(authorized):
    rel = _write(authorized, _authorization(authorized_by="main agent"))
    with pytest.raises(McConsumerAbsent, match="only Aaron"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_malformed_json_refuses(authorized):
    target = authorized / "MC_RUN_AUTHORIZATION.json"
    target.write_text("{not json", encoding="utf-8")
    from pathlib import Path
    import itsf.mc.consumer as _c
    repo = Path(_c.__file__).resolve().parents[3]
    rel = str(target.relative_to(repo)).replace("\\", "/")
    with pytest.raises(McConsumerAbsent, match="does not parse"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_a_missing_field_refuses(authorized):
    row = _authorization()
    del row["sealed_supplement_sha256"]
    rel = _write(authorized, row)
    with pytest.raises(McConsumerAbsent, match="missing"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


# == 3. wrong code / supplement / prereg binding ==========================

def test_a_different_commit_refuses(authorized):
    rel = _write(authorized, _authorization())
    with pytest.raises(McConsumerAbsent, match="prepared input is bound"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit="c" * 40,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_a_different_supplement_refuses(authorized):
    rel = _write(authorized, _authorization())
    with pytest.raises(McConsumerAbsent, match="sealed supplement"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256="d" * 64, path=rel)


def test_a_stale_preregistration_refuses(authorized):
    """An authorization cannot outlive the research design it was for."""
    rel = _write(authorized, _authorization(prereg_sha256="e" * 64))
    with pytest.raises(McConsumerAbsent, match="preregistration"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_a_transported_sentence_is_never_trusted(authorized):
    """The sentence is rebuilt from the run id and the commit; a row that
    merely SAYS it is authorized does not authorize."""
    rel = _write(authorized, _authorization(sentence="启动第一次真实MC，授权"))
    with pytest.raises(McConsumerAbsent, match="rebuilt"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


def test_a_sentence_for_another_commit_refuses(authorized):
    """The commit cell and the sentence must agree with each other."""
    rel = _write(authorized, _authorization(
        sentence=mcc.MC_AUTHORIZATION_SENTENCE.format(
            run_id=RUN_ID, commit="f" * 40)))
    with pytest.raises(McConsumerAbsent, match="rebuilt"):
        mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                              sealed_supplement_sha256=SUPPLEMENT, path=rel)


# == 4. a correct authorization reaches the post-gate boundary ============

def test_a_correct_authorization_is_accepted_and_returned(authorized):
    """The gate's positive path, with NO real run: it returns the validated
    authorization and the caller goes no further here."""
    rel = _write(authorized, _authorization())
    got = mcc.authorize_real_mc("", run_id=RUN_ID, authorized_commit=COMMIT,
                                sealed_supplement_sha256=SUPPLEMENT, path=rel)
    assert got["run_id"] == RUN_ID
    assert got["authorized_commit"] == COMMIT
    assert got["authorized_by"] == mcc.MC_AUTHORIZATION_ACTOR
    assert got["sentence"] == mcc.MC_AUTHORIZATION_SENTENCE.format(
        run_id=RUN_ID, commit=COMMIT)
    with pytest.raises(TypeError):                   # returned read-only
        got["run_id"] = "MC-R999"


def test_the_synthetic_entry_is_unaffected_by_the_gate():
    """`execute_full_mc_for_tests` takes a bound authorization and never
    calls the Owner gate, so the test path cannot be mistaken for the real
    one in either direction."""
    import inspect
    from itsf.mc import mc_runner as run
    body = inspect.getsource(run.execute_full_mc_for_tests)
    assert "authorize_real_mc" not in body
    assert "authorize_real_mc" in inspect.getsource(run.execute_full_mc)


# == 5. nothing real was created ==========================================

def test_no_real_mc_artifact_is_created_by_this_module():
    """The whole file runs against fixtures: the gate reads a JSON file and
    returns or raises. Pinned so a future edit cannot quietly add a run."""
    import inspect
    import scripts.mc_real_run as entry
    src = inspect.getsource(mcc.authorize_real_mc)
    for banned in ("execute_full_mc", "run_epistemic", "load_bars",
                   "open(", "mkdir", "write_text", "write_bytes"):
        assert banned not in src, banned
    # and the entrypoint asks the gate before it touches a byte
    body = inspect.getsource(entry.main)
    assert body.index("authorize_real_mc") < body.index(
        "precheck_bundle_on_disk")
    assert body.index("authorize_real_mc") < body.index("prepare_mc_input")
