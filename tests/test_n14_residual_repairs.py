"""F02, F04 and F06/R1 -- the residual blockers, as FINAL OBSERVABLES.

The independent verification of the first remediation closed F01, F03, F05 and
F07 and left these three open. Each test below states what the repaired system
does at a boundary a consumer sees: the passes actually executed, the standing
the seal is handed, the seal's own refusal, the ledger's bytes.

The bound in every escalation test is the RULED one, read from
`contracts.aaron_ruled_methods().grid_policy.max_doublings` rather than written
here, so a test cannot quietly disagree with the authority it is checking.

Everything is synthetic: a fabricated bundle at B=2, K=2, a synthetic registry
chain and a synthetic DAY_STRATA supplement. No real MC runs.
"""
import dataclasses

import pytest

import test_mc_battery_boundary as BB
import test_mc_registry_parser as RP
from test_mc_grid_channel_b27 import (            # noqa: F401
    K_SMALL, OUT_ROOT, small_grid, wide, authority, supplement, _sha)
from itsf import contracts
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import grid_replay as gr
from itsf.mc import mc_contract as mcx
from itsf.mc import mc_runner as run

U2028 = " "


def _bound():
    return int(contracts.aaron_ruled_methods().grid_policy.max_doublings)


def _authorization(tmp_path, prepared):
    from itsf.mc.registry_boundary import resolve_registry
    reg = tmp_path / "TRIAL_REGISTRY.md"
    reg.write_text(RP.Reg().chain(RP.FULL[:5], commit=BB.COMMIT).text(),
                   encoding="utf-8")
    return run.bind_run_authorization(
        resolve_registry(reg), run_id=mcx.FIRST_RUN_ID,
        expected_commit=prepared.authorized_commit, output_root=OUT_ROOT,
        test_only=True)


def _run(wide, supplement, tmp_path):
    return run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))


class _Escalate:
    """Makes a chosen seed's comparison GENUINELY fail, by moving one cell.

    Nothing here touches a convergence flag. `run_grid_cell` is wrapped and one
    cell's Conservative P5 is pushed across the region boundary at chosen
    doubling levels, so the comparison computes the flip itself and the witness
    that records it is minted normally, digest and all.

    Perturbing {1} makes every comparison disagree -- the seed never converges.
    Perturbing {1, 2} makes attempt 0 (K vs 2K) disagree and attempt 1 (2K vs
    4K) agree, which is the authorized retry succeeding.
    """

    def __init__(self, monkeypatch, seeds, at_doublings):
        self.seeds = set(seeds)
        self.at = set(at_doublings)
        self.real = run._gc.run_grid_cell
        monkeypatch.setattr(run._gc, "run_grid_cell", self)

    def __call__(self, prepared, authority, supplement, *, q_mil, r_mil,
                 master_seed, B, doublings=0, **kw):
        cell = self.real(prepared, authority, supplement, q_mil=q_mil,
                         r_mil=r_mil, master_seed=master_seed, B=B,
                         doublings=doublings, **kw)
        if (master_seed not in self.seeds or doublings not in self.at
                or gr.is_infeasible(cell)
                or (q_mil, r_mil) != tuple(gr.GRID_CELL_KEYS[0])):
            return cell
        return gr.CellStatistics(
            conservative_p5={c: -abs(v) - 1000.0
                             for c, v in cell.conservative_p5.items()},
            stress_median=dict(cell.stress_median),
            feasible=dict(cell.feasible), identity=dict(cell.identity))


def _passes_run(monkeypatch):
    """Every (seed, doublings) the runner actually executes."""
    seen = []
    real = run._gc.run_grid_pass

    def spy(prepared, authority, supp, *, master_seed, B, doublings=0, **kw):
        seen.append((master_seed, doublings))
        return real(prepared, authority, supp, master_seed=master_seed, B=B,
                    doublings=doublings, **kw)

    monkeypatch.setattr(run._gc, "run_grid_pass", spy)
    return seen


# == F02 -- the bounded escalation, K -> 2K -> 4K and no further ===========

def test_F02_a_converged_seed_stops_at_K_and_2K(wide, supplement, tmp_path,
                                                monkeypatch):
    """The control, and the reason the escalation is an escalation: when the
    first authorized comparison converges, no second one runs."""
    seen = _passes_run(monkeypatch)
    result = _run(wide, supplement, tmp_path)
    assert result.grid_convergence.grid_converged is True
    assert {d for _s, d in seen} == {0, 1}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert result.grid_convergence.attempts_by_seed[seed] == 1


