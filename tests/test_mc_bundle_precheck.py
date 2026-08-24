"""N09's required mitigation: the trust root is rebuilt, not inferred.

THE TEST THE RULING NAMED is the last one in this file -- a self-consistent
forged (prepared, authority) pair that `verify_supplement_authority`
accepts, against an on-disk bundle that does not match. The verifier says
yes; the precheck says no. That gap is the whole reason the mitigation
exists, and it is the one thing here that would be worth writing even if
everything else were dropped.
"""
from __future__ import annotations

import dataclasses
import hashlib

import pytest

from itsf.mc import bundle_precheck as bp
from itsf.mc import supplement_authority as sa

from test_mc_supplement_provenance_battery import (  # noqa: F401
    _fixture_root, authority, make_prod, prod)


def _write(root, files):
    for name, body in files.items():
        (root / name).write_bytes(body)


def _table(files):
    return tuple(bp.BundleEntry(name=n, size=len(b),
                                sha256=hashlib.sha256(b).hexdigest())
                 for n, b in sorted(files.items()))


FILES = {"a.jsonl": b"alpha\n", "b.json": b'{"k": 1}\n', "c.md": b"# c\n"}


def test_a_matching_bundle_returns_what_was_actually_on_disk(tmp_path):
    _write(tmp_path, FILES)
    out = bp.precheck_bundle_on_disk(tmp_path, _table(FILES), for_tests=True)
    assert out.n_files == 3
    assert {e.name for e in out.recomputed} == set(FILES)
    for e in out.recomputed:
        assert e.sha256 == hashlib.sha256(FILES[e.name]).hexdigest()
    assert len(out.summary_digest) == 64


def test_the_result_carries_the_table_not_a_boolean():
    """A boolean would let the run evidence say "checked" while recording
    nothing about what it checked against."""
    fields = {f.name for f in dataclasses.fields(bp.BundlePrecheck)}
    assert "recomputed" in fields and "summary_digest" in fields
    assert "ok" not in fields and "passed" not in fields


@pytest.mark.parametrize("mutate,fragment", [
    (lambda f: f.__setitem__("a.jsonl", b"tampered\n"), "sha256"),
    (lambda f: f.__setitem__("a.jsonl", b"alpha\n\n"), "bytes on disk"),
    (lambda f: f.pop("b.json"), "MISSING"),
])
def test_any_divergence_refuses(tmp_path, mutate, fragment):
    on_disk = dict(FILES)
    mutate(on_disk)
    _write(tmp_path, on_disk)
    with pytest.raises(bp.BundlePrecheckError) as ei:
        bp.precheck_bundle_on_disk(tmp_path, _table(FILES), for_tests=True)
    assert ei.value.code == "bundle_ondisk_mismatch"
    assert fragment in str(ei.value)


def test_an_extra_file_refuses(tmp_path):
    """A bundle with a file the sealed set does not name is not the bundle
    that was sealed, whatever the named files hash to."""
    _write(tmp_path, dict(FILES, extra=b"surprise\n"))
    with pytest.raises(bp.BundlePrecheckError) as ei:
        bp.precheck_bundle_on_disk(tmp_path, _table(FILES), for_tests=True)
    assert "not in the sealed set" in str(ei.value)


def test_a_caller_supplied_table_is_refused_without_saying_so(tmp_path):
    """The trust root must not slide back to a caller. Supplying a table
    is a test affordance and has to be named as one."""
    _write(tmp_path, FILES)
    with pytest.raises(bp.BundlePrecheckError) as ei:
        bp.precheck_bundle_on_disk(tmp_path, _table(FILES))
    assert ei.value.code == "bundle_expected_table_unpinned"


