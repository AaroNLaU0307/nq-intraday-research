"""The operational execution ledger, and the immutability of the sealed registry.

Two integrity models, tested as two different things:

    sealed R1_TRIAL_REGISTRY.md   exact immutable digest
    R1_EXECUTION_LEDGER.md        append-only hash chain
"""
from __future__ import annotations

import shutil

import pytest

from r1 import ledger
from r1.contract import PROJECT_ROOT, load_sealed_contract, sha256_file
from r1.errors import LedgerError, SealIdentityError
from r1.ledger import (GENESIS, RUN_STARTED, S2_BUILD_COMPLETE, append_event,
                       assert_sealed_registry_unchanged, create_ledger,
                       current_digest, verify_chain)

LIVE_LEDGER = PROJECT_ROOT / "R1_EXECUTION_LEDGER.md"


@pytest.fixture
def fresh_ledger(tmp_path, contract):
    path = tmp_path / "R1_EXECUTION_LEDGER.md"
    create_ledger(path, contract=contract,
                  sealed_registry_sha256=contract.trial_registry_sha256,
                  seal_attestation_commit="595af1c9663eb868e9f2d72f44abfe2f426ca24d",
                  utc="2026-09-17T00:00:00Z")
    return path


# ------------------------------------------------------------ the live ledger
def test_the_live_ledger_exists_and_verifies():
    entries = verify_chain(LIVE_LEDGER)
    assert entries[0].event == GENESIS
    assert any(e.event == S2_BUILD_COMPLETE for e in entries)
    assert len(current_digest(LIVE_LEDGER)) == 64


def test_the_live_ledger_is_outside_the_sealed_digest_set():
    import json
    seal = json.loads((PROJECT_ROOT / "R1_S1_SEAL_ATTESTATION.json").read_text(
        encoding="utf-8"))
    assert "R1_EXECUTION_LEDGER.md" not in seal["sealed_digests"]
    assert "R1_TRIAL_REGISTRY.md" in seal["sealed_digests"]


def test_genesis_binds_lineage_and_seal(contract):
    genesis = verify_chain(LIVE_LEDGER)[0]
    for required in (
            "lineage R1",
            f"SAMPLE_FORMAL_TRIAL_ORDINAL={contract.sample_formal_trial_ordinal}",
            "PRIOR_LINEAGE=ITSF S0-T001",
            f"INHERITED_RESEARCHER_EXPOSURE_COUNT="
            f"{contract.inherited_researcher_exposure_count}",
            f"SEALED_TRIAL_REGISTRY_SHA256={contract.trial_registry_sha256}",
            f"CONTENT_COMMIT={contract.content_commit}",
            "SEAL_ATTESTATION_COMMIT=595af1c9663eb868e9f2d72f44abfe2f426ca24d"):
        assert required in genesis.detail, required


# ------------------------------------------------------------ sealed registry
def test_sealed_registry_is_unchanged(contract):
    assert_sealed_registry_unchanged(contract)
    assert sha256_file(PROJECT_ROOT / "R1_TRIAL_REGISTRY.md") == \
        contract.trial_registry_sha256


def test_sealed_registry_modification_refuses(contract, tmp_path):
    shutil.copytree(PROJECT_ROOT / "artifacts", tmp_path / "artifacts")
    for rel in ("R1_TRIAL_REGISTRY.md", "R1_S1_SEAL_ATTESTATION.json"):
        shutil.copy2(PROJECT_ROOT / rel, tmp_path / rel)
    p = tmp_path / "R1_TRIAL_REGISTRY.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n| 8 | ... |\n",
                 encoding="utf-8")
    with pytest.raises(SealIdentityError, match="immutable"):
        assert_sealed_registry_unchanged(contract, root=tmp_path)


def test_run_started_cannot_be_recorded_in_the_sealed_registry():
    for event in (RUN_STARTED, S2_BUILD_COMPLETE, "REVEALED"):
        with pytest.raises(SealIdentityError, match="sealed"):
            ledger.refuse_operational_event_in_sealed_registry(event)
    # GENESIS is the ledger's own first row, not an operational event
    ledger.refuse_operational_event_in_sealed_registry(GENESIS)


