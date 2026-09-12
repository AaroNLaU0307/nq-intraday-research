"""F02, the B half -- every governed seed runs its OWN {B, 2B}.

The K half of frozen F02 was repaired first: per seed, K -> 2K -> if the
comparison fails, one bounded retry to 4K. The B half survived both repairs.
M10 quantifier (b) reads "B 加倍同样三 seeds 各做（3×{B,2B} 全量）… (b) 跨 seed
判定类别一致在基础档与加倍档都成立", and the runner built a `double_B` arm for
the base seed alone. Seeds 13 and 31 ran base B and nothing else, so the
doubled-scale half of rule (b) had no evidence to evaluate -- it could not
fail, and so it never did.

Every test below asserts a FINAL OBSERVABLE: the arms the runner actually
requests, the coverage the returned `RunnerResult` reports, the seal's own
refusal, the seal payload. Where a convergence failure has to be created it is
COMPUTED, never flagged: one perturbation is applied to the single atom
producer both the forward run and the cold replay call, keyed on a seed and on
world indices that exist only because of the doubling, and the production
reducer, verdict and convergence rules decide the consequence themselves.

Everything is synthetic: a fabricated bundle at B=2, K=2, a synthetic registry
chain and a synthetic DAY_STRATA supplement. No real MC runs and no number
below is a research result.
"""
import dataclasses

import pytest

import test_mc_battery_boundary as BB                      # noqa: F401
from test_mc_grid_channel_b27 import (                     # noqa: F401
    K_SMALL, OUT_ROOT, small_grid, wide, authority, supplement, _sha)
from test_n14_residual_repairs import _Escalate, _authorization, _passes_run
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import mc_runner as run


def _go(wide, supplement, tmp_path):
    return run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))


def _arm_log(monkeypatch):
    """Every (run_label, master_seed, B) a FULL arm asked for.

    `run_epistemic` is the only producer of a full MC arm, so its call log IS
    the arm schedule -- not a restatement of it kept beside the code.
    """
    seen = []
    real = run._mcc.run_epistemic

    def spy(prepared, **kw):
        seen.append((kw["run_label"], kw["master_seed"], kw["B"]))
        return real(prepared, **kw)

    monkeypatch.setattr(run._mcc, "run_epistemic", spy)
    return seen


def _scales(log):
    """master_seed -> the set of B scales that seed ran a full arm at."""
    by_seed = {}
    for _label, seed, b in log:
        by_seed.setdefault(seed, set()).add(b)
    return by_seed


class _DropDoubled:
    """Removes ONE seed's doubled-B arm on the way into the real seal.

    Nothing is stubbed: the runner produces every arm for real and the
    genuine `verdict_and_seal_from_evidence` runs. One entry of one mapping
    is deleted, which is exactly the state the tree was in before this
    repair, and the refusal is the production one.
    """

    def __init__(self, monkeypatch, seed):
        self.seed = seed
        self.real = run._mcc.verdict_and_seal_from_evidence
        monkeypatch.setattr(run._mcc, "verdict_and_seal_from_evidence", self)

    def __call__(self, prepared, *, seed_doubled_runs, **kw):
        short = {s: r for s, r in seed_doubled_runs.items()
                 if s != self.seed}
        return self.real(prepared, seed_doubled_runs=short, **kw)


class _ShiftDoubledWorlds:
    """Moves one seed's result, in the worlds that exist only at 2B.

    `_run_path_atom` is THE single lifecycle executor -- the forward run and
    the cold replay both call it -- so a perturbation keyed on (master_seed,
    world_index) is self-consistent across both and the replay agrees. A base
    arm at B has world indices 0..B-1; the doubled arm has 0..2B-1. Touching
    only index >= B therefore touches only that seed's DOUBLED arm, which is
    what "a failure visible only at 2B" means.
    """

    def __init__(self, monkeypatch, seed, *, base_b, delta=5000.0):
        self.seed, self.base_b, self.delta = seed, base_b, delta
        self.real = mcc._run_path_atom
        monkeypatch.setattr(mcc, "_run_path_atom", self)

    def __call__(self, prepared, **kw):
        atom = self.real(prepared, **kw)
        if kw["master_seed"] != self.seed or kw["world_index"] < self.base_b:
            return atom
        return dataclasses.replace(
            atom,
            monthly_prop_operating_ev=atom.monthly_prop_operating_ev
            + self.delta)