def test_the_signature_accepts_no_object_that_reports_itself():
    """The N09 ruling in one assertion: the gate's inputs are a path and
    the bytes behind it. If a PreparedMCInput or SupplementAuthority ever
    appears in this signature, the mitigation has been undone -- the
    forged pair can fabricate exactly those."""
    import inspect
    params = inspect.signature(bp.precheck_bundle_on_disk).parameters
    assert set(params) == {"bundle_root", "expected", "for_tests"}
    src = inspect.getsource(bp.precheck_bundle_on_disk)
    for forbidden in ("PreparedMCInput", "SupplementAuthority",
                      "verify_supplement_authority"):
        assert forbidden not in src, forbidden


def test_a_missing_root_refuses_rather_than_passing_vacuously(tmp_path):
    with pytest.raises(bp.BundlePrecheckError) as ei:
        bp.precheck_bundle_on_disk(tmp_path / "nope", _table(FILES),
                                   for_tests=True)
    assert ei.value.code == "bundle_root_absent"


# ---------------------------------------------------------------------------
# The test the ruling named
# ---------------------------------------------------------------------------

def test_a_self_consistent_forged_pair_does_not_survive_the_disk(
        prod, authority, tmp_path):
    """MEASURED 2026-08-24, and the reason this module exists.

    Forge BOTH the prepared input and the authority so the pair agrees
    with itself. `verify_supplement_authority` accepts it -- that is the
    F1/F2 residual, disclosed and not repaired, and it is real:

        VERIFY_ACCEPTED_FULLY_FORGED_PAIR=True

    The verifier has proved internal consistency and nothing else. Point
    the precheck at a bundle on disk that does not match the sealed table
    and it refuses, because it never asks either object anything."""
    class _StrLiar(str):
        def __str__(self):
            return "f" * 64

        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        __hash__ = str.__hash__

    def _forge(obj, **over):
        new = object.__new__(type(obj))
        for f in dataclasses.fields(obj):
            object.__setattr__(new, f.name,
                               over.get(f.name, getattr(obj, f.name)))
        return new

    table = dict(prod.file_sha256)
    first = sorted(table)[0]
    poisoned = dict(table)
    poisoned[first] = _StrLiar(table[first])
    bad_prep = _forge(prod, file_sha256=poisoned)
    bad_auth = _forge(authority,
                      bundle_table_digest=sa.bundle_table_digest(poisoned))
    object.__setattr__(bad_auth, "authority_digest",
                       sa._digest(sa.AUTHORITY_DIGEST_SCHEMA,
                                  sa._authority_payload(bad_auth)))

    # the verifier says yes -- internal consistency, and nothing more
    assert sa.verify_supplement_authority(bad_auth, bad_prep) is bad_auth

    # and the disk says no, without consulting either object
    _write(tmp_path, dict(FILES, **{"a.jsonl": b"not the sealed bytes\n"}))
    with pytest.raises(bp.BundlePrecheckError) as ei:
        bp.precheck_bundle_on_disk(tmp_path, _table(FILES), for_tests=True)
    assert ei.value.code == "bundle_ondisk_mismatch"


def test_verifier_success_is_never_cited_as_bundle_provenance():
    """The ruling's documentary half: no document, gate or audit may treat
    verify_supplement_authority=PASS on its own as evidence about the real
    bundle.

    Enforced where it can be mechanically: this module never CALLS it. It
    is named several times in prose, explaining why it is not enough --
    which is the opposite of relying on it, and the check has to be able
    to tell those apart. My first version of this test could not, and its
    first line was `assert <something> or True`, which is not an
    assertion at all."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(bp))
    called = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = (fn.id if isinstance(fn, ast.Name)
                else fn.attr if isinstance(fn, ast.Attribute) else "")
        if name == "verify_supplement_authority":
            called.append(node.lineno)
    assert not called, (
        "bundle_precheck CALLS verify_supplement_authority at line(s) "
        f"{called}; the whole point of N09's mitigation is that the trust "
        "root is rebuilt from bytes rather than inherited from a verifier "
        "a forged pair can satisfy")

    # and the prose mentions are still there, so the reason survives in
    # the file rather than only in a commit message
    assert "verify_supplement_authority" in inspect.getsource(bp)
