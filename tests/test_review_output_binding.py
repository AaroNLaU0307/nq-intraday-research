"""The review output root is bound to exactly one delivery.

Reviewer artifacts no longer live inside the sealed bundle -- a review seat
running under a restricted token cannot write there whatever the permissions
say -- so they live in a seat-native directory outside it. That moves one risk
in: two deliveries, or two attempts at one delivery, could put artifacts in the
same place and become indistinguishable.

The binding closes that. The root's NAME carries the review id and a prefix of
the manifest digest, and the root holds an `OUTPUT_BINDING.json` naming the
review id, the manifest digest, the runtime digest and the round. Every
mismatch below is a REFUSAL, not a warning, and a pre-existing non-empty root
is never reused.

Everything here runs in `tmp_path`. No real bundle, no real temp base, no
reviewer artifact is touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import review_output as ro                                  # noqa: E402

REVIEW_ID = "N14-BUNDLE-TEST"
MANIFEST = "ab" * 32
RUNTIME = "cd" * 32


def _binding(**over):
    b = {"review_id": REVIEW_ID, "manifest_sha256": MANIFEST,
         "runtime_manifest_sha256": RUNTIME, "substantive_round": "2 of 2"}
    b.update(over)
    return b


@pytest.fixture
def bundle(tmp_path):
    """A stand-in sealed bundle. Only its path matters to these tests."""
    root = tmp_path / "bundle"
    root.mkdir()
    return root


@pytest.fixture
def base(tmp_path):
    """A stand-in seat temp base, so nothing touches the real one."""
    b = tmp_path / "seat-temp"
    b.mkdir()
    return b


# ---------------------------------------------------------------- resolution

def test_the_root_is_derived_from_the_review_id_and_the_manifest(base):
    root = ro.output_root_for(REVIEW_ID, MANIFEST, base=base)
    assert root.parent.name == ro.NAMESPACE
    assert root.name == "%s-%s" % (REVIEW_ID, MANIFEST[:12])
    assert base in root.parents
    # Deterministic: the launcher and the runner must derive the same path.
    assert root == ro.output_root_for(REVIEW_ID, MANIFEST, base=base)


def test_two_deliveries_never_share_a_root(base):
    a = ro.output_root_for(REVIEW_ID, MANIFEST, base=base)
    b = ro.output_root_for(REVIEW_ID, "ef" * 32, base=base)
    c = ro.output_root_for("N14-BUNDLE-OTHER", MANIFEST, base=base)
    assert len({a, b, c}) == 3


def test_a_root_without_an_identity_is_refused(base):
    for rid, man in ((None, MANIFEST), ("", MANIFEST), (REVIEW_ID, "")):
        with pytest.raises(ro.OutputRootRefused):
            ro.output_root_for(rid, man, base=base)


# ------------------------------------------------------------- creation rules

def test_creation_proves_the_capability_by_exercising_it(bundle, base):
    root = ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    assert root.is_dir()
    # The probe cleans up after itself; a root that kept residue would make
    # the "new and empty" rule below meaningless on the next attempt.
    assert sorted(p.name for p in root.iterdir()) == []


def test_a_pre_existing_non_empty_root_is_never_reused(bundle, base):
    root = ro.output_root_for(REVIEW_ID, MANIFEST, base=base)
    root.mkdir(parents=True)
    (root / "INITIAL_FINDINGS.md").write_text("stale", encoding="utf-8")
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    assert "NOT empty" in str(ei.value)
    # And it is left exactly as it was -- refusing is not cleaning up.
    assert (root / "INITIAL_FINDINGS.md").read_text(encoding="utf-8") == "stale"


def test_an_empty_pre_existing_root_is_acceptable(bundle, base):
    root = ro.output_root_for(REVIEW_ID, MANIFEST, base=base)
    root.mkdir(parents=True)
    assert ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base) == root


def test_a_root_inside_the_sealed_bundle_is_refused(bundle):
    """The whole point of the move. If the derived root ever landed inside the
    delivery, the bundle would stop being immutable to review execution."""
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=bundle)
    assert "inside" in str(ei.value) or "does not lie under" in str(ei.value)


def test_a_root_that_would_contain_a_sealed_input_is_refused(bundle, base):
    """A root that is a PARENT of a governed location would put sealed inputs
    inside the writable surface -- the same defect from the other direction."""
    deep = base / ro.NAMESPACE / ("%s-%s" % (REVIEW_ID, MANIFEST[:12]))
    inner = deep / "governed"
    inner.mkdir(parents=True)
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base,
                              forbidden=(inner,))
    assert "PARENT" in str(ei.value) or "NOT empty" in str(ei.value)


# -------------------------------------------------------------- the binding

def test_the_binding_is_read_off_the_sealed_manifest():
    manifest = {"review_id": REVIEW_ID, "substantive_round": "2 of 2",
                "review_runtime": {"runtime_manifest_sha256": RUNTIME},
                "__manifest_sha256__": MANIFEST}
    assert ro.binding_for(manifest) == _binding()


def test_a_binding_missing_any_field_is_refused(tmp_path):
    for field in ro.BINDING_FIELDS:
        with pytest.raises(ro.OutputRootRefused) as ei:
            ro.write_binding(tmp_path, _binding(**{field: ""}))
        assert field in str(ei.value)


def test_a_matching_binding_is_accepted(bundle, base):
    root = ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    ro.write_binding(root, _binding())
    assert ro.check_binding(root, _binding())["review_id"] == REVIEW_ID


@pytest.mark.parametrize("field,wrong", [
    ("review_id", "N14-BUNDLE-SOMETHING-ELSE"),
    ("manifest_sha256", "ff" * 32),
    ("runtime_manifest_sha256", "ff" * 32),
    ("substantive_round", "1 of 2"),
])
def test_an_artifact_bound_to_another_review_object_is_refused(bundle, base,
                                                               field, wrong):
    """Each of the four bound fields on its own is enough to refuse. A wrong
    manifest or a wrong runtime digest means the artifacts describe different
    bytes than the ones in front of you."""
    root = ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    ro.write_binding(root, _binding(**{field: wrong}))
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.check_binding(root, _binding())
    assert field in str(ei.value)
    assert "DIFFERENT review object" in str(ei.value)


def test_a_root_with_no_binding_at_all_is_refused(bundle, base):
    root = ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    with pytest.raises(ro.OutputRootRefused) as ei:
        ro.check_binding(root, _binding())
    assert ro.BINDING_FILE in str(ei.value)


def test_an_unreadable_binding_is_refused_rather_than_ignored(bundle, base):
    root = ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    (root / ro.BINDING_FILE).write_text("{ not json", encoding="utf-8")
    with pytest.raises(ro.OutputRootRefused):
        ro.check_binding(root, _binding())


def test_the_binding_file_names_every_bound_field(bundle, base):
    root = ro.create_output_root(bundle, REVIEW_ID, MANIFEST, base=base)
    written = json.loads(ro.write_binding(root, _binding())
                         .read_text(encoding="utf-8"))
    for field in ro.BINDING_FIELDS:
        assert written[field] == _binding()[field]


def test_the_retained_returns_are_named_and_are_not_scratch():
    """The three returns are declared so the runner can assert they never end
    up inside the ephemeral directory."""
    assert ro.RETAINED_ARTIFACTS == ("INITIAL_FINDINGS.md", "FREEZE.json",
                                     "ATTESTATION.md")
    assert ro.SCRATCH_NAME.startswith(".")
    assert ro.SCRATCH_NAME not in ro.RETAINED_ARTIFACTS