class _CaptureReport:
    """Keeps the ConvergenceReport the PRODUCTION path computed.

    Convergence returns its report and the seal refuses afterwards, so the
    real object is observable even on a run that does not seal -- which is
    better than recomputing it here from captured arms, because a
    recomputation is a second opinion rather than the one that decided.
    """

    def __init__(self, monkeypatch):
        self.report = None
        real = mcc.convergence_from_evidence

        def spy(*a, **kw):
            self.report = real(*a, **kw)
            return self.report

        monkeypatch.setattr(mcc, "convergence_from_evidence", spy)


# == 1-2: every governed seed requests B, and its OWN 2B ===================

def test_B_every_governed_seed_requests_the_base_B_arm(wide, supplement,
                                                       tmp_path, monkeypatch):
    log = _arm_log(monkeypatch)
    _go(wide, supplement, tmp_path)
    by_seed = _scales(log)
    base_b = min(b for _l, _s, b in log)
    assert set(by_seed) >= set(RESEARCH_BOOTSTRAP_SEEDS)
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert base_b in by_seed[seed], "seed %s never ran a base-B arm" % seed


def test_B_every_governed_seed_requests_its_OWN_doubled_arm(
        wide, supplement, tmp_path, monkeypatch):
    """The finding, inverted. Before the repair this was true of the base
    seed alone and the other two governed seeds ran base B only."""
    log = _arm_log(monkeypatch)
    _go(wide, supplement, tmp_path)
    by_seed = _scales(log)
    base_b = min(b for _l, _s, b in log)
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert 2 * base_b in by_seed[seed], (
            "seed %s has no doubled-B arm" % seed)
        # and it is that seed's own arm, not a share of another seed's
        mine = [row for row in log if row[1] == seed and row[2] == 2 * base_b]
        assert mine, seed
        assert len({row[0] for row in mine}) == 1, mine


def test_B_the_result_reports_the_coverage_it_actually_ran(wide, supplement,
                                                           tmp_path):
    """A FINAL OBSERVABLE. The missing arms were invisible on the returned
    object, which is part of why they survived two repairs and a green
    suite."""
    result = _go(wide, supplement, tmp_path)
    assert set(result.b_scales_by_seed) == set(RESEARCH_BOOTSTRAP_SEEDS)
    scales = set(result.b_scales_by_seed.values())
    assert len(scales) == 1, "the seeds do not share one {B, 2B} pair"
    at_b, at_2b = scales.pop()
    assert at_2b == 2 * at_b
    assert {"seed_13_double_B", "seed_31_double_B"} <= set(result.arm_labels)


def test_B_the_seal_records_every_seeds_doubled_arm(wide, supplement,
                                                    tmp_path):
    """Requirement 8: the cross-seed standing consumes all B/2B results, and
    the seal says so rather than implying it."""
    seal = _go(wide, supplement, tmp_path).seal_candidate
    recorded = seal["convergence_evidence"]["seed_doubled_b_runs"]
    assert set(recorded) == {str(s) for s in RESEARCH_BOOTSTRAP_SEEDS}
    base_b = min(int(v["B"]) for v in recorded.values()) // 2
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        row = recorded[str(seed)]
        assert row["master_seed"] == seed        # nobody inherited an arm
        assert row["B"] == 2 * base_b
    scales = seal["convergence_evidence"]["seeds_agree_by_scale"]
    assert set(scales) == {"base", "doubled"}
    assert scales["base"] is True and scales["doubled"] is True


# == 3-5: a missing 2B arm refuses, for EVERY seed ========================

@pytest.mark.parametrize("seed", list(RESEARCH_BOOTSTRAP_SEEDS))
def test_B_a_missing_doubled_arm_refuses_for_any_seed(seed, wide, supplement,
                                                      tmp_path, monkeypatch):
    """Requirements 3, 4 and 5 -- and the base seed is one of the three,
    deliberately: the repair must not leave a privileged seed behind."""
    _DropDoubled(monkeypatch, seed)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "seed_doubled_b_set_violation"
    assert str(seed) in str(ei.value)


