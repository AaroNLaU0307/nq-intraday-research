"""The review workspace is a supplied capability, validated and bound.

ONE generic validator for the whole workspace contract. The sealed review object
is told, once, where it may write; it canonicalises what it is told, proves the
base is disjoint in BOTH directions from every governed root, takes exactly one
fresh child, proves that child usable by using it, and binds it to a single
delivery. Every failure below is a REFUSAL, never a warning and never a
fallback.

WHAT THE NEGATIVE TESTS ARE FOR. Discovery was removed because four different
resolutions of "where can I write" each turned out to be a guess: a directory
inside the sealed delivery, `tempfile.gettempdir()` (which consults TMPDIR, TEMP
and TMP -- measured), `GetTempPathW`/`GetTempPath2W` (documented to consult the
same variables), and a known-folder lookup that inferred the answer from profile
structure. So the tests that matter most here assert an ABSENCE: that nothing
selects the workspace except the parameter.

Everything runs in `tmp_path` against a stand-in manifest. No real bundle, no
real runtime, no reviewer artifact and no host temporary directory is touched.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import review_output as ro                                  # noqa: E402
import code_review_bundle_guard as guard_mod                # noqa: E402

REVIEW_ID = "N14-BUNDLE-TEST"
MANIFEST = "ab" * 32
RUNTIME = "cd" * 32
ROUND = "2 of 2"
RUNTIME_ID = "N14-RUNTIME-TEST"


def _binding(**over):
    b = {"review_id": REVIEW_ID, "manifest_sha256": MANIFEST,
         "runtime_manifest_sha256": RUNTIME, "substantive_round": ROUND}
    b.update(over)
    return b


@pytest.fixture
def bundle(tmp_path):
    """A stand-in sealed delivery: a MANIFEST.json in a delivery directory.

    The manifest is written so that its SHA256 is what the binding carries,
    exactly as the real runner derives it -- the digest is not asserted, it is
    computed, so these tests cannot drift from the sealed bytes.
    """
    root = tmp_path / "deliveries" / REVIEW_ID
    root.mkdir(parents=True)
    (root / "MANIFEST.json").write_text(json.dumps({
        "review_id": REVIEW_ID,
        "substantive_round": ROUND,
        "review_runtime": {"runtime_id": RUNTIME_ID,
                           "runtime_manifest_sha256": RUNTIME},
        "write_surfaces": {"forbidden_workspace_roots": {
            str(tmp_path / "repo"): "the live repository workspace",
            str(tmp_path / "quant-data"): "the research-data roots",
        }},
    }, indent=2), encoding="utf-8")
    for rel in ("repo", "quant-data", "deliveries/" + RUNTIME_ID):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def base(tmp_path):
    """A stand-in dispatcher-supplied workspace base, disjoint from all of it."""
    b = tmp_path / "supplied-base"
    b.mkdir()
    return b


def _digest(bundle):
    return ro._manifest_with_digest(bundle)["__manifest_sha256__"]


# == 1. the parameter ======================================================

def test_1_a_missing_workspace_parameter_is_refused(bundle, base):
    """The load-bearing absence. No parameter, no workspace, no review -- and
    in particular no quiet fallback to a directory the runner picked."""
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.parse_workspace_base([])
    assert "does not discover" in str(ei.value)
    assert ro.PARAMETER in str(ei.value)


def test_1_the_parameter_is_accepted_in_both_spellings():
    for argv in ([ro.PARAMETER, "C:/x"], [ro.PARAMETER + "=C:/x"]):
        assert ro.parse_workspace_base(argv) == "C:/x"


@pytest.mark.parametrize("argv,why", [
    ([ro.PARAMETER], "no value"),
    ([ro.PARAMETER, ""], "empty"),
    ([ro.PARAMETER, "a", ro.PARAMETER, "b"], "2 times"),
    (["--somewhere-else", "a"], "unrecognised"),
])
def test_1_an_ambiguous_or_unknown_launch_argument_is_refused(argv, why):
    """Two bases would make the authorised one ambiguous; an unknown argument
    silently ignored is how a typo becomes a different workspace."""
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.parse_workspace_base(argv)
    assert why in str(ei.value)


def _code_only(path: Path) -> str:
    """Source with comments and string literals removed.

    The resolver's own prose NAMES the APIs it no longer uses, and has to: the
    reason discovery is gone is the point of the file. So the scan below reads
    executable tokens only -- otherwise the documentation would trip the test
    that exists to police the code.
    """
    import io
    import tokenize
    kept = []
    with open(path, "rb") as fh:
        for tok in tokenize.tokenize(io.BufferedReader(fh).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            kept.append(tok.string)
    return " ".join(kept)


def test_1_nothing_in_the_resolver_reads_the_environment():
    """The property the last three corrections were about, asserted against the
    SOURCE rather than behaviour, because the defect each time was a channel
    nobody noticed rather than a wrong answer."""
    code = _code_only(SCRIPTS / "review_output.py")
    for banned in ("environ", "getenv", "gettempdir", "GetTempPath",
                   "SHGetKnownFolderPath", "FOLDERID", "expandvars",
                   "TMPDIR", "TEMP"):
        assert banned not in code, (
            "%s reintroduces host discovery into the workspace resolver; the "
            "base is supplied, never found" % banned)


# == 2-5. canonical disjointness, both directions ==========================

def test_2_a_base_inside_the_sealed_delivery_is_refused(bundle):
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, bundle / "inside")
    assert "INSIDE" in str(ei.value) or "not an existing directory" in str(ei.value)


def test_2_a_base_that_IS_the_sealed_delivery_is_refused(bundle):
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, bundle)
    assert "INSIDE" in str(ei.value)


def test_3_a_base_that_CONTAINS_the_sealed_delivery_is_refused(bundle):
    """The other direction, and the one a single containment check misses: a
    base enclosing the delivery would put sealed input inside the writable
    surface."""
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, bundle.parent.parent)
    assert "CONTAINS" in str(ei.value)


def test_4_a_base_overlapping_the_portable_runtime_is_refused(bundle, tmp_path):
    runtime = tmp_path / "deliveries" / RUNTIME_ID
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, runtime)
    assert "INSIDE" in str(ei.value)
    assert RUNTIME_ID in str(ei.value)


@pytest.mark.parametrize("rel,label", [
    ("repo", "the live repository workspace"),
    ("quant-data", "the research-data roots"),
    ("deliveries", "the review-delivery directory"),
])
def test_5_a_base_overlapping_a_governed_root_is_refused(bundle, tmp_path,
                                                         rel, label):
    """Declared roots and derived roots are checked the same way. The repository
    and the data roots must be DECLARED -- a sealed object cannot derive them
    from its own location -- while the delivery directory is derived, so it
    stays correct if the delivery moves."""
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, tmp_path / rel)
    assert label in str(ei.value)


def test_5_a_sibling_that_merely_shares_a_PREFIX_is_not_overlapping(bundle,
                                                                    tmp_path):
    """Component-safe containment, stated as the case that a string comparison
    gets wrong: `quant-data-2` is not inside `quant-data`."""
    sibling = tmp_path / "quant-data-2"
    sibling.mkdir()
    assert ro.prepare(bundle, sibling).is_dir()


def test_5_containment_is_case_insensitive(tmp_path):
    """On a filesystem that does not care about case, a comparison that does
    would let `C:\\USERS\\...` past a check on `C:\\Users\\...`."""
    assert ro.contains_or_equals(Path(r"C:\Governed"), Path(r"C:\GOVERNED\x"))
    assert not ro.contains_or_equals(Path(r"C:\Governed"),
                                     Path(r"C:\Governed-2\x"))


def test_5_a_base_that_resolves_INTO_a_governed_root_is_refused(bundle,
                                                                tmp_path):
    """Canonicalisation before comparison. A link is judged by where it points,
    which is the same reason the execution guard resolves before it compares.
    Skipped where this seat cannot create one -- the property is asserted on
    the seats that can, and never silently assumed on those that cannot."""
    link = tmp_path / "looks-harmless"
    target = tmp_path / "quant-data"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        # A symlink needs a privilege an ordinary Windows seat does not have;
        # a JUNCTION does not, and is the form this project has actually hit.
        import subprocess
        rc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link),
                             str(target)], capture_output=True)
        if rc.returncode or not link.exists():
            pytest.skip("no link creation on this seat: %s"
                        % rc.stderr.decode("utf-8", "replace").strip())
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, link)
    assert "research-data" in str(ei.value)


def test_5_a_base_that_does_not_exist_is_refused(bundle, tmp_path):
    """The dispatcher supplies a base it has authorised and that exists. This
    runner creates only its own child, never the base."""
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, tmp_path / "never-created")
    assert "not an existing directory" in str(ei.value)


# == 6. exactly one fresh child ============================================

def test_6_a_pre_existing_child_is_refused_and_left_untouched(bundle, base):
    """Refusing is not cleaning up. An empty directory is not evidence that it
    is unused -- another run may be in progress -- and deleting another
    attempt's work to make room is worse than stopping."""
    child = ro.child_for(base, REVIEW_ID, _digest(bundle))
    child.mkdir(parents=True)
    (child / "INITIAL_FINDINGS.md").write_text("someone else's", encoding="utf-8")
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, base)
    assert "ALREADY EXISTS" in str(ei.value)
    assert (child / "INITIAL_FINDINGS.md").read_text(encoding="utf-8") \
        == "someone else's"


