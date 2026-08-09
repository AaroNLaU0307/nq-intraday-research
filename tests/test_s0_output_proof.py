"""Tests for itsf.s0.output_proof — final S0_REPORT.json -> governance.* proof.

Hermetic and fully synthetic: no real archive, no registry, no run, no clock.
Every fixture is built in-memory from the constants below, and every governance
value used here is deliberately unlike any production value.

The suite is organised around the three measured failures the module exists to
avoid (see its docstring): the check must run AFTER the sealed bytes exist and
parse THOSE (F-a); the expected side must not be a mirror of the target and the
pass must come from a real comparison (F-b); the expected key domain must not
shrink when the guarded object shrinks (F-c).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from itsf.s0 import output_proof as op
from itsf.s0.output_proof import (CONTRACT_GOVERNANCE_KEYS, GovernanceProof,
                                  ProofRefused, SourceContext,
                                  prove_governance)

REPO = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# synthetic expected-side inputs
# --------------------------------------------------------------------------
TRIAL_ID = "S0-TSYNTH"
COMMIT = "1f2e3d4c5b6a70819283746556473829100aabbc"          # 40 hex
SEED = 19750102
SEED_PROVENANCE = "synthetic fixture provenance (no real approval)"
SEQ = 12

FROZEN_PATHS = (
    "SYNTH_CHARTER.md", "SYNTH_PREREG.md", "SYNTH_plan.yaml",
    "SYNTH_METHOD.md", "gate1/SYNTH_params.yaml",
    "gate1/SYNTH_registry.yaml", "gate1/snapshots/SYNTH_manifest.json",
)


def _digest(path: str) -> str:
    return hashlib.sha256(f"synthetic-frozen::{path}".encode("utf-8")).hexdigest()


AUTHORITY = {p: _digest(p) for p in FROZEN_PATHS}

SNAPSHOT = {
    # exactly the shape RealChain.authorization_snapshot() returns
    # (scripts/s0_real_run.py:2253-2280)
    "registry_sha256": hashlib.sha256(b"synthetic-registry").hexdigest(),
    "event_sequence": SEQ,
    "trial_id": TRIAL_ID,
    "authorized_commit": COMMIT,
    "exact_authorization_text_sha256":
        hashlib.sha256(b"synthetic-sentence").hexdigest(),
}

# Every literal an honest report is expected to CARRY. Used by the leak test.
EXPECTED_VALUES = (TRIAL_ID, COMMIT, str(SEED), str(SEQ),
                   SNAPSHOT["registry_sha256"],
                   SNAPSHOT["exact_authorization_text_sha256"],
                   *AUTHORITY.values())


def _context(**overrides) -> SourceContext:
    kwargs = {
        "authorization_snapshot": dict(SNAPSHOT),
        "frozen_hash_authority": dict(AUTHORITY),
        # observations = an INDEPENDENT re-hash that happens to agree
        "frozen_hash_observations": {p: _digest(p) for p in FROZEN_PATHS},
        "engineering_seed": SEED,
        "engineering_seed_provenance": SEED_PROVENANCE,
    }
    kwargs.update(overrides)
    return SourceContext(**kwargs)


def _honest_governance() -> dict:
    """What a truthful renderer would have sealed. Written out here by hand —
    NOT obtained from the module — so the test's target side is not a mirror of
    the module's expected side either."""
    return {
        "trial_id": TRIAL_ID,
        "authorized_commit": COMMIT,
        "engineering_seed": SEED,
        "frozen_hashes": {p: _digest(p) for p in FROZEN_PATHS},
        "registry_sequence_snapshot": SEQ,
    }


