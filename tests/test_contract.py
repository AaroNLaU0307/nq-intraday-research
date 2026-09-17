"""TASK 1 -- sealed contract loader, and the mutation tests that prove the
binding is real.

Every mutation below is applied to a COPY of the sealed set. The real sealed
files are never written to.
"""
from __future__ import annotations

import json

import pytest

from conftest import refresh_digest
from r1.contract import BOUND_CONTENT_COMMIT, load_sealed_contract
from r1.errors import SealIdentityError


# ---------------------------------------------------------------- positive
def test_contract_loads_and_binds_the_seal(contract):
    assert contract.content_commit == BOUND_CONTENT_COMMIT
    assert contract.event_family == ("CPI", "NFP")
    assert contract.k == 1
    assert contract.materiality_m_usd == pytest.approx(3.99)
    assert contract.pre_seal_structural_n == 252
    assert (contract.cpi_structural_n, contract.nfp_structural_n) == (118, 134)
    assert contract.roll_transition_exclusions == 0
    assert contract.holding_minutes == 56


def test_timing_matches_the_sealed_clock(contract):
    assert contract.pre_release_anchor_minute == 8 * 60 + 29
    assert contract.reaction_close_minute == 8 * 60 + 31
    assert contract.signal_complete_minute == 8 * 60 + 32
    assert contract.entry_minute == 8 * 60 + 33
    assert contract.exit_minute == 9 * 60 + 29
    # the sealed 60-second latency budget
    assert contract.entry_minute == contract.signal_complete_minute + 1


def test_bootstrap_grammar_is_sealed(contract):
    assert contract.bootstrap_block_events == 5
    assert contract.bootstrap_sensitivity_block_events == 10
    assert contract.bootstrap_resamples == 10_000
    assert contract.bootstrap_seeds == (7, 13, 31)
    assert contract.bootstrap_interval_level == 0.95


def test_contract_is_immutable(contract):
    with pytest.raises(Exception):
        contract.k = 2                                     # frozen dataclass
    with pytest.raises(Exception):
        contract.cost_scenarios["Base"] = None             # mapping proxy


def test_loader_accepts_an_untouched_copy(sealed_copy):
    c = load_sealed_contract(sealed_copy)
    assert c.pre_seal_structural_n == 252


# ---------------------------------------------------------------- mutations
def _mutate(path, fn):
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_mutation_k(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d["operative_design"].__setitem__("k", 2))
    with pytest.raises(SealIdentityError, match="k"):
        load_sealed_contract(sealed_copy)


def test_mutation_event_family(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d["operative_design"].__setitem__("EVENT_FAMILY",
                                                        ["CPI", "NFP", "PPI"]))
    with pytest.raises(SealIdentityError, match="event family"):
        load_sealed_contract(sealed_copy)


def test_mutation_reaction_anchor(sealed_copy):
    rel = "artifacts/PSMV_STRUCTURAL_REPORT.json"
    _mutate(sealed_copy / rel,
            lambda d: d["anchor_availability"]["required_anchors"].__setitem__(
                "C_0831", "minute_of_day_et=512"))
    refresh_digest(sealed_copy, rel)
    with pytest.raises(SealIdentityError, match="label"):
        load_sealed_contract(sealed_copy)


def test_mutation_entry_time(sealed_copy):
    rel = "artifacts/PSMV_STRUCTURAL_REPORT.json"
    _mutate(sealed_copy / rel,
            lambda d: d["anchor_availability"]["required_anchors"].__setitem__(
                "O_0833", "minute_of_day_et=514"))
    refresh_digest(sealed_copy, rel)
    with pytest.raises(SealIdentityError):
        load_sealed_contract(sealed_copy)


def test_mutation_entry_reference_string(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d["operative_design"].__setitem__(
                "PRIMARY_ENTRY_REFERENCE", "O(08:34)"))
    with pytest.raises(SealIdentityError, match="entry reference"):
        load_sealed_contract(sealed_copy)


def test_mutation_exit_time(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d["operative_design"].__setitem__("EXIT", "O(09:59)"))
    with pytest.raises(SealIdentityError, match="exit reference"):
        load_sealed_contract(sealed_copy)


def test_mutation_structural_n(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d["operative_design"].__setitem__(
                "PRE_SEAL_STRUCTURAL_N", 250))
    with pytest.raises(SealIdentityError, match="structural n"):
        load_sealed_contract(sealed_copy)


def test_mutation_seal_identity(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d.__setitem__("CONTENT_COMMIT", "0" * 40))
    with pytest.raises(SealIdentityError, match="different seal"):
        load_sealed_contract(sealed_copy)


def test_mutation_unsealed_prereg(sealed_copy):
    _mutate(sealed_copy / "R1_S1_SEAL_ATTESTATION.json",
            lambda d: d.__setitem__("PREREG_SEALED", "NO"))
    with pytest.raises(SealIdentityError, match="not sealed"):
        load_sealed_contract(sealed_copy)


def test_mutation_any_sealed_byte(sealed_copy):
    """A single appended byte anywhere in the sealed set is refused."""
    p = sealed_copy / "R1_S1_PREREGISTRATION_SEALED.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SealIdentityError, match="has changed"):
        load_sealed_contract(sealed_copy)


def test_mutation_calendar_digest_is_carried(sealed_copy):
    rel = "artifacts/PSMV_STRUCTURAL_REPORT.json"
    _mutate(sealed_copy / rel,
            lambda d: d["inputs"].__setitem__("event_calendar_sha256", "0" * 64))
    refresh_digest(sealed_copy, rel)
    c = load_sealed_contract(sealed_copy)
    assert c.event_calendar_sha256 == "0" * 64          # carried, and L-11 will
    # refuse it at load time -- see tests/test_events.py::test_l11_calendar_digest


def test_mutation_manifest_disagrees_with_the_seal(sealed_copy):
    rel = "R1_PREREG_MANIFEST.json"
    _mutate(sealed_copy / rel,
            lambda d: d["materiality"].__setitem__("k", 2))
    refresh_digest(sealed_copy, rel)
    with pytest.raises(SealIdentityError):
        load_sealed_contract(sealed_copy)


def test_appending_a_registry_row_breaks_the_seal(sealed_copy):
    """A found consequence, recorded as a test rather than as an opinion.

    R1_TRIAL_REGISTRY.md is an APPEND-ONLY event chain that must still grow
    (`S2_BUILD_STARTED`, `RUN_STARTED`, `REVEAL_AUTHORIZED` ...), and it is
    also inside the sealed digest set. Appending the next row therefore makes
    the engine refuse to load. That is correct behaviour for a digest, and it
    is a real S3 blocker: see S2_BUILD_REPORT.md section 10.
    """
    p = sealed_copy / "R1_TRIAL_REGISTRY.md"
    p.write_text(p.read_text(encoding="utf-8")
                 + "\n| 8 | 2026-09-18 | `RUN_STARTED` | Aaron | ... |\n",
                 encoding="utf-8")
    with pytest.raises(SealIdentityError, match="R1_TRIAL_REGISTRY"):
        load_sealed_contract(sealed_copy)