@pytest.mark.parametrize("victim", list(RESEARCH_BOOTSTRAP_SEEDS))
def test_F02_any_one_seed_can_independently_require_its_4K_attempt(
        wide, supplement, tmp_path, monkeypatch, victim):
    """Each governed seed escalates on its own account. The other two stop at
    2K, which is what makes the retry per-seed rather than a global mode."""
    seen = _passes_run(monkeypatch)
    _Escalate(monkeypatch, [victim], at_doublings={1, 2})
    result = _run(wide, supplement, tmp_path)
    standing = result.grid_convergence
    assert standing.attempts_by_seed[victim] == 2
    assert (victim, 2) in seen, "the 4K arm did not run for the victim"
    for other in RESEARCH_BOOTSTRAP_SEEDS:
        if other == victim:
            continue
        assert standing.attempts_by_seed[other] == 1
        assert (other, 2) not in seen
    # the retry converged, so the whole grid stands converged
    assert standing.grid_converged is True
    assert standing.final_k_by_seed[victim] == 2 * K_SMALL
    assert standing.final_k_doubled_by_seed[victim] == 4 * K_SMALL


def test_F02_every_seed_may_require_its_4K_attempt_at_once(
        wide, supplement, tmp_path, monkeypatch):
    seen = _passes_run(monkeypatch)
    _Escalate(monkeypatch, RESEARCH_BOOTSTRAP_SEEDS, at_doublings={1, 2})
    result = _run(wide, supplement, tmp_path)
    standing = result.grid_convergence
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert standing.attempts_by_seed[seed] == 2
        assert (seed, 2) in seen
    assert standing.grid_converged is True
    assert standing.doublings_executed == 2 == _bound()


def test_F02_still_non_converged_at_4K_stays_NON_CONVERGED(
        wide, supplement, tmp_path, monkeypatch):
    """A seed the authorized bound does not rescue keeps its verdict, and
    takes the cross-seed conjunction and H1 eligibility with it."""
    _Escalate(monkeypatch, [RESEARCH_BOOTSTRAP_SEEDS[1]], at_doublings={1})
    result = _run(wide, supplement, tmp_path)
    standing = result.grid_convergence
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]
    assert standing.attempts_by_seed[victim] == _bound()
    assert standing.converged_by_seed[victim] is False
    assert standing.grid_converged is False
    assert standing.grid_seal_status == "NON_CONVERGED"
    assert standing.may_support_h1_entry is False
    assert result.grid_seal_status == "NON_CONVERGED"
    assert result.may_support_h1_entry is False


def test_F02_nothing_runs_beyond_the_ruled_bound(wide, supplement, tmp_path,
                                                 monkeypatch):
    """No 8K. The bound is the ruled `max_doublings`, and the highest arm any
    seed reaches is one doubling above its last authorized base."""
    seen = _passes_run(monkeypatch)
    _Escalate(monkeypatch, RESEARCH_BOOTSTRAP_SEEDS, at_doublings={1})
    result = _run(wide, supplement, tmp_path)
    highest = max(d for _s, d in seen)
    assert highest == _bound(), highest
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert result.grid_convergence.attempts_by_seed[seed] == _bound()
    assert result.grid_convergence.doublings_executed == _bound()
    assert result.grid_convergence.max_doublings == _bound()


def test_F02_the_standing_consumes_each_seeds_FINAL_attempt(
        wide, supplement, tmp_path, monkeypatch):
    """The integration point. The chain records every attempt; the verdict is
    the last one's."""
    victim = RESEARCH_BOOTSTRAP_SEEDS[2]
    _Escalate(monkeypatch, [victim], at_doublings={1, 2})
    result = _run(wide, supplement, tmp_path)
    standing = gr.verify_grid_convergence(result.grid_convergence)
    assert len(standing.witness_chain_by_seed[victim]) == 2
    assert standing.converged_by_seed[victim] is True    # the FINAL attempt
    report = result.grid_evidence_by_seed[victim]
    assert report["attempts"] == 2
    assert report["converged_by_attempt"] == (False, True)