def _report_text(governance: dict, *, self_consistent: bool = False) -> str:
    """A synthetic FINAL S0_REPORT.json body: the governance block plus enough
    surrounding shape (an embedded manifest that hashes the governance block)
    to model a report whose own integrity metadata agrees with its content."""
    payload = {
        "governance": governance,
        "era_axis": {"note": "synthetic"},
        "mc_handoff_manifest": {
            "files": {}, "sealed_files": {},
            "self_excluded": ["S0_REPORT.json"]},
    }
    if self_consistent:
        payload["mc_handoff_manifest"]["governance_block_sha256"] = (
            _block_hash(governance))
    return json.dumps(payload, sort_keys=True, indent=1, allow_nan=False)


def _block_hash(governance: dict) -> str:
    return hashlib.sha256(
        json.dumps(governance, sort_keys=True).encode("utf-8")).hexdigest()


def _artifacts(governance: dict, **kw) -> dict:
    """The Stage-E artifact map as it looks at the END of the render flow —
    i.e. only after files["S0_REPORT.json"] has been assigned."""
    return {
        "S0_REPORT.md": "# synthetic",
        "HANDOFF_ADMISSION.json": "{}",
        "S0_REPORT.json": _report_text(governance, **kw),
    }


def _prove(governance: dict, context: SourceContext | None = None,
           **kw) -> GovernanceProof:
    return prove_governance(context or _context(),
                            sealed_artifacts=_artifacts(governance, **kw))


# ==========================================================================
# 1. the honest case
# ==========================================================================

def test_honest_synthetic_final_report_passes():
    proof = _prove(_honest_governance())
    assert proof.ok is True
    assert proof.problems == ()
    # 4 top-level scalars + 7 frozen-hash leaves, all actually compared
    assert proof.comparisons_required == 11
    assert proof.comparisons_performed == 11
    assert proof.actual_source == "sealed_artifact"
    assert proof.report_sha256 == hashlib.sha256(
        _report_text(_honest_governance()).encode("utf-8")).hexdigest()


def test_honest_report_passes_from_written_bytes(tmp_path):
    target = tmp_path / "S0_REPORT.json"
    target.write_bytes(_report_text(_honest_governance()).encode("utf-8"))
    proof = prove_governance(_context(), report_path=target)
    assert proof.ok is True
    assert proof.actual_source == "file"


# ==========================================================================
# 2. the five divergence classes, each with its own deterministic code
# ==========================================================================

def test_missing_key_fails():
    gov = _honest_governance()
    del gov["authorized_commit"]
    proof = _prove(gov)
    assert proof.ok is False
    assert "governance_proof_key_missing:governance.authorized_commit" in \
        proof.problems
    # the skipped leaf is visible in the count, not papered over
    assert proof.comparisons_performed == 10
    assert proof.comparisons_required == 11


def test_extra_key_fails():
    gov = _honest_governance()
    gov["approved_by"] = "someone"
    proof = _prove(gov)
    assert proof.ok is False
    assert "governance_proof_key_unexpected:governance.approved_by" in \
        proof.problems


def test_wrong_type_fails():
    gov = _honest_governance()
    gov["engineering_seed"] = str(SEED)          # "19750102", not 19750102
    proof = _prove(gov)
    assert proof.ok is False
    assert "governance_proof_type_mismatch:governance.engineering_seed" in \
        proof.problems
    # a wrong-typed leaf was still COMPARED — the count stays whole
    assert proof.comparisons_performed == 11


def test_wrong_value_fails():
    gov = _honest_governance()
    gov["trial_id"] = "S0-TOTHER"
    proof = _prove(gov)
    assert proof.ok is False
    assert "governance_proof_value_mismatch:governance.trial_id" in \
        proof.problems


def test_unexpected_null_fails():
    gov = _honest_governance()
    gov["registry_sequence_snapshot"] = None
    proof = _prove(gov)
    assert proof.ok is False
    assert ("governance_proof_null_value:governance.registry_sequence_snapshot"
            in proof.problems)
    # explicit null is NOT the same state as absent
    assert not any(p.startswith("governance_proof_key_missing")
                   for p in proof.problems)