def test_6_an_EMPTY_pre_existing_child_is_refused_too(bundle, base):
    """The case the previous contract allowed, and the reason it no longer
    does: an empty root is exactly what a crashed or concurrent run leaves."""
    ro.child_for(base, REVIEW_ID, _digest(bundle)).mkdir(parents=True)
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prepare(bundle, base)
    assert "empty or not" in str(ei.value)


def test_6_the_child_is_named_for_the_delivery_and_two_never_collide(base):
    a = ro.child_for(base, REVIEW_ID, MANIFEST)
    assert a.parent.name == ro.NAMESPACE
    assert a.name == "%s-%s" % (REVIEW_ID, MANIFEST[:12])
    others = {ro.child_for(base, REVIEW_ID, "ef" * 32),
              ro.child_for(base, "N14-BUNDLE-OTHER", MANIFEST)}
    assert a not in others and len(others) == 2


def test_6_a_child_without_an_identity_is_refused(base):
    for rid, man in ((None, MANIFEST), ("", MANIFEST), (REVIEW_ID, "")):
        with pytest.raises(ro.OutputRootRefused):
            ro.child_for(base, rid, man)


def test_6_establishing_the_workspace_never_enumerates_the_base(bundle, base):
    """The supplied base was authority to CREATE one directory, not a licence
    to read the seat's other work. Enforced by making enumeration fail: if any
    step listed a directory, this test would raise instead of passing.

    Restored in a `finally` rather than by `monkeypatch`, because these three
    are process-wide and the fixture teardown that would undo them runs after
    other teardown that legitimately enumerates directories.
    """
    def refuse(*a, **k):
        raise AssertionError("the workspace base was enumerated")

    saved = (os.listdir, os.scandir, Path.iterdir)
    os.listdir, os.scandir, Path.iterdir = refuse, refuse, refuse
    try:
        child = ro.prepare(bundle, base)
    finally:
        os.listdir, os.scandir, Path.iterdir = saved
    assert child.is_dir()