def test_F02_the_K_arm_still_binds_to_the_FIRST_attempt(
        wide, supplement, tmp_path, monkeypatch):
    """F01's seal path is untouched: the outer K arm is produced at the frozen
    scales, so it binds to the frozen-base attempt even when the base seed
    escalated."""
    _Escalate(monkeypatch, [mcc.BASE_MASTER_SEED], at_doublings={1, 2})
    result = _run(wide, supplement, tmp_path)
    section = result.seal_candidate["grid_section"]
    assert section["k"] == K_SMALL              # the frozen base arm
    assert section["k_doubled"] == 2 * K_SMALL
    assert section["attempts_by_seed"][str(mcc.BASE_MASTER_SEED)] == 2
    assert section["final_k_by_seed"][str(mcc.BASE_MASTER_SEED)] == 2 * K_SMALL


def test_F02_publication_still_uses_the_adjusted_maps(
        wide, supplement, tmp_path, monkeypatch):
    """F03 stays closed through the escalation: the published classes come
    from the FINAL attempt's comparison-adjusted map."""
    banded = {}
    real = gr.compare_region_maps

    def spy(kind, cells_at_k, cells_at_2k, *, k, k_doubled):
        out = real(kind, cells_at_k, cells_at_2k, k=k, k_doubled=k_doubled)
        key = gr.GRID_CELL_KEYS[0]
        adjusted = dict(out.map_at_k)
        adjusted[key] = gr.BOUNDARY_BAND
        banded[kind] = key
        return dataclasses.replace(out, map_at_k=adjusted)

    monkeypatch.setattr(gr, "compare_region_maps", spy)
    result = _run(wide, supplement, tmp_path)
    assert banded
    for kind, key in banded.items():
        assert result.published_region_by_kind[kind][key] == gr.BOUNDARY_BAND


def test_F02_an_attempt_after_a_converged_one_is_refused(wide, supplement,
                                                         small_grid):
    """The bound is not a budget. Rule (e) authorizes the retry only while a
    region has NOT converged, so a chain that continues past a convergence is
    a second opinion and is refused."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))

    def pass_(seed, doublings, p5=100.0):
        return gr.grid_pass_for_tests(
            auth, prepared_digest=auth.prepared_digest, master_seed=seed,
            doublings=doublings, B=2, channel=mcc.PRIMARY_THETA_CHANNEL,
            cells={key: gr.CellStatistics(conservative_p5={"c": p5},
                                          stress_median={"c": 50.0},
                                          feasible={"c": True})
                   for key in gr.GRID_CELL_KEYS})

    chains = {}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        first = gr.derive_k_replay_evidence(
            auth, master_seed=seed, cells_at_k=pass_(seed, 0),
            cells_at_2k=pass_(seed, 1))
        assert first.grid_converged is True
        second = gr.derive_k_replay_evidence(
            auth, master_seed=seed, k=2 * K_SMALL, k_doubled=4 * K_SMALL,
            cells_at_k=pass_(seed, 1), cells_at_2k=pass_(seed, 2))
        chains[seed] = (first, second)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.aggregate_k_replay_evidence(chains)
    assert ei.value.code == "grid_convergence_retry_after_convergence"


def test_F02_a_third_attempt_cannot_be_minted_at_all(wide, supplement,
                                                     small_grid):
    """Beyond the bound the evidence layer itself refuses: a base arm of 4K
    is not an authorized base arm."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))

    def pass_(doublings):
        return gr.grid_pass_for_tests(
            auth, prepared_digest=auth.prepared_digest, master_seed=7,
            doublings=doublings, B=2, channel=mcc.PRIMARY_THETA_CHANNEL,
            cells={key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                          stress_median={"c": 50.0},
                                          feasible={"c": True})
                   for key in gr.GRID_CELL_KEYS})

    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_k_replay_evidence(
            auth, master_seed=7, k=4 * K_SMALL, k_doubled=8 * K_SMALL,
            cells_at_k=pass_(2), cells_at_2k=pass_(3))
    assert ei.value.code == "grid_replay_k_per_seed_not_frozen"


# == F04 -- test-only grid evidence is never production seal-admissible ====