def test_bool_does_not_satisfy_an_int_expectation():
    gov = _honest_governance()
    gov["registry_sequence_snapshot"] = True
    proof = _prove(gov)
    assert proof.ok is False
    assert ("governance_proof_type_mismatch:"
            "governance.registry_sequence_snapshot") in proof.problems


def test_each_divergence_class_has_its_own_deterministic_string():
    def mutate(fn):
        gov = _honest_governance()
        fn(gov)
        return _prove(gov).problems

    cases = {
        "missing": lambda g: g.pop("trial_id"),
        "extra": lambda g: g.update({"zzz": 1}),
        "type": lambda g: g.update({"trial_id": 7}),
        "value": lambda g: g.update({"trial_id": "S0-TOTHER"}),
        "null": lambda g: g.update({"trial_id": None}),
    }
    seen = {}
    for name, fn in cases.items():
        first, second = mutate(fn), mutate(fn)
        assert first == second, f"{name} problem strings are not deterministic"
        seen[name] = tuple(p for p in first
                           if not p.endswith("comparison_count"))
    codes = [problems[0].split(":", 1)[0] for problems in seen.values()]
    assert len(set(codes)) == len(codes), f"codes collided: {codes}"


def test_unparsable_and_non_object_reports_fail():
    ctx = _context()
    bad = prove_governance(ctx, sealed_artifacts={"S0_REPORT.json": "{not json"})
    assert bad.ok is False
    assert "governance_proof_report_unparsable" in bad.problems
    arr = prove_governance(ctx, sealed_artifacts={"S0_REPORT.json": "[1, 2]"})
    assert arr.ok is False
    assert "governance_proof_report_root_not_object" in arr.problems
    none = prove_governance(ctx, sealed_artifacts={"S0_REPORT.json": "{}"})
    assert none.ok is False
    assert "governance_proof_section_missing" in none.problems


# ==========================================================================
# 3. tamper that also fixes the report's own integrity metadata
# ==========================================================================

def test_self_consistent_tamper_is_still_caught():
    """A tamperer who rewrites governance AND the report's own embedded hash of
    it produces an internally consistent report. It is still caught, because
    the expected side never came from the report."""
    tampered = _honest_governance()
    victim = FROZEN_PATHS[3]
    tampered["frozen_hashes"] = dict(tampered["frozen_hashes"])
    tampered["frozen_hashes"][victim] = hashlib.sha256(b"forged").hexdigest()

    text = _report_text(tampered, self_consistent=True)
    parsed = json.loads(text)
    # the report agrees with itself ...
    assert (parsed["mc_handoff_manifest"]["governance_block_sha256"]
            == _block_hash(parsed["governance"]))
    # ... and the proof rejects it anyway
    proof = prove_governance(_context(), sealed_artifacts={"S0_REPORT.json": text})
    assert proof.ok is False
    assert (f"governance_proof_value_mismatch:governance.frozen_hashes[{victim}]"
            in proof.problems)


# ==========================================================================
# 4. F-c: the expected domain does not shrink with the guarded object
# ==========================================================================

def test_deleting_an_actual_path_does_not_shrink_the_expected_domain():
    gov = _honest_governance()
    victim = FROZEN_PATHS[0]
    gov["frozen_hashes"] = {k: v for k, v in gov["frozen_hashes"].items()
                            if k != victim}
    proof = _prove(gov)
    assert proof.ok is False
    assert (f"governance_proof_key_missing:governance.frozen_hashes[{victim}]"
            in proof.problems)
    assert proof.comparisons_required == 11        # unchanged by the deletion
    assert proof.comparisons_performed == 10


def test_emptying_frozen_hashes_entirely_still_expects_seven():
    gov = _honest_governance()
    gov["frozen_hashes"] = {}
    proof = _prove(gov)
    assert proof.ok is False
    missing = [p for p in proof.problems
               if p.startswith("governance_proof_key_missing:"
                               "governance.frozen_hashes[")]
    assert len(missing) == len(FROZEN_PATHS) == 7
    assert proof.comparisons_required == 11
    assert proof.comparisons_performed == 4