def test_B_no_doubled_evidence_at_all_refuses(wide, supplement, tmp_path,
                                              monkeypatch):
    """The parameter has a default, so absence has to refuse rather than pass
    silently -- an optional arm would BE the defect being repaired."""
    real = run._mcc.verdict_and_seal_from_evidence

    def drop_all(prepared, *, seed_doubled_runs, **kw):
        return real(prepared, seed_doubled_runs=None, **kw)

    monkeypatch.setattr(run._mcc, "verdict_and_seal_from_evidence", drop_all)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "seed_doubled_b_evidence_absent"


def test_B_a_seed_may_not_inherit_another_seeds_doubled_arm(
        wide, supplement, tmp_path, monkeypatch):
    """The set check alone would pass if one seed's arm were filed under
    three keys, and the other two seeds would still be unmeasured."""
    real = run._mcc.verdict_and_seal_from_evidence
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]

    def share(prepared, *, seed_doubled_runs, **kw):
        one = seed_doubled_runs[RESEARCH_BOOTSTRAP_SEEDS[0]]
        shared = {s: (one if s == victim else r)
                  for s, r in seed_doubled_runs.items()}
        return real(prepared, seed_doubled_runs=shared, **kw)

    monkeypatch.setattr(run._mcc, "verdict_and_seal_from_evidence", share)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "seed_doubled_b_seed_mismatch"


# == 6-7: a doubled-scale-only failure reaches the final standing ==========

@pytest.mark.parametrize("seed", list(RESEARCH_BOOTSTRAP_SEEDS[1:]))
def test_B_a_failure_visible_only_at_2B_affects_the_final_standing(
        seed, wide, supplement, tmp_path, monkeypatch):
    """Requirements 6 and 7, for the two seeds that had no doubled arm at
    all before this repair.

    The perturbation lands only on world indices that exist because of the
    doubling, so the seed's BASE arm is untouched and every other seed is
    untouched. Nothing asserts a category or sets a flag: the production
    reducer computes the statistic, the production verdict computes the
    category, and rule (b)'s doubled-scale half computes the disagreement.
    """
    seen = _CaptureReport(monkeypatch)
    _ShiftDoubledWorlds(monkeypatch, seed, base_b=mcc.B_WORLDS_FROZEN)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "main_channel_not_converged"

    # and WHICH half failed, read off the report the production path itself
    # produced: the base tier still agrees, the doubled tier does not.
    report = seen.report
    assert report is not None
    assert report.seeds_agree_by_scale["base"] is True
    assert report.seeds_agree_by_scale["doubled"] is False
    assert report.category_same_across_seeds is False
    assert report.converged is False


def test_B_the_base_seeds_doubled_arm_still_carries_rule_a(
        wide, supplement, tmp_path, monkeypatch):
    """The base seed's doubled arm is the ratified `double_B`; perturbing its
    extra worlds must still break rule (a), which is a different rule from
    (b) and is not traded for it."""
    _ShiftDoubledWorlds(monkeypatch, mcc.BASE_MASTER_SEED,
                        base_b=mcc.B_WORLDS_FROZEN)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "main_channel_not_converged"


# == 9: the B -> 2B prefix semantics are unchanged =========================

def test_B_a_redrawn_doubled_arm_refuses_for_a_non_base_seed(
        wide, supplement, tmp_path, monkeypatch):
    """Requirement 9. The content witness that has always guarded the base
    seed's doubling now guards every seed's: a genuine B doubling EXTENDS
    that seed's world table, it does not redraw it. The builder is patched
    for one (seed, B) pair so the doubled arm's first B worlds differ."""
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]
    real = mcc.build_world_table

    def redraw(prepared, *, channel, B, master_seed):
        table = real(prepared, channel=channel, B=B, master_seed=master_seed)
        if master_seed == victim and B == 2 * mcc.B_WORLDS_FROZEN:
            return tuple(reversed(tuple(table)))
        return table

    monkeypatch.setattr(mcc, "build_world_table", redraw)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "b_doubling_world_prefix_violation"