def _test_only_standing(wide, supplement):
    """A complete, genuine, TEST-ONLY standing: real passes, real witnesses,
    real aggregate -- everything except a production authority."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    assert auth.test_only is True

    def pass_(seed, doublings):
        return gr.grid_pass_for_tests(
            auth, prepared_digest=auth.prepared_digest, master_seed=seed,
            doublings=doublings, B=2, channel=mcc.PRIMARY_THETA_CHANNEL,
            cells={key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                          stress_median={"c": 50.0},
                                          feasible={"c": True})
                   for key in gr.GRID_CELL_KEYS})

    chains = {seed: (gr.derive_k_replay_evidence(
        auth, master_seed=seed, cells_at_k=pass_(seed, 0),
        cells_at_2k=pass_(seed, 1)),) for seed in RESEARCH_BOOTSTRAP_SEEDS}
    return chains, gr.aggregate_k_replay_evidence(chains)


def test_F04_a_test_only_standing_is_refused_at_the_public_seal(
        wide, supplement, tmp_path, small_grid):
    """THE hole the verifier found. The standing is CONVERGED with H1 support
    and it still may not seal a production prepared input -- recording the
    flag was a label, and this is the boundary."""
    chains, standing = _test_only_standing(wide, supplement)
    assert standing.grid_converged is True
    assert standing.may_support_h1_entry is True
    assert wide.test_only is False
    base = run._arm(wide, run_label="base", axis="base",
                    B=mcc.B_WORLDS_FROZEN, K=wide.k_per_seed,
                    seed=mcc.BASE_MASTER_SEED)
    doubled = {
        "B": run._arm(wide, run_label="double_B", axis="B",
                      B=2 * mcc.B_WORLDS_FROZEN, K=wide.k_per_seed,
                      seed=mcc.BASE_MASTER_SEED),
        "K": run._arm(wide, run_label="double_K", axis="K",
                      B=mcc.B_WORLDS_FROZEN, K=2 * wide.k_per_seed,
                      seed=mcc.BASE_MASTER_SEED)}
    seeds = {s: run._arm(wide, run_label="seed_%d" % s, axis="seed",
                         B=mcc.B_WORLDS_FROZEN, K=wide.k_per_seed, seed=s)
             for s in RESEARCH_BOOTSTRAP_SEEDS}
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.verdict_and_seal_from_evidence(
            wide, base=base, doubled_by_axis=doubled, seed_runs=seeds,
            k_witness=chains[mcc.BASE_MASTER_SEED][0],
            grid_convergence=standing)
    assert ei.value.code == "grid_evidence_test_only_at_production_seal"


def test_F04_mixed_genuine_and_test_only_evidence_is_refused(
        wide, supplement, small_grid):
    """A standing cannot be assembled half from each. The aggregate compares
    every witness's provenance against the first and refuses a disagreement,
    so a test-only witness can never hide inside a production standing."""
    auth_t = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    auth_p = gr.derive_grid_replay_authority(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    assert auth_t.test_only is True and auth_p.test_only is False
    assert auth_t.authority_digest != auth_p.authority_digest

    def witness(auth, seed):
        def pass_(doublings):
            return gr.grid_pass_for_tests(
                auth, prepared_digest=auth.prepared_digest, master_seed=seed,
                doublings=doublings, B=2,
                channel=mcc.PRIMARY_THETA_CHANNEL,
                cells={key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                              stress_median={"c": 50.0},
                                              feasible={"c": True})
                       for key in gr.GRID_CELL_KEYS})
        return gr.derive_k_replay_evidence(
            auth, master_seed=seed, cells_at_k=pass_(0), cells_at_2k=pass_(1))

    # the production authority refuses hand-built cells outright, which is
    # itself the point -- so a MIXED standing can only be attempted with two
    # test-only-constructible authorities of different provenance
    with pytest.raises(mcc.MCInputError) as ei:
        gr.grid_pass_for_tests(
            auth_p, prepared_digest=auth_p.prepared_digest, master_seed=7,
            doublings=0, B=2, channel=mcc.PRIMARY_THETA_CHANNEL, cells={})
    assert ei.value.code == "grid_pass_for_tests_requires_test_authority"

    # and a standing whose witnesses disagree on provenance is refused
    forged = witness(auth_t, RESEARCH_BOOTSTRAP_SEEDS[0])
    object.__setattr__(forged, "test_only", False)
    chains = {seed: (witness(auth_t, seed),)
              for seed in RESEARCH_BOOTSTRAP_SEEDS}
    chains[RESEARCH_BOOTSTRAP_SEEDS[0]] = (forged,)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.aggregate_k_replay_evidence(chains)
    assert ei.value.code == "k_replay_evidence_digest_mismatch"


def test_F04_genuine_production_grid_evidence_still_seals(wide, supplement,
                                                          tmp_path):
    """The control. The governed production authority produces evidence the
    seal accepts, so the refusal above is about provenance and not about
    breaking the path."""
    result = _run(wide, supplement, tmp_path)
    assert result.grid_convergence.test_only is False
    assert result.seal_candidate["grid_section"]["test_only"] is False
    assert result.seal_candidate["grid_section"]["status"] == "CONVERGED"
    assert result.sealed is True


def test_F04_the_test_only_construction_route_still_exists(wide, supplement,
                                                           small_grid):
    """It is required by tests and is not removed -- what changed is that it
    can no longer reach a production seal."""
    chains, standing = _test_only_standing(wide, supplement)
    assert standing.test_only is True
    assert gr.verify_grid_convergence(standing) is standing


def test_F04_provenance_protections_from_the_first_repair_still_hold(
        wide, supplement, small_grid):
    """The earlier F04 mechanisms are untouched: raw mappings are inadmissible
    and a mutated pass refuses."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    cells = {key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                    stress_median={"c": 50.0},
                                    feasible={"c": True})
             for key in gr.GRID_CELL_KEYS}
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_k_replay_evidence(auth, master_seed=7, cells_at_k=cells,
                                    cells_at_2k=cells)
    assert ei.value.code == "grid_pass_required"
    pass_ = gr.grid_pass_for_tests(
        auth, prepared_digest=auth.prepared_digest, master_seed=7,
        doublings=0, B=2, channel=mcc.PRIMARY_THETA_CHANNEL, cells=cells)
    swapped = dict(pass_.cells)
    swapped[gr.GRID_CELL_KEYS[0]] = gr.CellStatistics(
        conservative_p5={"c": 9e5}, stress_median={"c": 50.0},
        feasible={"c": True})
    object.__setattr__(pass_, "cells", swapped)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.verify_grid_pass(pass_)
    assert ei.value.code == "grid_pass_cells_mutated"