def test_expected_domain_is_derivable_without_the_actual_file():
    """Requirement: the expected key domain exists with no report anywhere."""
    tree = op._expected_tree(_context())
    assert set(tree) == CONTRACT_GOVERNANCE_KEYS
    assert set(tree["frozen_hashes"]) == set(FROZEN_PATHS)
    assert op._leaf_count(tree) == 11


# ==========================================================================
# 5. F-b: the pass is a real comparison, the expected side is independent
# ==========================================================================

def test_comparison_count_is_derived_not_hardcoded():
    three = {p: _digest(p) for p in FROZEN_PATHS[:3]}
    ctx = _context(frozen_hash_authority=three,
                   frozen_hash_observations=dict(three))
    gov = _honest_governance()
    gov["frozen_hashes"] = dict(three)
    proof = prove_governance(ctx, sealed_artifacts=_artifacts(gov))
    assert proof.comparisons_required == 7        # 4 scalars + 3 hashes
    assert proof.comparisons_performed == 7
    # ... but a 3-item restatement is not what the contract fixes at seven
    assert "governance_proof_context_frozen_hash_count" in proof.problems
    assert proof.ok is False


def test_authority_observation_conflict_is_a_problem():
    """The expected side is TWO derivations (freeze registry + on-disk re-hash);
    a disagreement is surfaced, never silently resolved."""
    victim = FROZEN_PATHS[2]
    obs = {p: _digest(p) for p in FROZEN_PATHS}
    obs[victim] = hashlib.sha256(b"mutated-on-disk").hexdigest()
    proof = _prove(_honest_governance(), _context(frozen_hash_observations=obs))
    assert proof.ok is False
    assert ("governance_proof_context_observation_conflict:"
            f"governance.frozen_hashes[{victim}]") in proof.problems


def test_missing_and_extra_observations_are_problems():
    obs = {p: _digest(p) for p in FROZEN_PATHS[:-1]}
    obs["SYNTH_UNREGISTERED.md"] = hashlib.sha256(b"x").hexdigest()
    proof = _prove(_honest_governance(), _context(frozen_hash_observations=obs))
    assert proof.ok is False
    assert ("governance_proof_context_observation_missing:"
            f"governance.frozen_hashes[{FROZEN_PATHS[-1]}]") in proof.problems
    assert ("governance_proof_context_observation_extra:"
            "governance.frozen_hashes[SYNTH_UNREGISTERED.md]") in proof.problems


# ==========================================================================
# 6. the deliberate registry-moved failure (requirement 8)
# ==========================================================================

def test_registry_moved_between_pre_run_snapshot_and_compute_fails():
    """RealChain.compute() re-reads the registry (scripts/s0_real_run.py:2305)
    while the expectation comes from the PRE-RUN snapshot. An event inserted in
    between MUST fail the proof — that is correct behaviour."""
    gov = _honest_governance()
    gov["registry_sequence_snapshot"] = SEQ + 1          # one event appeared
    proof = _prove(gov)
    assert proof.ok is False
    assert ("governance_proof_value_mismatch:"
            "governance.registry_sequence_snapshot") in proof.problems


def test_re_signed_authorization_between_snapshot_and_compute_fails():
    gov = _honest_governance()
    gov["authorized_commit"] = "0" * 40                  # re-authorized commit
    proof = _prove(gov)
    assert proof.ok is False
    assert "governance_proof_value_mismatch:governance.authorized_commit" in \
        proof.problems


# ==========================================================================
# 7. F-a: refusals — the proof cannot run before the final report exists
# ==========================================================================