# == 7. the capability is proved by exercising it ==========================

def test_7_create_write_rename_delete_are_performed_not_inferred(tmp_path):
    child = tmp_path / "fresh"
    child.mkdir()
    assert ro.prove_capability(child) == ["CREATE", "WRITE", "RENAME", "DELETE"]


def test_7_the_proof_leaves_no_residue(bundle, base):
    """The child a reviewer receives holds its binding and its scratch
    directory and nothing else -- the probe cleans up after itself, which is
    also what keeps the 'must not already exist' rule meaningful."""
    child = ro.prepare(bundle, base)
    assert sorted(p.name for p in child.iterdir()) == [ro.SCRATCH_NAME,
                                                       ro.BINDING_FILE]


def test_7_a_workspace_that_cannot_be_written_is_a_refusal(tmp_path,
                                                           monkeypatch):
    """Capability comes from the operation succeeding, never from an ACL: three
    deliveries carried a surface whose permissions said writable and whose
    restricted token said otherwise."""
    child = tmp_path / "looks-fine"
    child.mkdir()

    def deny(self, *a, **k):
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr(Path, "write_text", deny)
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.prove_capability(child)
    assert "failed the capability proof after ['CREATE']" in str(ei.value)


# == 8. after the freeze, the guard admits the child and nothing else ======