# ------------------------------------------------------------ append-only
def test_a_valid_append_extends_the_chain(fresh_ledger):
    before = current_digest(fresh_ledger)
    ancestry_before = ledger.ancestry(fresh_ledger)
    entry = append_event(fresh_ledger, RUN_STARTED, "Aaron",
                         "authorized run; trial consumed",
                         utc="2026-09-18T12:00:00Z")
    after = current_digest(fresh_ledger)
    assert after != before                      # the head moves
    assert entry.parent == before               # and it chains to the old head
    assert ledger.ancestry(fresh_ledger)[:len(ancestry_before)] == ancestry_before


def test_editing_a_historical_entry_refuses(fresh_ledger):
    append_event(fresh_ledger, RUN_STARTED, "Aaron", "original detail",
                 utc="2026-09-18T12:00:00Z")
    text = fresh_ledger.read_text(encoding="utf-8")
    fresh_ledger.write_text(text.replace("original detail", "edited detail"),
                            encoding="utf-8")
    with pytest.raises(LedgerError, match="was edited"):
        verify_chain(fresh_ledger)


def test_deleting_a_historical_entry_refuses(fresh_ledger):
    append_event(fresh_ledger, S2_BUILD_COMPLETE, "main agent", "one",
                 utc="2026-09-18T01:00:00Z")
    append_event(fresh_ledger, RUN_STARTED, "Aaron", "two",
                 utc="2026-09-18T02:00:00Z")
    lines = fresh_ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [ln for ln in lines if "| one |" not in ln]
    fresh_ledger.write_text("".join(kept), encoding="utf-8")
    with pytest.raises(LedgerError, match="sequence broken|does not chain"):
        verify_chain(fresh_ledger)


def test_reordering_entries_refuses(fresh_ledger):
    append_event(fresh_ledger, S2_BUILD_COMPLETE, "main agent", "alpha",
                 utc="2026-09-18T01:00:00Z")
    append_event(fresh_ledger, RUN_STARTED, "Aaron", "beta",
                 utc="2026-09-18T02:00:00Z")
    lines = fresh_ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    i = next(n for n, ln in enumerate(lines) if "| alpha |" in ln)
    j = next(n for n, ln in enumerate(lines) if "| beta |" in ln)
    lines[i], lines[j] = lines[j], lines[i]
    fresh_ledger.write_text("".join(lines), encoding="utf-8")
    with pytest.raises(LedgerError, match="sequence broken|does not chain"):
        verify_chain(fresh_ledger)


def test_an_appended_row_with_a_forged_parent_refuses(fresh_ledger):
    append_event(fresh_ledger, RUN_STARTED, "Aaron", "ok",
                 utc="2026-09-18T12:00:00Z")
    forged = ("| 3 | 2026-09-19T00:00:00Z | `REVEALED` | someone | forged | "
              "`" + "0" * 64 + "` | `" + "1" * 64 + "` |\n")
    with fresh_ledger.open("a", encoding="utf-8") as fh:
        fh.write(forged)
    with pytest.raises(LedgerError, match="does not chain"):
        verify_chain(fresh_ledger)


def test_genesis_is_written_once(fresh_ledger, contract):
    with pytest.raises(LedgerError, match="written once"):
        create_ledger(fresh_ledger, contract=contract,
                      sealed_registry_sha256=contract.trial_registry_sha256,
                      seal_attestation_commit="x")
    with pytest.raises(LedgerError, match="GENESIS is written once"):
        append_event(fresh_ledger, GENESIS, "x", "y")


def test_unknown_event_refuses(fresh_ledger):
    with pytest.raises(LedgerError, match="unknown ledger event"):
        append_event(fresh_ledger, "PROMOTED", "someone", "nope")


def test_missing_ledger_refuses(tmp_path):
    with pytest.raises(LedgerError, match="not found"):
        verify_chain(tmp_path / "absent.md")


def test_ledger_changes_no_scientific_constant(contract):
    """The ledger records what happened; it never states a design fact."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(ledger))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not {"k", "entry_minute", "exit_minute", "materiality_m_usd"} & names


def test_seal_snapshot_resolves_the_attestation_by_tag_not_by_grep():
    """A later commit that MENTIONS the attestation is not the attestation.

    The first version of tools/validate_seal_snapshot.py searched commit
    messages and picked up the ledger-record commit as soon as one existed,
    turning a clean PASS into a FAIL. It now resolves the tag and checks that
    its parent is the CONTENT_COMMIT.
    """
    src = (PROJECT_ROOT / "tools" / "validate_seal_snapshot.py").read_text(
        encoding="utf-8")
    assert "--grep=SEAL_ATTESTATION_COMMIT" not in src
    assert 'rev-parse", "r1-s1-sealed^{commit}"' in src