def test_refused_when_final_report_is_not_in_the_artifact_map_yet():
    """Exactly the F-a wiring bug: called mid-render, before
    files["S0_REPORT.json"] is assigned."""
    early = {"S0_REPORT.md": "# md", "HANDOFF_ADMISSION.json": "{}"}
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), sealed_artifacts=early)
    assert "S0_REPORT.json" in str(exc.value)


def test_refused_when_the_final_report_entry_is_empty():
    with pytest.raises(ProofRefused):
        prove_governance(_context(), sealed_artifacts={"S0_REPORT.json": "  "})
    with pytest.raises(ProofRefused):
        prove_governance(_context(), sealed_artifacts={"S0_REPORT.json": None})


def test_refused_when_the_report_file_does_not_exist(tmp_path):
    with pytest.raises(ProofRefused):
        prove_governance(_context(), report_path=tmp_path / "S0_REPORT.json")
    empty = tmp_path / "S0_REPORT.json"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ProofRefused):
        prove_governance(_context(), report_path=empty)


def test_refused_when_pointed_at_anything_but_the_final_report(tmp_path):
    """Requirement 6: an evidence mirror copy is never the authority."""
    mirror = tmp_path / "EVIDENCE_S0_REPORT_COPY.json"
    mirror.write_text(_report_text(_honest_governance()), encoding="utf-8")
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), report_path=mirror)
    assert "S0_REPORT.json" in str(exc.value)


def test_refused_on_bad_wiring():
    ctx = _context()
    with pytest.raises(ProofRefused):
        prove_governance(ctx)                                    # neither
    with pytest.raises(ProofRefused):
        prove_governance(ctx, sealed_artifacts=_artifacts(_honest_governance()),
                         report_path="S0_REPORT.json")           # both
    with pytest.raises(ProofRefused):
        prove_governance({"trial_id": TRIAL_ID},                 # not a context
                         sealed_artifacts=_artifacts(_honest_governance()))


def test_refused_on_a_structurally_unusable_context():
    for bad in (
        {"authorization_snapshot": {k: v for k, v in SNAPSHOT.items()
                                    if k != "authorized_commit"}},
        {"authorization_snapshot": {**SNAPSHOT, "authorized_commit": "nope"}},
        {"authorization_snapshot": {**SNAPSHOT, "event_sequence": 0}},
        {"authorization_snapshot": {**SNAPSHOT, "event_sequence": True}},
        {"frozen_hash_authority": {}},
        {"frozen_hash_authority": {"p": "not-a-sha"}},
        {"frozen_hash_observations": {}},
        {"engineering_seed": "19750102"},
        {"engineering_seed": True},
        {"engineering_seed_provenance": "   "},
    ):
        with pytest.raises(ProofRefused):
            _context(**bad)


# ==========================================================================
# 8. structural: this module cannot be used to GENERATE governance content
# ==========================================================================

def test_the_module_exposes_no_generator_entry_point():
    assert op.__all__ == (
        "FINAL_REPORT_NAME", "CONTRACT_GOVERNANCE_KEYS",
        "CONTRACT_FROZEN_HASH_COUNT", "ProofRefused", "SourceContext",
        "GovernanceProof", "prove_governance")
    public = {name: getattr(op, name) for name in dir(op)
              if not name.startswith("_")}
    # the expected-tree builder is not reachable under any public name
    assert not any(value is op._expected_tree for value in public.values())
    # the only public callable this module DEFINES (bar the two dataclasses
    # and the exception, which are types) is the proof itself
    callables = {n for n, v in public.items()
                 if callable(v) and not isinstance(v, type)
                 and getattr(v, "__module__", None) == op.__name__}
    assert callables == {"prove_governance"}
    # and no public name advertises production of content
    assert not any(n.startswith(("build_", "make_", "render_", "generate_",
                                 "emit_", "patch_", "fix_", "write_", "to_"))
                   for n in public)