# == F06 / R1 -- nothing invalid reaches the physical write ================

def _ledger_with_hold(tmp_path):
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger = tmp_path / "TRIAL_REGISTRY.md"
    ledger.write_text(RP.Reg().text(), encoding="utf-8")
    commit = "a" * 40
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=commit,
                         utc_stamp="2026-09-12T00:00:00+00:00", path=ledger)
    rows = oc.parse_owner_rows(ledger.read_text(encoding="utf-8"))
    held = [r for r in rows if r.token == oc.OWNER_HOLD][-1]
    return ledger, held, commit


def test_R1_a_U2028_reason_is_refused_BEFORE_the_write(tmp_path):
    """The blocker, inverted. The bytes do not move and the ledger stays
    readable, which is the property a post-write check could never give."""
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger, held, commit = _ledger_with_hold(tmp_path)
    before = ledger.read_bytes()
    with pytest.raises(rb.AppendRefused) as ei:
        rb.append_owner_release(
            scope=oc.GLOBAL_SCOPE, reason="resume" + U2028 + "now",
            head_commit=commit, utc_stamp="2026-09-12T00:00:01+00:00",
            releases_event_sequence=held.seq, path=ledger)
    assert ei.value.code == "owner_append_reason_breaks_the_row"
    assert ledger.read_bytes() == before
    assert oc.parse_owner_rows(ledger.read_text(encoding="utf-8"))
    assert oc.active_holds(ledger.read_text(encoding="utf-8"), "MC-DS-S001")


def test_R1_the_forbidden_class_is_derived_from_the_splitter():
    """Not an enumerated list -- R1 is what an enumerated list costs. Every
    character `str.splitlines()` treats as a boundary is refused, which is the
    same primitive the registry parser splits on."""
    from itsf.mc import registry_boundary as rb
    assert U2028 in rb.LINE_BOUNDARY_CHARACTERS
    assert " " in rb.LINE_BOUNDARY_CHARACTERS
    assert "\x85" in rb.LINE_BOUNDARY_CHARACTERS
    assert {"|", ";"} <= rb.ROW_TEXT_FORBIDDEN
    for ch in rb.LINE_BOUNDARY_CHARACTERS:
        assert len(("a" + ch + "b").splitlines()) > 1, repr(ch)
    assert "a" not in rb.ROW_TEXT_FORBIDDEN