@pytest.fixture
def armed(tmp_path, bundle, base):
    """A guard constructed exactly as the runner constructs it, but NOT
    installed: an audit hook cannot be removed once added, so installing one
    here would outlive the test and judge the rest of the session."""
    child = ro.prepare(bundle, base)
    g = guard_mod.Guard(bundle, child, runtime_roots=(tmp_path / "no-runtime",),
                        writable_root=child)
    return g, child


def test_8_a_write_inside_the_frozen_child_is_admitted(armed):
    g, child = armed
    g("os.mkdir", (str(child / "sub"),))
    g("open", (str(child / "INITIAL_FINDINGS.md"), "w"))
    assert g.denials == []


@pytest.mark.parametrize("where", ["bundle", "base", "sibling"])
def test_8_a_write_outside_the_frozen_child_is_denied(armed, bundle, base,
                                                      where):
    """Including under the supplied BASE itself. The base was never admitted:
    it is where the child was allowed to be created, not a writable region."""
    g, child = armed
    target = {"bundle": bundle / "MANIFEST.json",
              "base": base / "notes.txt",
              "sibling": child.parent / "another-delivery"}[where]
    with pytest.raises(guard_mod.BundleEscapeDenied):
        g("open", (str(target), "w"))
    assert g.denials


def test_8_the_base_is_not_a_read_or_listing_root(armed, base):
    """No arbitrary sibling enumeration. A listing of the base is denied like
    any other read outside the boundary."""
    g, _ = armed
    with pytest.raises(guard_mod.BundleEscapeDenied):
        g("os.listdir", (str(base),))
    with pytest.raises(guard_mod.BundleEscapeDenied):
        g("open", (str(base / "someone-elses-notes.txt"), "r"))


# == 9. the environment has no say =========================================

def test_9_hostile_tmp_temp_and_tmpdir_do_not_move_the_workspace(
        bundle, base, tmp_path, monkeypatch):
    """The property, and the CONTROL that makes it mean something.

    An earlier version resolved the workspace through `tempfile.gettempdir()`,
    which consults TMPDIR, then TEMP, then TMP. Measured with those three
    pointed at a directory of one's choosing, the output root followed them
    there. The control matters as much as the assertion: the same hostile
    values are shown to actually move `tempfile.gettempdir()`. Without it this
    test would pass just as happily if the variables were never effective.
    """
    hostile = tmp_path / "hostile-but-writable"
    hostile.mkdir()
    for var in ("TMP", "TEMP", "TMPDIR"):
        monkeypatch.setenv(var, str(hostile))

    # CONTROL: an environment-directed resolver really does move.
    import importlib
    import tempfile as _tf
    monkeypatch.setattr(_tf, "tempdir", None)
    importlib.reload(_tf)
    assert Path(_tf.gettempdir()).resolve() == hostile.resolve(), (
        "the hostile values did not take effect, so this test would prove "
        "nothing about the resolver under test")

    # THE PROPERTY: the supplied base decides, and nothing else does.
    child = ro.prepare(bundle, base)
    assert base.resolve() in child.parents
    assert hostile.resolve() not in child.parents
    assert not (hostile / ro.NAMESPACE).exists()


