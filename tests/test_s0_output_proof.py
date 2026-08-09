"""Tests for itsf.s0.output_proof — the sealed RUN DIRECTORY, as read on disk.

Hermetic and fully synthetic: no real archive, no registry, no run, no clock.
Every fixture is built in-memory from the constants below and then WRITTEN into
a pytest `tmp_path` run directory, because the module under test now accepts
one input mode only — the bytes that landed.

The suite is organised around the four measured failures the module exists to
avoid (see its docstring):

  F-a  the check must run AFTER the sealed bytes exist and parse THOSE;
  F-b  the expected side must not be a mirror of the target, and the pass must
       come from real, counted comparisons;
  F-c  the expected domain must not shrink when the guarded object shrinks;
  F-d  (M6.1.7) the verdict must be about the FILES, not about the `dict` the
       renderer was about to write — at HEAD 185e47f7 nine of the ten
       `sealed_files` digests disagreed with the bytes on disk, and an
       in-memory verdict could not see it.

The synthetic run directory deliberately mirrors HEAD's shape: 8 MC_HANDOFF
JSONL artifacts + HANDOFF_ADMISSION.json + S0_REPORT.md = 10 sealed entries,
plus the self-excluded S0_REPORT.json = 11 artifacts, plus 2 run-infrastructure
files the renderer did not produce.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from itsf.s0 import output_proof as op
from itsf.s0.output_proof import (CONTRACT_GOVERNANCE_KEYS, DraftScreen,
                                  FINAL_REPORT_NAME, GovernanceProof,
                                  ProofRefused, REFUSAL_CLASSES,
                                  REFUSAL_DECLARED_BYTES_MISMATCH,
                                  REFUSAL_DECLARED_FILE_MISSING,
                                  REFUSAL_DECLARED_SHA256_MISMATCH,
                                  REFUSAL_DISK_EXTRA_FILE,
                                  REFUSAL_MANIFEST_MISSING,
                                  REFUSAL_REPORT_MISSING, SourceContext,
                                  prove_governance, screen_governance_draft)

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
    # (scripts/s0_real_run.py:2339-2364)
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

# --------------------------------------------------------------------------
# synthetic run directory (HEAD's shape)
# --------------------------------------------------------------------------
ENGINES = ("E1", "E2")
SCENARIOS = ("Base", "Conservative", "Stress", "Severe")

# What runner.py writes that the RENDERER did not produce.
INFRA = ("manifest.jsonl", "REGISTRY_AFTER_RUN_STARTED.json")


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


def _artifact_bodies() -> dict[str, str]:
    """The ten artifacts the renderer produces BESIDES the final report, in
    the same byte shapes production uses: multi-line "\\n".join JSONL bodies,
    a single-line canonical-JSON admission record, a multi-line markdown."""
    bodies: dict[str, str] = {}
    for eng in ENGINES:
        for scn in SCENARIOS:
            bodies[f"MC_HANDOFF_{eng}_{scn}.jsonl"] = "\n".join(
                json.dumps({"engine": eng, "cost_scenario": scn, "i": i},
                           sort_keys=True) for i in range(3))
    # dumps_canonical -> no indent -> a single line, so newline translation is
    # a no-op on this one file. That asymmetry is exactly why HEAD is 9-of-10
    # broken rather than 10-of-10.
    bodies["HANDOFF_ADMISSION.json"] = json.dumps(
        {"admitted": [], "withheld": {"SEED_MANIFEST.json": "synthetic"}},
        sort_keys=True)
    bodies["S0_REPORT.md"] = "\n".join(
        ["# SYNTHETIC S0 FORMAL REPORT", "", "- formal payload: S0_REPORT.json"])
    return bodies


def _entry(body: str) -> dict:
    raw = body.encode("utf-8")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def _report_text(governance: dict, sealed: dict, self_excluded) -> str:
    """A synthetic FINAL S0_REPORT.json body: the governance block plus the
    manifest section the renderer injects at s0_real_run.py:1050-1057."""
    payload = {
        "governance": governance,
        "era_axis": {"note": "synthetic"},
        "mc_handoff_manifest": {
            "files": {}, "sealed_files": sealed,
            "self_excluded": self_excluded},
    }
    return json.dumps(payload, sort_keys=True, indent=1, allow_nan=False)


def _same_length_forgery(original: bytes) -> bytes:
    """Flip one byte to a DIFFERENT value, keeping the length identical — the
    only tamper a byte-count check cannot see."""
    head = b"!" if original[:1] != b"!" else b"?"
    return head + original[1:]


def _write(path: Path, text: str, newline: str = "\n") -> None:
    """Write with an EXPLICIT newline convention. `newline="\\r\\n"` reproduces,
    deterministically and on any platform, what runner.py's text-mode
    `Path.write_text` does on Windows."""
    body = text if newline == "\n" else text.replace("\n", newline)
    path.write_bytes(body.encode("utf-8"))


def _build_run(base: Path, *, governance=None, self_excluded=None,
               sealed_mutator=None, disk_mutator=None, skip_files=(),
               extra_disk=(), write_infra=True, newline="\n",
               report_text=None) -> Path:
    """Materialise a synthetic sealed run directory and return the path of its
    S0_REPORT.json.

    The manifest is ALWAYS declared from the LF bodies (production hashes
    `body.encode("utf-8")`), while `newline` controls what actually lands on
    disk — so the honest case and the CRLF defect differ by one argument.
    """
    run = base / "runs" / TRIAL_ID
    run.mkdir(parents=True, exist_ok=True)
    bodies = _artifact_bodies()
    sealed = {name: _entry(body) for name, body in sorted(bodies.items())}
    if sealed_mutator is not None:
        sealed_mutator(sealed)
    excluded = [FINAL_REPORT_NAME] if self_excluded is None else self_excluded
    text = (_report_text(_honest_governance() if governance is None
                         else governance, sealed, excluded)
            if report_text is None else report_text)
    for name, body in bodies.items():
        if name in skip_files:
            continue
        _write(run / name, body, newline)
    if FINAL_REPORT_NAME not in skip_files:
        _write(run / FINAL_REPORT_NAME, text, newline)
    if write_infra:
        for name in INFRA:
            _write(run / name, '{"synthetic": true}\n', newline)
    for name in extra_disk:
        _write(run / name, "planted\n", newline)
    if disk_mutator is not None:
        disk_mutator(run)
    return run / FINAL_REPORT_NAME


def _prove(base: Path, context: SourceContext | None = None,
           infrastructure=INFRA, **kw) -> GovernanceProof:
    report = _build_run(base, **kw)
    return prove_governance(context or _context(), report_path=report,
                            infrastructure_files=infrastructure)


def _gov_prove(base: Path, governance: dict,
               context: SourceContext | None = None) -> GovernanceProof:
    """Governance-axis convenience: an otherwise honest run directory whose
    only defect is the governance block handed in."""
    return _prove(base, context, governance=governance)


# ==========================================================================
# 1. the honest case — and HEAD's arithmetic, verified rather than asserted
# ==========================================================================

def test_honest_on_disk_run_passes(tmp_path):
    proof = _prove(tmp_path)
    assert proof.ok is True
    assert proof.problems == ()
    assert proof.actual_source == "file"
    # governance: 4 top-level scalars + 7 frozen-hash leaves, all compared
    assert proof.comparisons_required == 11
    assert proof.comparisons_performed == 11
    # sealed set: 10 declared files x (exists, bytes, sha256)
    assert proof.sealed_files_declared == 10
    assert proof.disk_checks_required == 30
    assert proof.disk_checks_performed == 30
    # 11 artifacts + 2 infrastructure files
    assert proof.run_dir_entries_seen == 13


def test_the_self_exclusion_arithmetic_matches_head(tmp_path):
    """HEAD's numbers, DERIVED here instead of trusted: the renderer writes
    N artifacts, declares N-1 of them, and the one it does not declare is
    S0_REPORT.json (it carries the manifest, so it cannot hash itself)."""
    report = _build_run(tmp_path)
    run = report.parent
    on_disk = {p.name for p in run.iterdir()} - set(INFRA)
    declared = set(json.loads(report.read_bytes().decode("utf-8"))
                   ["mc_handoff_manifest"]["sealed_files"])
    assert len(on_disk) == 11
    assert len(declared) == 10
    assert on_disk - declared == {FINAL_REPORT_NAME}
    assert FINAL_REPORT_NAME not in declared


def test_report_sha256_is_the_hash_of_the_bytes_on_disk(tmp_path):
    report = _build_run(tmp_path)
    proof = prove_governance(_context(), report_path=report,
                             infrastructure_files=INFRA)
    assert proof.report_sha256 == hashlib.sha256(
        report.read_bytes()).hexdigest()


# ==========================================================================
# 2. F-d: the six named sealed-set failure classes
# ==========================================================================

def test_the_six_refusal_classes_are_distinct_and_deterministic():
    assert len(REFUSAL_CLASSES) == 6
    assert len(set(REFUSAL_CLASSES)) == 6
    assert REFUSAL_CLASSES == (
        "governance_proof_report_missing",
        "governance_proof_manifest_missing",
        "governance_proof_declared_file_missing",
        "governance_proof_disk_extra_file",
        "governance_proof_declared_bytes_mismatch",
        "governance_proof_declared_sha256_mismatch")
    # no class is a prefix of another, so `startswith` filtering is unambiguous
    for a in REFUSAL_CLASSES:
        assert sum(b.startswith(a) for b in REFUSAL_CLASSES) == 1


def test_refusal_class_1_report_missing(tmp_path):
    """The report file is not there at all — no honest verdict exists, so this
    class is a ProofRefused rather than an ok=False proof."""
    missing = tmp_path / "runs" / TRIAL_ID / FINAL_REPORT_NAME
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), report_path=missing,
                         infrastructure_files=INFRA)
    assert REFUSAL_REPORT_MISSING in str(exc.value)


def test_refusal_class_1_report_present_but_empty(tmp_path):
    report = _build_run(tmp_path)
    report.write_bytes(b"   \n")
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), report_path=report,
                         infrastructure_files=INFRA)
    assert REFUSAL_REPORT_MISSING in str(exc.value)


def test_refusal_class_2_manifest_missing(tmp_path):
    no_section = json.dumps({"governance": _honest_governance()},
                            sort_keys=True, indent=1)
    proof = _prove(tmp_path / "a", report_text=no_section)
    assert proof.ok is False
    assert (f"{REFUSAL_MANIFEST_MISSING}:mc_handoff_manifest"
            in proof.problems)

    def _drop(sealed):
        sealed.clear()

    empty = _prove(tmp_path / "b", sealed_mutator=_drop)
    assert empty.ok is False
    assert (f"{REFUSAL_MANIFEST_MISSING}:mc_handoff_manifest.sealed_files"
            in empty.problems)


def test_refusal_class_3_declared_file_missing(tmp_path):
    proof = _prove(tmp_path, skip_files=("S0_REPORT.md",))
    assert proof.ok is False
    assert (f"{REFUSAL_DECLARED_FILE_MISSING}:"
            "mc_handoff_manifest.sealed_files[S0_REPORT.md]") in proof.problems
    # the two checks that could not run are visible in the count
    assert proof.disk_checks_performed == 28
    assert proof.disk_checks_required == 30
    assert "governance_proof_disk_check_count" in proof.problems


def test_refusal_class_4_disk_extra_file(tmp_path):
    proof = _prove(tmp_path, extra_disk=("PLANTED_EXTRA.json",))
    assert proof.ok is False
    assert (f"{REFUSAL_DISK_EXTRA_FILE}:run_dir[PLANTED_EXTRA.json]"
            in proof.problems)
    assert proof.run_dir_entries_seen == 14


def test_refusal_class_5_declared_bytes_mismatch(tmp_path):
    def _grow(run):
        _write(run / "S0_REPORT.md",
               (run / "S0_REPORT.md").read_bytes().decode("utf-8") + "\nextra")

    proof = _prove(tmp_path, disk_mutator=_grow)
    assert proof.ok is False
    assert (f"{REFUSAL_DECLARED_BYTES_MISMATCH}:"
            "mc_handoff_manifest.sealed_files[S0_REPORT.md]") in proof.problems
    # all three checks still RAN — a wrong file is compared, not skipped
    assert proof.disk_checks_performed == 30


def test_refusal_class_6_declared_sha256_mismatch(tmp_path):
    """Same byte COUNT, different bytes: only the digest can catch this, so it
    proves the two classes are genuinely independent checks."""
    def _swap(run):
        target = run / "S0_REPORT.md"
        original = target.read_bytes()
        forged = _same_length_forgery(original)
        assert len(forged) == len(original) and forged != original
        target.write_bytes(forged)

    proof = _prove(tmp_path, disk_mutator=_swap)
    assert proof.ok is False
    node = "mc_handoff_manifest.sealed_files[S0_REPORT.md]"
    assert f"{REFUSAL_DECLARED_SHA256_MISMATCH}:{node}" in proof.problems
    assert f"{REFUSAL_DECLARED_BYTES_MISMATCH}:{node}" not in proof.problems
    assert proof.disk_checks_performed == 30


def test_every_refusal_class_is_reachable_and_uniquely_identified(tmp_path):
    """One observation per class, collected in one place: each class is
    produced by a different defect and no two defects produce the same code."""
    observed: dict[str, str] = {}

    missing = tmp_path / "none" / FINAL_REPORT_NAME
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), report_path=missing,
                         infrastructure_files=INFRA)
    observed[REFUSAL_REPORT_MISSING] = str(exc.value)

    cases = {
        REFUSAL_MANIFEST_MISSING:
            dict(sealed_mutator=lambda s: s.clear()),
        REFUSAL_DECLARED_FILE_MISSING:
            dict(skip_files=("HANDOFF_ADMISSION.json",)),
        REFUSAL_DISK_EXTRA_FILE:
            dict(extra_disk=("PLANTED.txt",)),
        REFUSAL_DECLARED_BYTES_MISMATCH:
            dict(disk_mutator=lambda r: _write(r / "S0_REPORT.md", "short")),
        REFUSAL_DECLARED_SHA256_MISMATCH:
            dict(disk_mutator=lambda r: (r / "S0_REPORT.md").write_bytes(
                _same_length_forgery((r / "S0_REPORT.md").read_bytes()))),
    }
    for i, (code, kwargs) in enumerate(sorted(cases.items())):
        first = _prove(tmp_path / f"c{i}a", **kwargs)
        second = _prove(tmp_path / f"c{i}b", **kwargs)
        assert first.problems == second.problems, f"{code} is not deterministic"
        hits = [p for p in first.problems if p.split(":", 1)[0] == code]
        assert hits, f"{code} not produced by its own defect"
        observed[code] = hits[0]
        assert first.ok is False
    assert set(observed) == set(REFUSAL_CLASSES)


# ==========================================================================
# 3. F-d: HEAD's actual defect — CRLF write-out
# ==========================================================================

def test_crlf_written_artifacts_are_caught(tmp_path):
    """The HEAD 185e47f7 defect, reproduced: the manifest hashes LF bodies, the
    runner writes them in text mode, and on Windows nine of the ten sealed
    files land as CRLF. An in-memory verdict cannot see this; the disk proof
    fails on exactly those nine."""
    proof = _prove(tmp_path, newline="\r\n")
    assert proof.ok is False

    def _names(code):
        return {p.split("[", 1)[1][:-1] for p in proof.problems
                if p.startswith(code + ":")}

    translated = {n for n, b in _artifact_bodies().items() if "\n" in b}
    assert len(translated) == 9
    assert "HANDOFF_ADMISSION.json" not in translated
    assert _names(REFUSAL_DECLARED_SHA256_MISMATCH) == translated
    assert _names(REFUSAL_DECLARED_BYTES_MISMATCH) == translated
    # the GOVERNANCE axis is untouched — CRLF is whitespace to a JSON parser,
    # so this failure is attributable to the sealed-set axis alone
    assert proof.comparisons_performed == proof.comparisons_required == 11
    assert not any(p.startswith(("governance_proof_value_mismatch",
                                 "governance_proof_type_mismatch",
                                 "governance_proof_key_missing"))
                   for p in proof.problems)


# ==========================================================================
# 4. the in-memory route can never be a production acceptance
# ==========================================================================

def test_the_in_memory_route_is_refused_by_prove_governance(tmp_path):
    report = _build_run(tmp_path)
    artifacts = {FINAL_REPORT_NAME: report.read_bytes().decode("utf-8")}
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), sealed_artifacts=artifacts)
    assert "sealed_artifacts" in str(exc.value)
    # even WITH a valid report_path alongside it, the poison pill wins
    with pytest.raises(ProofRefused):
        prove_governance(_context(), report_path=report,
                         infrastructure_files=INFRA,
                         sealed_artifacts=artifacts)


def test_the_draft_screen_cannot_yield_a_production_grade_pass(tmp_path):
    report = _build_run(tmp_path)
    artifacts = {"S0_REPORT.md": "# synthetic",
                 FINAL_REPORT_NAME: report.read_bytes().decode("utf-8")}
    screen = screen_governance_draft(_context(), draft_artifacts=artifacts)
    assert isinstance(screen, DraftScreen)
    assert not isinstance(screen, GovernanceProof)
    # it DID do its job — the governance block is clean ...
    assert screen.blocking_problems == ()
    assert screen.comparisons_performed == screen.comparisons_required == 11
    # ... and it still cannot be read as an acceptance
    assert screen.acceptance == "not_an_acceptance:disk_proof_required"
    assert "ok" not in {f.name for f in dataclasses.fields(screen)}
    with pytest.raises(ProofRefused):
        screen.ok
    with pytest.raises(TypeError):
        bool(screen)
    if screen.blocking_problems:                 # the SUPPORTED gate shape
        raise AssertionError("unreachable on an honest draft")


def test_a_governance_proof_can_only_exist_for_bytes_read_off_disk():
    """The structural invariant: `actual_source` is enforced, not documented,
    so `isinstance(x, GovernanceProof)` implies the disk was read."""
    with pytest.raises(ValueError):
        GovernanceProof(ok=True, problems=(), partial=(),
                        comparisons_performed=11, comparisons_required=11,
                        disk_checks_performed=30, disk_checks_required=30,
                        sealed_files_declared=10, run_dir_entries_seen=13,
                        report_sha256="0" * 64,
                        actual_source="sealed_artifact")


def test_the_draft_screen_still_refuses_to_run_before_the_report_exists():
    early = {"S0_REPORT.md": "# md", "HANDOFF_ADMISSION.json": "{}"}
    with pytest.raises(ProofRefused) as exc:
        screen_governance_draft(_context(), draft_artifacts=early)
    assert FINAL_REPORT_NAME in str(exc.value)
    with pytest.raises(ProofRefused):
        screen_governance_draft(_context(),
                                draft_artifacts={FINAL_REPORT_NAME: "  "})
    with pytest.raises(ProofRefused):
        screen_governance_draft(_context(), draft_artifacts=None)
    with pytest.raises(ProofRefused):
        screen_governance_draft({"trial_id": TRIAL_ID},
                                draft_artifacts={FINAL_REPORT_NAME: "{}"})


def test_the_draft_screen_catches_a_wrong_governance_block_before_write():
    gov = _honest_governance()
    gov["trial_id"] = "S0-TOTHER"
    text = _report_text(gov, {}, [FINAL_REPORT_NAME])
    screen = screen_governance_draft(
        _context(), draft_artifacts={FINAL_REPORT_NAME: text})
    assert ("governance_proof_value_mismatch:governance.trial_id"
            in screen.blocking_problems)


# ==========================================================================
# 5. self-exclusion is preserved, and re-adding the report is refused
# ==========================================================================

def test_self_exclusion_is_preserved_on_an_honest_run(tmp_path):
    proof = _prove(tmp_path)
    assert proof.ok is True
    # the report is on disk, is NOT declared, and is NOT an "extra file"
    assert not any(FINAL_REPORT_NAME in p for p in proof.problems)
    assert proof.run_dir_entries_seen - len(INFRA) == (
        proof.sealed_files_declared + 1)


def test_declaring_the_report_inside_its_own_manifest_is_refused(tmp_path):
    def _add_self(sealed):
        sealed[FINAL_REPORT_NAME] = {"sha256": "0" * 64, "bytes": 1}

    proof = _prove(tmp_path, sealed_mutator=_add_self)
    assert proof.ok is False
    assert ("governance_proof_self_exclusion_violated:"
            f"mc_handoff_manifest.sealed_files[{FINAL_REPORT_NAME}]"
            in proof.problems)
    # and it is NOT quietly honoured as an eleventh declaration
    assert proof.sealed_files_declared == 10


def test_a_dropped_self_exclusion_declaration_is_refused(tmp_path):
    proof = _prove(tmp_path, self_excluded=[])
    assert proof.ok is False
    assert ("governance_proof_self_exclusion_violated:"
            "mc_handoff_manifest.self_excluded") in proof.problems
    wrong = _prove(tmp_path / "b", self_excluded=["S0_REPORT.md"])
    assert wrong.ok is False
    assert ("governance_proof_self_exclusion_violated:"
            "mc_handoff_manifest.self_excluded") in wrong.problems


# ==========================================================================
# 6. manifest self-consistency is NOT sufficient
# ==========================================================================

def test_manifest_self_consistency_is_not_sufficient(tmp_path):
    """A tamperer who edits an artifact AND rewrites its manifest entry to
    match produces a run directory whose sealed-set axis is perfectly clean.
    It is still caught, because the governance axis's expected side never came
    from the report."""
    forged_body = "# FORGED\n\n- tampered"
    tampered_gov = _honest_governance()
    tampered_gov["registry_sequence_snapshot"] = SEQ + 1

    def _relabel(sealed):
        sealed["S0_REPORT.md"] = _entry(forged_body)

    def _rewrite(run):
        _write(run / "S0_REPORT.md", forged_body)

    proof = _prove(tmp_path, governance=tampered_gov,
                   sealed_mutator=_relabel, disk_mutator=_rewrite)
    # the sealed-set axis sees nothing wrong: declaration == disk, everywhere
    assert proof.disk_checks_performed == proof.disk_checks_required == 30
    assert not any(p.split(":", 1)[0] in REFUSAL_CLASSES
                   for p in proof.problems)
    # ... and the proof fails anyway, on the independent axis
    assert proof.ok is False
    assert ("governance_proof_value_mismatch:"
            "governance.registry_sequence_snapshot") in proof.problems


def test_a_self_consistent_governance_tamper_is_still_caught(tmp_path):
    """The M6.1.6 case, re-run on disk: rewriting governance AND the report's
    own embedded hash of it yields an internally consistent report that the
    proof still rejects."""
    tampered = _honest_governance()
    victim = FROZEN_PATHS[3]
    tampered["frozen_hashes"] = dict(tampered["frozen_hashes"])
    tampered["frozen_hashes"][victim] = hashlib.sha256(b"forged").hexdigest()

    bodies = _artifact_bodies()
    sealed = {n: _entry(b) for n, b in sorted(bodies.items())}
    payload = json.loads(_report_text(tampered, sealed, [FINAL_REPORT_NAME]))
    payload["mc_handoff_manifest"]["governance_block_sha256"] = hashlib.sha256(
        json.dumps(tampered, sort_keys=True).encode("utf-8")).hexdigest()
    text = json.dumps(payload, sort_keys=True, indent=1, allow_nan=False)

    proof = _prove(tmp_path, report_text=text)
    parsed = json.loads((tmp_path / "runs" / TRIAL_ID / FINAL_REPORT_NAME)
                        .read_bytes().decode("utf-8"))
    # the report on disk agrees with itself ...
    assert (parsed["mc_handoff_manifest"]["governance_block_sha256"]
            == hashlib.sha256(json.dumps(parsed["governance"], sort_keys=True)
                              .encode("utf-8")).hexdigest())
    assert proof.ok is False
    assert (f"governance_proof_value_mismatch:governance.frozen_hashes[{victim}]"
            in proof.problems)


# ==========================================================================
# 7. F-c on BOTH axes: the expected domain never shrinks with the guarded
#    object
# ==========================================================================

def test_emptying_the_manifest_does_not_empty_the_disk_domain(tmp_path):
    """The sealed-set axis IS sized from the guarded object, so it is guarded
    from the other side: the file universe comes from the directory."""
    proof = _prove(tmp_path, sealed_mutator=lambda s: s.clear())
    assert proof.ok is False
    assert proof.disk_checks_required == 0
    extras = {p for p in proof.problems
              if p.startswith(REFUSAL_DISK_EXTRA_FILE + ":")}
    assert len(extras) == 10          # every artifact but the self-excluded one
    assert not any(FINAL_REPORT_NAME in p for p in extras)


def test_deleting_an_actual_path_does_not_shrink_the_expected_domain(tmp_path):
    gov = _honest_governance()
    victim = FROZEN_PATHS[0]
    gov["frozen_hashes"] = {k: v for k, v in gov["frozen_hashes"].items()
                            if k != victim}
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert (f"governance_proof_key_missing:governance.frozen_hashes[{victim}]"
            in proof.problems)
    assert proof.comparisons_required == 11        # unchanged by the deletion
    assert proof.comparisons_performed == 10


def test_emptying_frozen_hashes_entirely_still_expects_seven(tmp_path):
    gov = _honest_governance()
    gov["frozen_hashes"] = {}
    proof = _gov_prove(tmp_path, gov)
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
# 8. the five governance divergence classes, each with its own code
# ==========================================================================

def test_missing_key_fails(tmp_path):
    gov = _honest_governance()
    del gov["authorized_commit"]
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert "governance_proof_key_missing:governance.authorized_commit" in \
        proof.problems
    assert proof.comparisons_performed == 10
    assert proof.comparisons_required == 11


def test_extra_key_fails(tmp_path):
    gov = _honest_governance()
    gov["approved_by"] = "someone"
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert "governance_proof_key_unexpected:governance.approved_by" in \
        proof.problems


def test_wrong_type_fails(tmp_path):
    gov = _honest_governance()
    gov["engineering_seed"] = str(SEED)          # "19750102", not 19750102
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert "governance_proof_type_mismatch:governance.engineering_seed" in \
        proof.problems
    assert proof.comparisons_performed == 11


def test_wrong_value_fails(tmp_path):
    gov = _honest_governance()
    gov["trial_id"] = "S0-TOTHER"
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert "governance_proof_value_mismatch:governance.trial_id" in \
        proof.problems


def test_unexpected_null_fails(tmp_path):
    gov = _honest_governance()
    gov["registry_sequence_snapshot"] = None
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert ("governance_proof_null_value:governance.registry_sequence_snapshot"
            in proof.problems)
    assert not any(p.startswith("governance_proof_key_missing")
                   for p in proof.problems)


def test_bool_does_not_satisfy_an_int_expectation(tmp_path):
    gov = _honest_governance()
    gov["registry_sequence_snapshot"] = True
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert ("governance_proof_type_mismatch:"
            "governance.registry_sequence_snapshot") in proof.problems


def test_each_divergence_class_has_its_own_deterministic_string(tmp_path):
    def mutate(tag, fn):
        gov = _honest_governance()
        fn(gov)
        return _gov_prove(tmp_path / tag, gov).problems

    cases = {
        "missing": lambda g: g.pop("trial_id"),
        "extra": lambda g: g.update({"zzz": 1}),
        "type": lambda g: g.update({"trial_id": 7}),
        "value": lambda g: g.update({"trial_id": "S0-TOTHER"}),
        "null": lambda g: g.update({"trial_id": None}),
    }
    seen = {}
    for name, fn in cases.items():
        first, second = mutate(f"{name}1", fn), mutate(f"{name}2", fn)
        assert first == second, f"{name} problem strings are not deterministic"
        seen[name] = tuple(p for p in first
                           if not p.endswith("comparison_count"))
    codes = [problems[0].split(":", 1)[0] for problems in seen.values()]
    assert len(set(codes)) == len(codes), f"codes collided: {codes}"


def test_unparsable_and_non_object_reports_fail(tmp_path):
    bad = _prove(tmp_path / "a", report_text="{not json")
    assert bad.ok is False
    assert "governance_proof_report_unparsable" in bad.problems
    arr = _prove(tmp_path / "b", report_text="[1, 2]")
    assert arr.ok is False
    assert "governance_proof_report_root_not_object" in arr.problems
    none = _prove(tmp_path / "c", report_text="{}")
    assert none.ok is False
    assert "governance_proof_section_missing" in none.problems
    # an unparsable report cannot yield a sealed-set verdict either
    assert f"{REFUSAL_MANIFEST_MISSING}:mc_handoff_manifest" not in bad.problems
    assert bad.disk_checks_required == 0


# ==========================================================================
# 9. F-b: the pass is a real comparison, the expected side is independent
# ==========================================================================

def test_comparison_count_is_derived_not_hardcoded(tmp_path):
    three = {p: _digest(p) for p in FROZEN_PATHS[:3]}
    ctx = _context(frozen_hash_authority=three,
                   frozen_hash_observations=dict(three))
    gov = _honest_governance()
    gov["frozen_hashes"] = dict(three)
    proof = _prove(tmp_path, ctx, governance=gov)
    assert proof.comparisons_required == 7        # 4 scalars + 3 hashes
    assert proof.comparisons_performed == 7
    # ... but a 3-item restatement is not what the contract fixes at seven
    assert "governance_proof_context_frozen_hash_count" in proof.problems
    assert proof.ok is False


def test_authority_observation_conflict_is_a_problem(tmp_path):
    """The expected side is TWO derivations (freeze registry + on-disk re-hash);
    a disagreement is surfaced, never silently resolved."""
    victim = FROZEN_PATHS[2]
    obs = {p: _digest(p) for p in FROZEN_PATHS}
    obs[victim] = hashlib.sha256(b"mutated-on-disk").hexdigest()
    proof = _prove(tmp_path, _context(frozen_hash_observations=obs))
    assert proof.ok is False
    assert ("governance_proof_context_observation_conflict:"
            f"governance.frozen_hashes[{victim}]") in proof.problems


def test_missing_and_extra_observations_are_problems(tmp_path):
    obs = {p: _digest(p) for p in FROZEN_PATHS[:-1]}
    obs["SYNTH_UNREGISTERED.md"] = hashlib.sha256(b"x").hexdigest()
    proof = _prove(tmp_path, _context(frozen_hash_observations=obs))
    assert proof.ok is False
    assert ("governance_proof_context_observation_missing:"
            f"governance.frozen_hashes[{FROZEN_PATHS[-1]}]") in proof.problems
    assert ("governance_proof_context_observation_extra:"
            "governance.frozen_hashes[SYNTH_UNREGISTERED.md]") in proof.problems


# ==========================================================================
# 10. the deliberate registry-moved failure
# ==========================================================================

def test_registry_moved_between_pre_run_snapshot_and_compute_fails(tmp_path):
    """RealChain.compute() re-reads the registry (scripts/s0_real_run.py:2305)
    while the expectation comes from the PRE-RUN snapshot. An event inserted in
    between MUST fail the proof — that is correct behaviour."""
    gov = _honest_governance()
    gov["registry_sequence_snapshot"] = SEQ + 1          # one event appeared
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert ("governance_proof_value_mismatch:"
            "governance.registry_sequence_snapshot") in proof.problems


def test_re_signed_authorization_between_snapshot_and_compute_fails(tmp_path):
    gov = _honest_governance()
    gov["authorized_commit"] = "0" * 40                  # re-authorized commit
    proof = _gov_prove(tmp_path, gov)
    assert proof.ok is False
    assert "governance_proof_value_mismatch:governance.authorized_commit" in \
        proof.problems


# ==========================================================================
# 11. F-a: refusals — the proof cannot run before the artifacts are on disk
# ==========================================================================

def test_calling_the_proof_before_the_files_are_on_disk_is_refused(tmp_path):
    """The whole run directory does not exist yet — this is the mid-render
    call site the M6.1.6 wiring used."""
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(),
                         report_path=tmp_path / "runs" / TRIAL_ID /
                         FINAL_REPORT_NAME,
                         infrastructure_files=INFRA)
    assert REFUSAL_REPORT_MISSING in str(exc.value)
    # ... and an empty placeholder is not "close enough" either
    run = tmp_path / "runs" / TRIAL_ID
    run.mkdir(parents=True)
    (run / FINAL_REPORT_NAME).write_bytes(b"")
    with pytest.raises(ProofRefused):
        prove_governance(_context(), report_path=run / FINAL_REPORT_NAME,
                         infrastructure_files=INFRA)


def test_a_report_written_before_its_siblings_does_not_pass(tmp_path):
    """Report on disk, artifacts not yet — a verdict IS possible (the report
    exists), and it is a failing one, per declared file."""
    proof = _prove(tmp_path, skip_files=tuple(_artifact_bodies()))
    assert proof.ok is False
    missing = [p for p in proof.problems
               if p.startswith(REFUSAL_DECLARED_FILE_MISSING + ":")]
    assert len(missing) == 10
    assert proof.disk_checks_performed == 10
    assert proof.disk_checks_required == 30


def test_refused_when_pointed_at_anything_but_the_final_report(tmp_path):
    """An evidence mirror copy is never the authority."""
    report = _build_run(tmp_path)
    mirror = report.parent / "EVIDENCE_S0_REPORT_COPY.json"
    mirror.write_bytes(report.read_bytes())
    with pytest.raises(ProofRefused) as exc:
        prove_governance(_context(), report_path=mirror,
                         infrastructure_files=INFRA)
    assert FINAL_REPORT_NAME in str(exc.value)


def test_refused_on_bad_wiring(tmp_path):
    report = _build_run(tmp_path)
    ctx = _context()
    with pytest.raises(ProofRefused):
        prove_governance(ctx)                                    # nothing
    with pytest.raises(ProofRefused):
        prove_governance(ctx, infrastructure_files=INFRA)        # no path
    with pytest.raises(ProofRefused):
        prove_governance({"trial_id": TRIAL_ID}, report_path=report,
                         infrastructure_files=INFRA)             # not a context


def test_infrastructure_declaration_is_required_and_validated(tmp_path):
    report = _build_run(tmp_path)
    ctx = _context()
    with pytest.raises(ProofRefused) as exc:
        prove_governance(ctx, report_path=report)                # forgotten
    assert "infrastructure_files" in str(exc.value)
    for bad in ("manifest.jsonl",                     # a bare string
                (FINAL_REPORT_NAME,),                 # the report itself
                ("../escape.json",),                  # not inside the run dir
                ("sub/dir.json",), ("",), (7,), (None,)):
        with pytest.raises(ProofRefused):
            prove_governance(ctx, report_path=report,
                             infrastructure_files=bad)
    # an EXPLICIT empty declaration stays expressible — and then the two real
    # infrastructure files are extras, which is the honest reading
    strict = prove_governance(ctx, report_path=report, infrastructure_files=())
    assert strict.ok is False
    assert {p for p in strict.problems
            if p.startswith(REFUSAL_DISK_EXTRA_FILE + ":")} == {
        f"{REFUSAL_DISK_EXTRA_FILE}:run_dir[{name}]" for name in INFRA}


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
# 12. a hostile manifest never reaches the filesystem, and is never skipped
# ==========================================================================

def test_a_path_traversal_declaration_is_refused_before_any_path_join(tmp_path):
    outside = tmp_path / "SECRET.json"
    outside.write_bytes(b"never read")

    def _escape(sealed):
        sealed["../SECRET.json"] = _entry("never read")

    proof = _prove(tmp_path, sealed_mutator=_escape)
    assert proof.ok is False
    assert any(p.startswith("governance_proof_manifest_entry_unsafe_name:")
               for p in proof.problems)
    # the escaping name is never treated as a declared, checkable file
    assert proof.sealed_files_declared == 10
    assert proof.disk_checks_required == 30
    # and its literal never appears in a problem string (positional reporting)
    assert not any("SECRET" in p for p in proof.problems)


def test_a_malformed_entry_is_a_problem_not_a_skipped_check(tmp_path):
    def _wreck(sealed):
        sealed["S0_REPORT.md"] = {"sha256": "0" * 64}          # no `bytes`
        sealed["HANDOFF_ADMISSION.json"] = {"sha256": "nothex", "bytes": 3}

    proof = _prove(tmp_path, sealed_mutator=_wreck)
    assert proof.ok is False
    for name in ("S0_REPORT.md", "HANDOFF_ADMISSION.json"):
        assert ("governance_proof_manifest_entry_malformed:"
                f"mc_handoff_manifest.sealed_files[{name}]") in proof.problems
    assert proof.sealed_files_declared == 8
    # the two files are still ACCOUNTED for on disk — one defect, one problem
    assert not any(p.startswith(REFUSAL_DISK_EXTRA_FILE + ":")
                   for p in proof.problems)


def test_a_non_string_manifest_key_is_reported_positionally(tmp_path):
    text = _report_text(_honest_governance(),
                        {n: _entry(b) for n, b in _artifact_bodies().items()},
                        [FINAL_REPORT_NAME])
    # json.dumps would stringify an int key, so inject it after parsing
    payload = json.loads(text)
    payload["mc_handoff_manifest"]["sealed_files"]["7"] = {
        "sha256": "0" * 64, "bytes": 0}
    proof = _prove(tmp_path, report_text=json.dumps(payload, sort_keys=True,
                                                    indent=1))
    assert proof.ok is False
    assert (f"{REFUSAL_DECLARED_FILE_MISSING}:"
            "mc_handoff_manifest.sealed_files[7]") in proof.problems


# ==========================================================================
# 13. structural: this module cannot be used to GENERATE anything
# ==========================================================================

def test_the_module_exposes_no_generator_entry_point():
    assert op.__all__ == (
        "FINAL_REPORT_NAME", "MANIFEST_SECTION", "SEALED_FILES_KEY",
        "SELF_EXCLUDED_KEY", "CONTRACT_GOVERNANCE_KEYS",
        "CONTRACT_FROZEN_HASH_COUNT", "SEALED_ENTRY_KEYS",
        "REFUSAL_REPORT_MISSING", "REFUSAL_MANIFEST_MISSING",
        "REFUSAL_DECLARED_FILE_MISSING", "REFUSAL_DISK_EXTRA_FILE",
        "REFUSAL_DECLARED_BYTES_MISMATCH", "REFUSAL_DECLARED_SHA256_MISMATCH",
        "REFUSAL_CLASSES", "ProofRefused", "SourceContext", "GovernanceProof",
        "DraftScreen", "prove_governance", "screen_governance_draft",
        # F-2 key-claims release gate (S0 closeout, Aaron ruling 2026-08-10):
        # a deliberate main-agent interface extension — checker surface only.
        "KEY_CLAIM_IDS", "ResearchClaimsContext", "KeyClaimsReport",
        "verify_key_claims")
    public = {name: getattr(op, name) for name in dir(op)
              if not name.startswith("_")}
    # the expected-tree builder is not reachable under any public name
    assert not any(value is op._expected_tree for value in public.values())
    # the only public callables this module DEFINES (bar the dataclasses and
    # the exception, which are types) are the two checkers
    callables = {n for n, v in public.items()
                 if callable(v) and not isinstance(v, type)
                 and getattr(v, "__module__", None) == op.__name__}
    assert callables == {"prove_governance", "screen_governance_draft",
                         "verify_key_claims"}
    # and no public name advertises production of content
    assert not any(n.startswith(("build_", "make_", "render_", "generate_",
                                 "emit_", "patch_", "fix_", "write_", "to_"))
                   for n in public)


def test_the_module_contains_no_filesystem_write_call():
    source = Path(op.__file__).read_text(encoding="utf-8")
    for verb in ("write_text(", "write_bytes(", "open(", "json.dump(",
                 "shutil.", "mkdir(", "unlink(", "replace("):
        assert verb not in source, f"output_proof.py must not call {verb}"
    # the ENTIRE I/O vocabulary, and every member of it is read-only
    assert {"read_bytes(", "is_file(", "is_symlink(", "iterdir("} <= {
        v for v in ("read_bytes(", "is_file(", "is_symlink(", "iterdir(")
        if v in source}
    for verb in ("rename(", "touch(", "rmdir(", "chmod(", "symlink_to("):
        assert verb not in source, f"output_proof.py must not call {verb}"


def test_a_proof_result_is_not_content_shaped(tmp_path):
    proof = _prove(tmp_path)
    as_dict = dataclasses.asdict(proof)
    assert set(as_dict) & CONTRACT_GOVERNANCE_KEYS == set()
    for value in as_dict.values():
        assert not isinstance(value, dict)
        if isinstance(value, tuple):
            assert all(isinstance(item, str) for item in value)
        else:
            assert type(value) in (bool, int, str)


def test_both_result_types_reject_a_content_shaped_field():
    with pytest.raises(TypeError):
        GovernanceProof(ok=True, problems=(), partial=(),
                        comparisons_performed=11, comparisons_required=11,
                        disk_checks_performed=30, disk_checks_required=30,
                        sealed_files_declared=10, run_dir_entries_seen=13,
                        report_sha256={"governance": {}},      # type: ignore
                        actual_source="file")
    with pytest.raises(TypeError):
        DraftScreen(blocking_problems=({"governance": {}},),   # type: ignore
                    partial=(), comparisons_performed=11,
                    comparisons_required=11, draft_sha256="0" * 64,
                    acceptance="not_an_acceptance:disk_proof_required")


def test_problem_strings_never_carry_an_expected_value(tmp_path):
    """A failing proof must not hand a renderer the values it failed on —
    including any sha256 it just compared."""
    mutations = (
        lambda g: g.pop("trial_id"),
        lambda g: g.update({"authorized_commit": "0" * 40}),
        lambda g: g.update({"engineering_seed": None}),
        lambda g: g.update({"frozen_hashes": {}}),
        lambda g: g.update({"registry_sequence_snapshot": SEQ + 1}),
        lambda g: g.update({"extra": 1}),
    )
    emitted: list[str] = []
    for i, fn in enumerate(mutations):
        gov = _honest_governance()
        fn(gov)
        proof = _gov_prove(tmp_path / f"m{i}", gov)
        emitted.extend(proof.problems)
        emitted.extend(proof.partial)
    # ... and the same discipline on the sealed-set axis
    disk = _prove(tmp_path / "disk", newline="\r\n")
    emitted.extend(disk.problems)
    assert emitted
    for text in emitted:
        for value in EXPECTED_VALUES:
            assert value not in text, f"{text!r} leaks an expected value"
        assert len(text.splitlines()) == 1, f"{text!r} is not a single line"


# ==========================================================================
# 14. the key set really is the contract's
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


def test_the_manifest_section_names_match_the_renderer():
    """The three manifest names this module reads are the three the renderer
    writes at scripts/s0_real_run.py:1050-1057."""
    src = (REPO / "scripts" / "s0_real_run.py").read_text(encoding="utf-8")
    assert f'formal["{op.MANIFEST_SECTION}"] = {{' in src
    assert f'"{op.SEALED_FILES_KEY}": {{' in src
    assert f'"{op.SELF_EXCLUDED_KEY}": ["{FINAL_REPORT_NAME}"]' in src
    assert op.SEALED_ENTRY_KEYS == frozenset({"sha256", "bytes"})


# ==========================================================================
# 15. honest coverage: PARTIAL is derived, and never moves the verdict
# ==========================================================================

def test_partial_coverage_is_derived_from_the_context(tmp_path):
    proof = _prove(tmp_path)
    assert proof.ok is True                    # PARTIAL never weakens a pass
    assert set(proof.partial) == {
        "governance_proof_partial:snapshot_fact_absent_from_schema:"
        "registry_sha256",
        "governance_proof_partial:snapshot_fact_absent_from_schema:"
        "exact_authorization_text_sha256",
        "governance_proof_partial:engineering_seed_provenance_absent_from_schema",
        # the sealed-set axis ran, so its honest limit is disclosed with it
        "governance_proof_partial:"
        "sealed_file_declaration_not_bound_to_an_external_authority",
    }


def test_partial_shrinks_when_the_snapshot_carries_no_extra_facts(tmp_path):
    lean = {"trial_id": TRIAL_ID, "authorized_commit": COMMIT,
            "event_sequence": SEQ}
    proof = _prove(tmp_path, _context(authorization_snapshot=lean))
    assert proof.ok is True
    assert proof.partial == (
        "governance_proof_partial:engineering_seed_provenance_absent_from_schema",
        "governance_proof_partial:"
        "sealed_file_declaration_not_bound_to_an_external_authority")


def test_the_sealed_set_partial_disappears_when_that_axis_did_not_run(tmp_path):
    """DERIVED, not hand-listed: no sealed-set claim, no sealed-set caveat.
    The marker qualifies a claim; when there is no claim it is absent."""
    unbound = "sealed_file_declaration_not_bound_to_an_external_authority"
    ran = _prove(tmp_path / "ok")
    assert any(unbound in p for p in ran.partial)
    none = _prove(tmp_path / "empty", sealed_mutator=lambda s: s.clear())
    assert none.disk_checks_required == 0
    assert not any(unbound in p for p in none.partial)
    # and a screen, which cannot run that axis at all, never carries it
    text = _report_text(_honest_governance(), {}, [FINAL_REPORT_NAME])
    screen = screen_governance_draft(
        _context(), draft_artifacts={FINAL_REPORT_NAME: text})
    assert not any(unbound in p for p in screen.partial)