@pytest.mark.parametrize("kind", [
    "u2028", "u2029", "nel", "pipe", "semicolon", "empty_reason",
    "bad_commit", "bad_utc", "wrong_hold", "bad_scope",
])
def test_E_any_rejected_candidate_leaves_the_ledger_byte_identical(tmp_path,
                                                                   kind):
    """TASK E, as one property over every rejection this path can produce.

    A refusal that happens after the append is a different and much weaker
    property than a refusal that prevents one, and R1 is what the difference
    costs. Every case below must leave the file exactly as it was.
    """
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger, held, commit = _ledger_with_hold(tmp_path)
    before = ledger.read_bytes()
    kwargs = dict(scope=oc.GLOBAL_SCOPE, reason="resume",
                  head_commit=commit, utc_stamp="2026-09-12T00:00:01+00:00",
                  releases_event_sequence=held.seq, path=ledger)
    kwargs.update({
        "u2028": {"reason": "a" + U2028 + "b"},
        "u2029": {"reason": "a b"},
        "nel": {"reason": "a\x85b"},
        "pipe": {"reason": "a|b"},
        "semicolon": {"reason": "a;b"},
        "empty_reason": {"reason": "   "},
        "bad_commit": {"head_commit": "not-40-hex"},
        "bad_utc": {"utc_stamp": "2026-09-12T00:00:01Z"},
        "wrong_hold": {"releases_event_sequence": held.seq + 99},
        "bad_scope": {"scope": "NOT-A-RUN-ID-FAMILY"},
    }[kind])
    with pytest.raises(rb.AppendRefused):
        rb.append_owner_release(**kwargs)
    assert ledger.read_bytes() == before, "the rejected candidate moved bytes"
    # and the ledger is still readable and still holding
    assert oc.parse_owner_rows(ledger.read_text(encoding="utf-8"))
    assert oc.active_holds(ledger.read_text(encoding="utf-8"), "MC-DS-S001")


def test_E_a_failed_compare_and_swap_also_leaves_the_bytes_unchanged(
        tmp_path):
    """The CAS case, which is the one rejection that happens under the lock."""
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger, held, commit = _ledger_with_hold(tmp_path)

    real = rb._compare_and_append
    moved = {}

    def intervene(target, decided, addition):
        # somebody else commits between the decision and the append
        if not moved:
            moved["yes"] = True
            with open(target, "a", encoding="utf-8") as fh:
                fh.write("| 99 | 2026-09-12T00:00:09+00:00 | NOTE | %s | "
                         "builder | intervening |\n" % ("a" * 12))
        return real(target, decided, addition)

    rb._compare_and_append = intervene
    try:
        before = None
        with pytest.raises(rb.AppendRefused) as ei:
            before_bytes = ledger.read_bytes()
            before = before_bytes
            rb.append_owner_release(
                scope=oc.GLOBAL_SCOPE, reason="resume", head_commit=commit,
                utc_stamp="2026-09-12T00:00:01+00:00",
                releases_event_sequence=held.seq, path=ledger)
        assert ei.value.code == "p3_registry_changed_under_decision"
    finally:
        rb._compare_and_append = real
    # the owner row itself never landed
    text = ledger.read_text(encoding="utf-8")
    assert "OWNER_RELEASE" not in text
    assert oc.active_holds(text, "MC-DS-S001")


def test_F06_the_legitimate_governed_release_still_works(tmp_path):
    """The positive path, end to end: actor, hold identity, CAS, integrity and
    the downstream hold state."""
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger, held, commit = _ledger_with_hold(tmp_path)
    assert oc.active_holds(ledger.read_text(encoding="utf-8"), "MC-DS-S001")
    row = rb.append_owner_release(
        scope=oc.GLOBAL_SCOPE, reason="resume", head_commit=commit,
        utc_stamp="2026-09-12T00:00:01+00:00",
        releases_event_sequence=held.seq, path=ledger)
    text = ledger.read_text(encoding="utf-8")
    assert row in text
    assert "| Aaron |" in row                       # the owner actor cell
    assert "releases_event_sequence: %d" % held.seq in row
    rows = oc.parse_owner_rows(text)
    assert any(r.token == oc.OWNER_RELEASE and r.releases == held.seq
               for r in rows)
    assert not oc.active_holds(text, "MC-DS-S001")  # downstream state moved


def test_F06_the_generic_writer_still_refuses_OWNER_RELEASE(tmp_path):
    """The first repair is not traded away by the second."""
    from itsf.mc import registry_boundary as rb
    ledger, held, _commit = _ledger_with_hold(tmp_path)
    before = ledger.read_bytes()
    release = ("| 9 | 2026-09-12T00:00:01+00:00 | OWNER_RELEASE | %s | Aaron "
               "| [GLOBAL] releases_event_sequence: %d; reason: go |"
               % ("a" * 12, held.seq))
    with pytest.raises(rb.AppendRefused) as ei:
        rb.serialized_append(ledger, (release + "\n").encode("utf-8"),
                             decided=before)
    assert ei.value.code == "generic_append_refuses_permission_event"
    assert ledger.read_bytes() == before