def test_9_setting_tmp_afterwards_is_routing_not_authority(bundle, base,
                                                            monkeypatch):
    """W7, stated as an ORDER. The runner sets TMP, TEMP and TMPDIR to the
    validated child so incidental temporary writes land inside the boundary.
    That happens after the child is frozen and changes nothing about which
    child was chosen -- proved here by choosing one, then pointing all three at
    it, then choosing again from the same parameter."""
    first = ro.prepare(bundle, base)
    for var in ("TMP", "TEMP", "TMPDIR"):
        monkeypatch.setenv(var, str(first / ro.SCRATCH_NAME))
    assert ro.child_for(base, REVIEW_ID, _digest(bundle)) == first


# == 10-13. the binding, one delivery each =================================

def test_10_13_the_binding_is_read_off_the_sealed_manifest(bundle):
    manifest = ro._manifest_with_digest(bundle)
    assert ro.binding_for(manifest) == _binding(
        manifest_sha256=manifest["__manifest_sha256__"])


@pytest.mark.parametrize("field,wrong", [
    ("review_id", "N14-BUNDLE-SOMETHING-ELSE"),         # 10
    ("manifest_sha256", "ff" * 32),                     # 11
    ("runtime_manifest_sha256", "ff" * 32),             # 12
    ("substantive_round", "1 of 2"),                    # 13
])
def test_10_13_a_workspace_bound_to_another_review_object_is_refused(
        bundle, base, field, wrong):
    """Each bound field on its own is enough to refuse. A wrong manifest or a
    wrong runtime digest means the artifacts describe different bytes than the
    ones in front of you; a wrong round means they answer a different
    question."""
    child = ro.prepare(bundle, base)
    expected = ro.binding_for(ro._manifest_with_digest(bundle))
    ro.write_binding(child, dict(expected, **{field: wrong}))
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.check_binding(child, expected)
    assert field in str(ei.value)
    assert "DIFFERENT review object" in str(ei.value)


def test_10_13_a_matching_binding_is_accepted(bundle, base):
    child = ro.prepare(bundle, base)
    expected = ro.binding_for(ro._manifest_with_digest(bundle))
    assert ro.check_binding(child, expected)["review_id"] == REVIEW_ID


def test_10_13_a_binding_missing_any_field_is_refused(tmp_path):
    for field in ro.BINDING_FIELDS:
        with pytest.raises(ro.OutputRootRefused) as ei:
            ro.write_binding(tmp_path, _binding(**{field: ""}))
        assert field in str(ei.value)


def test_10_13_a_workspace_with_no_binding_or_an_unreadable_one_is_refused(
        bundle, base):
    child = ro.prepare(bundle, base)
    (child / ro.BINDING_FILE).unlink()
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.check_binding(child, _binding())
    assert ro.BINDING_FILE in str(ei.value)
    (child / ro.BINDING_FILE).write_text("{ not json", encoding="utf-8")
    with pytest.raises(ro.OutputRootRefused):
        ro.check_binding(child, _binding())


def test_10_13_the_path_is_provenance_and_not_review_identity(bundle, tmp_path):
    """Two seats may run the same delivery at different absolute paths and
    review the same bytes, so the path is deliberately not a bound field."""
    assert "path" not in " ".join(ro.BINDING_FIELDS)
    one, two = tmp_path / "seat-one", tmp_path / "seat-two"
    one.mkdir()
    two.mkdir()
    a, b = ro.prepare(bundle, one), ro.prepare(bundle, two)
    assert a != b
    assert json.loads((a / ro.BINDING_FILE).read_text(encoding="utf-8")) \
        == json.loads((b / ro.BINDING_FILE).read_text(encoding="utf-8"))


def test_the_retained_returns_are_named_and_are_not_scratch():
    """The three returns are declared so the runner can assert they never end
    up inside the ephemeral directory."""
    assert ro.RETAINED_ARTIFACTS == ("INITIAL_FINDINGS.md", "FREEZE.json",
                                     "ATTESTATION.md")
    assert ro.SCRATCH_NAME.startswith(".")
    assert ro.SCRATCH_NAME not in ro.RETAINED_ARTIFACTS