def test_B_the_prefix_relation_actually_holds_on_every_seed(wide, supplement,
                                                            tmp_path,
                                                            monkeypatch):
    """The positive half of the same property, stated on the real arms: each
    seed's doubled arm reuses that seed's own base worlds verbatim as its
    first B, so the check above is passing on substance rather than on an
    absent comparand."""
    by_label = {}
    real = run._arm

    def spy(prepared, **kw):
        ev = real(prepared, **kw)
        by_label[kw["run_label"]] = ev
        return ev

    monkeypatch.setattr(run, "_arm", spy)
    _go(wide, supplement, tmp_path)
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        at_base = by_label["seed_%d" % seed]
        at_double = by_label[
            "double_B" if seed == mcc.BASE_MASTER_SEED
            else "seed_%d_double_B" % seed]
        mcc._check_b_doubling_world_prefix(at_base, at_double)


# == 10: there is no 4B, and no further B escalation =======================

def test_B_no_arm_runs_beyond_the_single_doubling(wide, supplement, tmp_path,
                                                  monkeypatch):
    """Requirement 10. M10 names {B, 2B}; nothing in the frozen authority
    escalates B further, so nothing here invents a 4B arm."""
    log = _arm_log(monkeypatch)
    _go(wide, supplement, tmp_path)
    base_b = min(b for _l, _s, b in log)
    assert sorted({b for _l, _s, b in log}) == [base_b, 2 * base_b]


def test_B_a_4B_arm_is_refused_rather_than_tolerated(wide, supplement,
                                                     tmp_path, monkeypatch):
    """And generosity is refused too: an arm at 4B is not "more evidence",
    it is an arm the frozen authority never authorised."""
    real = run._mcc.verdict_and_seal_from_evidence
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]

    def quadruple(prepared, *, seed_doubled_runs, **kw):
        over = dict(seed_doubled_runs)
        over[victim] = dataclasses.replace(over[victim],
                                           B=4 * mcc.B_WORLDS_FROZEN)
        return real(prepared, seed_doubled_runs=over, **kw)

    monkeypatch.setattr(run._mcc, "verdict_and_seal_from_evidence", quadruple)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    # the outer/inner binding is checked first and catches the lie about the
    # scale; either way a 4B claim cannot reach the rules.
    assert ei.value.code in {"seed_doubled_b_scale_violation",
                             "run_evidence_inner_mismatch:B"}


# == 11: the K half is untouched ==========================================

def test_B_the_K_escalation_still_runs_and_still_stops_at_the_bound(
        wide, supplement, tmp_path, monkeypatch):
    """Requirement 11, stated on the passes the runner actually executed:
    a seed that fails K vs 2K still takes its authorized 2K vs 4K retry, and
    still stops there. The B repair adds arms to the MAIN channel; the K
    escalation is the GRID channel and neither borrows from the other."""
    seen = _passes_run(monkeypatch)
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]
    _Escalate(monkeypatch, {victim}, {1})          # never converges
    _go(wide, supplement, tmp_path)
    attempts = sorted(d for s, d in seen if s == victim)
    assert attempts == [0, 1, 1, 2], attempts
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        if seed != victim:
            assert sorted(d for s, d in seen if s == seed) == [0, 1]


def test_B_the_two_doubling_axes_do_not_share_a_bound(wide, supplement,
                                                      tmp_path, monkeypatch):
    """The K axis escalates conditionally up to a ruled bound; the B axis is
    a flat {B, 2B} for every seed. Confusing them is the one mistake this
    repair could have made, so it is asserted rather than assumed."""
    epistemic = _arm_log(monkeypatch)
    passes = _passes_run(monkeypatch)
    _go(wide, supplement, tmp_path)
    base_b = min(b for _l, _s, b in epistemic)
    # B: exactly two scales, every seed, no conditionality
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert _scales(epistemic)[seed] == {base_b, 2 * base_b}
    # K: one attempt each, because nothing here fails to converge
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert sorted(d for s, d in passes if s == seed) == [0, 1]
