"""S2 implementation identity: the executable bytes must be the attested ones.

The failure this exists to prevent is specific and was actually made: a report
claimed `S2_FINAL_BUILD_COMMIT = 0bc815d` while HEAD was two commits further on.
A run that claims one implementation identity while executing another is not
reproducible, whatever its science looks like.
"""
from __future__ import annotations

import json
import shutil

import pytest

from r1.build_identity import (ATTESTATION_FILE, RUNTIME_SOURCE_DIR,
                               BuildIdentity, assert_executable_identity,
                               load_build_identity, runtime_source_map,
                               runtime_source_rollup)
from r1.contract import PROJECT_ROOT
from r1.errors import SealIdentityError


@pytest.fixture
def attested_tree(tmp_path):
    """A miniature project: runtime sources plus a matching attestation."""
    shutil.copytree(PROJECT_ROOT / RUNTIME_SOURCE_DIR,
                    tmp_path / RUNTIME_SOURCE_DIR,
                    ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "R1_EXECUTION_LEDGER.md").write_text("ledger\n", encoding="utf-8")
    attestation = {
        "S2_CODE_COMMIT": "a" * 40,
        "CONTENT_COMMIT": "46b8aef9d2471dd427db6a780435e743660a6f24",
        "SEAL_ATTESTATION_COMMIT": "595af1c9663eb868e9f2d72f44abfe2f426ca24d",
        "runtime_source": {
            "n_files": len(runtime_source_map(tmp_path)),
            "rollup_sha256": runtime_source_rollup(tmp_path),
            "files": runtime_source_map(tmp_path),
        },
        "sealed_digests": {},
        "state": {"TRIAL_CONSUMED": "NO"},
    }
    (tmp_path / ATTESTATION_FILE).write_text(
        json.dumps(attestation, indent=2), encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------- rollup
def test_rollup_covers_every_runtime_source_file():
    files = runtime_source_map()
    assert len(files) >= 20
    assert all(rel.startswith("r1/") and rel.endswith(".py") for rel in files)
    assert "r1/contract.py" in files and "r1/pipeline.py" in files
    assert len(runtime_source_rollup()) == 64


def test_rollup_is_deterministic():
    assert runtime_source_rollup() == runtime_source_rollup()


def test_tools_are_not_part_of_the_runtime_surface():
    """Validators are not runtime; editing one must not invalidate a run."""
    assert not any("tools" in rel for rel in runtime_source_map())


# ---------------------------------------------------------------- loading
def test_load_build_identity(attested_tree):
    ident = load_build_identity(attested_tree)
    assert ident.s2_code_commit == "a" * 40
    assert ident.s2_build_attestation_commit == "tag:r1-s2-built"
    assert ident.runtime_source_files == len(runtime_source_map(attested_tree))


def test_a_missing_attestation_refuses_rather_than_defaulting(tmp_path):
    with pytest.raises(SealIdentityError, match="no attested S2 code identity"):
        load_build_identity(tmp_path)


def test_a_malformed_attestation_refuses(attested_tree):
    (attested_tree / ATTESTATION_FILE).write_text("{oops", encoding="utf-8")
    with pytest.raises(SealIdentityError, match="malformed"):
        load_build_identity(attested_tree)


def test_missing_fields_refuse(attested_tree):
    data = json.loads((attested_tree / ATTESTATION_FILE).read_text("utf-8"))
    del data["CONTENT_COMMIT"]
    (attested_tree / ATTESTATION_FILE).write_text(json.dumps(data), "utf-8")
    with pytest.raises(SealIdentityError, match="missing required fields"):
        load_build_identity(attested_tree)


def test_a_short_commit_refuses(attested_tree):
    data = json.loads((attested_tree / ATTESTATION_FILE).read_text("utf-8"))
    data["S2_CODE_COMMIT"] = "0bc815d"          # the exact stale-short form
    (attested_tree / ATTESTATION_FILE).write_text(json.dumps(data), "utf-8")
    with pytest.raises(SealIdentityError, match="full 40-character sha"):
        load_build_identity(attested_tree)


# ------------------------------------------------- the S3 preflight check
def test_executable_identity_passes_on_an_untouched_tree(attested_tree):
    ident = assert_executable_identity(attested_tree)
    assert ident.s2_code_commit == "a" * 40


def test_a_metadata_only_change_does_NOT_invalidate(attested_tree):
    """A ledger append, a state pointer, a report edit: all irrelevant."""
    ledger = attested_tree / "R1_EXECUTION_LEDGER.md"
    ledger.write_text(ledger.read_text(encoding="utf-8")
                      + "| 4 | ... | S2_BUILD_IDENTITY_FROZEN | ... |\n",
                      encoding="utf-8")
    (attested_tree / "PROJECT_STATE.md").write_text("state\n", encoding="utf-8")
    assert_executable_identity(attested_tree)            # still fine


def test_a_code_edit_DOES_invalidate(attested_tree):
    target = attested_tree / RUNTIME_SOURCE_DIR / "trade.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tweak\n",
                      encoding="utf-8")
    with pytest.raises(SealIdentityError, match="executable identity mismatch"):
        assert_executable_identity(attested_tree)


def test_an_added_runtime_file_invalidates(attested_tree):
    (attested_tree / RUNTIME_SOURCE_DIR / "extra.py").write_text(
        "X = 1\n", encoding="utf-8")
    with pytest.raises(SealIdentityError, match="executable identity mismatch"):
        assert_executable_identity(attested_tree)


def test_a_deleted_runtime_file_invalidates(attested_tree):
    (attested_tree / RUNTIME_SOURCE_DIR / "covariates.py").unlink()
    with pytest.raises(SealIdentityError, match="executable identity mismatch"):
        assert_executable_identity(attested_tree)


def test_the_mismatch_message_names_the_changed_file(attested_tree):
    target = attested_tree / RUNTIME_SOURCE_DIR / "verdict.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SealIdentityError) as exc:
        assert_executable_identity(attested_tree)
    assert "r1/verdict.py" in str(exc.value)


# ---------------------------------------------------------------- hygiene
def test_no_runtime_module_hard_codes_a_build_commit():
    """The stale-identity defect, pinned as a test."""
    import re
    stale = re.compile(r"0bc815dc22863e50777311a9c2c25922ecfeb4fd|53518cd|6c133c7")
    for rel, _ in runtime_source_map().items():
        text = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
        assert not stale.search(text), rel


def test_build_identity_module_defines_no_commit_constant():
    text = (PROJECT_ROOT / "r1" / "build_identity.py").read_text(encoding="utf-8")
    import re
    assert not re.search(r'"[0-9a-f]{40}"', text)
    assert not re.search(r"'[0-9a-f]{40}'", text)


def test_build_identity_is_a_frozen_record():
    assert BuildIdentity.__dataclass_params__.frozen