def test_the_module_contains_no_filesystem_write_call():
    source = Path(op.__file__).read_text(encoding="utf-8")
    for verb in ("write_text(", "write_bytes(", "open(", "json.dump(",
                 "shutil.", "mkdir(", "unlink(", "replace("):
        assert verb not in source, f"output_proof.py must not call {verb}"
    assert "read_bytes(" in source          # the only I/O verb it does use


def test_a_proof_result_is_not_content_shaped():
    proof = _prove(_honest_governance())
    as_dict = dataclasses.asdict(proof)
    assert set(as_dict) & CONTRACT_GOVERNANCE_KEYS == set()
    for value in as_dict.values():
        assert not isinstance(value, dict)
        if isinstance(value, tuple):
            assert all(isinstance(item, str) for item in value)
        else:
            assert type(value) in (bool, int, str)


def test_governance_proof_rejects_a_content_shaped_field():
    with pytest.raises(TypeError):
        GovernanceProof(ok=True, problems=(), partial=(),
                        comparisons_performed=11, comparisons_required=11,
                        report_sha256={"governance": {}},      # type: ignore
                        actual_source="sealed_artifact")


def test_problem_strings_never_carry_an_expected_value():
    """A failing proof must not hand a renderer the values it failed on."""
    mutations = (
        lambda g: g.pop("trial_id"),
        lambda g: g.update({"authorized_commit": "0" * 40}),
        lambda g: g.update({"engineering_seed": None}),
        lambda g: g.update({"frozen_hashes": {}}),
        lambda g: g.update({"registry_sequence_snapshot": SEQ + 1}),
        lambda g: g.update({"extra": 1}),
    )
    emitted: list[str] = []
    for fn in mutations:
        gov = _honest_governance()
        fn(gov)
        proof = _prove(gov)
        emitted.extend(proof.problems)
        emitted.extend(proof.partial)
    assert emitted
    for text in emitted:
        for value in EXPECTED_VALUES:
            assert value not in text, f"{text!r} leaks an expected value"


# ==========================================================================
# 9. the key set really is the contract's
# ==========================================================================

def test_contract_key_set_matches_the_report_allowlist():
    from itsf.s0 import report as rep
    assert CONTRACT_GOVERNANCE_KEYS == rep._GOVERNANCE_ALLOWED_KEYS


def test_contract_key_set_matches_the_contract_document():
    doc = (REPO / "S0_REPORT_CONTENT_CONTRACT.md").read_text(encoding="utf-8")
    row = [ln for ln in doc.splitlines()
           if ln.startswith("| A12 ") and "governance" in ln]
    assert len(row) == 1, "S0_REPORT_CONTENT_CONTRACT.md §A row A12 not found"
    a12 = row[0]
    for literal in ("trial_id", "authorized_commit", "engineering_seed"):
        assert literal in a12
    assert "七项" in a12              # 七项 — the seven-item restatement
    assert "registry" in a12                  # registry event-sequence snapshot
    assert op.CONTRACT_FROZEN_HASH_COUNT == 7


# ==========================================================================
# 10. honest coverage: PARTIAL is derived, and never moves the verdict
# ==========================================================================

def test_partial_coverage_is_derived_from_the_context():
    proof = _prove(_honest_governance())
    assert proof.ok is True                    # PARTIAL never weakens a pass
    assert set(proof.partial) == {
        "governance_proof_partial:snapshot_fact_absent_from_schema:"
        "registry_sha256",
        "governance_proof_partial:snapshot_fact_absent_from_schema:"
        "exact_authorization_text_sha256",
        "governance_proof_partial:engineering_seed_provenance_absent_from_schema",
    }


def test_partial_shrinks_when_the_snapshot_carries_no_extra_facts():
    lean = {"trial_id": TRIAL_ID, "authorized_commit": COMMIT,
            "event_sequence": SEQ}
    proof = _prove(_honest_governance(), _context(authorization_snapshot=lean))
    assert proof.ok is True
    assert proof.partial == (
        "governance_proof_partial:engineering_seed_provenance_absent_from_schema",)
