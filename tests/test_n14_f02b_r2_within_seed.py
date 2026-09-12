"""F02-B / R2 -- a seed's doubled arm is measured against ITS OWN base arm.

Every governed seed got its own {B, 2B} arms in the previous repair, and then
rule (c) compared all three doubled arms against ONE reference: the base seed's
base-B arm. That answers "how far does this seed sit from seed 7", which is a
cross-seed question and already rule (b)'s job. The question a doubled arm
exists to answer is "did THIS seed stop moving when it got twice the worlds",
and nothing was asking it.

The verifier's reproduction, in the units the tolerance is written in:

    seed 7  reference   -100
    seed 13   B = -120       |-120 - (-100)| = 20   within tolerance
    seed 13  2B =  -80       | -80 - (-100)| = 20   within tolerance
                             | -80 - (-120)| = 40   NOT within tolerance

Both arms look fine against seed 7 and the seed has plainly not stabilised.

TWO LEVELS, KEPT SEPARATE. Within-seed B-stability is rule (c), per seed,
against that seed's own base-B arm. Cross-seed agreement is rule (b), computed
afterwards from the categories. Neither substitutes for the other and a failure
of one is not hidden by the other -- which is exactly what the tests below
assert, since a shared baseline let rule (b) be the only thing that ever
noticed.

Every test asserts a FINAL OBSERVABLE: the runner's own refusal, and the
ConvergenceReport the production path computed. Where a drift has to exist it
is COMPUTED: one perturbation is applied to the single lifecycle executor that
both the forward run and the cold replay call, keyed on a seed and on world
indices, and the production reducer and rules decide the consequence.

Everything is synthetic: a fabricated bundle at B=2, K=2, a synthetic registry
chain and a synthetic DAY_STRATA supplement. No real MC runs and no number
below is a research result.
"""
import dataclasses

import pytest

import test_mc_battery_boundary as BB                      # noqa: F401
from test_mc_grid_channel_b27 import (                     # noqa: F401
    K_SMALL, OUT_ROOT, small_grid, wide, authority, supplement, _sha)
from test_n14_residual_repairs import _authorization
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import mc_runner as run

#: The trap, in this fixture's units. `flat` moves every world of the chosen
#: seed, so its BASE arm and its DOUBLED arm move together and both stay
#: inside the $25 tolerance of the base seed's arm. `extra` moves only the
#: worlds that exist because of the doubling, so it separates the two arms
#: from EACH OTHER by more than the tolerance while leaving both within it of
#: seed 7. Chosen just inside the boundary on purpose: 24.9 < 25 < 26.
TRAP_FLAT, TRAP_EXTRA = -24.9, 26.0


class _Shift:
    """Moves one seed's atoms: `flat` on every world, `extra` only on the
    worlds that exist because of the doubling.

    `_run_path_atom` is THE single lifecycle executor -- the forward run and
    the cold replay both call it -- so a perturbation keyed on (master_seed,
    world_index) is self-consistent and the replay agrees. A base arm at B
    has world indices 0..B-1; the doubled arm has 0..2B-1.
    """

    def __init__(self, monkeypatch, seed, *, base_b, flat=0.0, extra=0.0):
        self.seed, self.base_b = seed, base_b
        self.flat, self.extra = flat, extra
        self.real = mcc._run_path_atom
        monkeypatch.setattr(mcc, "_run_path_atom", self)

    def __call__(self, prepared, **kw):
        atom = self.real(prepared, **kw)
        if kw["master_seed"] != self.seed:
            return atom
        delta = self.flat + (self.extra if kw["world_index"] >= self.base_b
                             else 0.0)
        if not delta:
            return atom
        return dataclasses.replace(
            atom,
            monthly_prop_operating_ev=atom.monthly_prop_operating_ev + delta)


class _Capture:
    """The arms the runner built and the report the production path computed.

    Nothing is altered: convergence returns its report and the seal refuses
    afterwards, so the real object is observable even on a run that does not
    seal. Recomputing it here would be a second opinion rather than the one
    that decided.
    """

    def __init__(self, monkeypatch):
        self.arms, self.report = {}, None
        real_arm, real_conv = run._arm, mcc.convergence_from_evidence

        def arm_spy(prepared, **kw):
            ev = real_arm(prepared, **kw)
            self.arms[kw["run_label"]] = ev
            return ev

        def conv_spy(*a, **kw):
            self.report = real_conv(*a, **kw)
            return self.report

        monkeypatch.setattr(run, "_arm", arm_spy)
        monkeypatch.setattr(mcc, "convergence_from_evidence", conv_spy)

    def quantiles(self, label):
        ev = self.arms[label]
        cons = ev.results[sorted(ev.results)[0]].__getitem__(0)
        return tuple(getattr(cons, f) for f in mcc.KEY_QUANTILE_FIELDS)

    def doubled_label(self, seed):
        """The label the runner filed this seed's doubled arm under."""
        return ("double_B" if seed == mcc.BASE_MASTER_SEED
                else "seed_%d_double_B" % seed)


def _go(wide, supplement, tmp_path):
    return run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))


def _tolerance(reference_value):
    return max(mcc.CONV_ABS_USD, mcc.CONV_REL * abs(reference_value))


def _worst(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


# == CASES 1 and 2 -- the drift is isolated to one non-base seed ===========

@pytest.mark.parametrize("victim", list(RESEARCH_BOOTSTRAP_SEEDS[1:]))
def test_R2_a_within_seed_drift_at_one_non_base_seed_refuses(
        victim, wide, supplement, tmp_path, monkeypatch):
    """CASES 1 and 2. The seed's own B and 2B arms are more than a tolerance
    apart; both are inside the tolerance of the base seed's arm. Before the
    repair rule (c) saw only the second fact and the run sealed."""
    cap = _Capture(monkeypatch)
    _Shift(monkeypatch, victim, base_b=mcc.B_WORLDS_FROZEN,
           flat=TRAP_FLAT, extra=TRAP_EXTRA)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "main_channel_not_converged"

    at_b = cap.quantiles("seed_%d" % victim)
    at_2b = cap.quantiles(cap.doubled_label(victim))
    base7 = cap.quantiles("base")
    tol = _tolerance(base7[0])

    # the trap holds: BOTH arms are within tolerance of the base seed's arm
    assert _worst(at_b, base7) <= tol
    assert _worst(at_2b, base7) <= tol
    # and the seed has not stabilised within itself
    assert _worst(at_2b, at_b) > tol

    report = cap.report
    assert report.quantile_drift_ok is False
    assert report.converged is False
    # ...and it is rule (c) that said so, with (b) untouched: a within-seed
    # failure is not being reported through the cross-seed rule.
    assert report.category_same_across_seeds is True
    assert dict(report.seeds_agree_by_scale) == {"base": True, "doubled": True}


@pytest.mark.parametrize("victim", list(RESEARCH_BOOTSTRAP_SEEDS[1:]))
def test_R2_the_recorded_delta_is_the_within_seed_movement(
        victim, wide, supplement, tmp_path, monkeypatch):
    """The number in the report is the one the rule acted on, and it is the
    seed's own B-to-2B movement -- not its distance from the base seed."""
    cap = _Capture(monkeypatch)
    _Shift(monkeypatch, victim, base_b=mcc.B_WORLDS_FROZEN,
           flat=TRAP_FLAT, extra=TRAP_EXTRA)
    with pytest.raises(mcc.MCInputError):
        _go(wide, supplement, tmp_path)

    label = "seed_%d_double_B" % victim
    recorded = cap.report.drift_by_axis[label]
    at_b = cap.quantiles("seed_%d" % victim)
    at_2b = cap.quantiles(cap.doubled_label(victim))
    base7 = cap.quantiles("base")
    cid = sorted(cap.arms["base"].results)[0]
    for field, own, doubled, seven in zip(mcc.KEY_QUANTILE_FIELDS,
                                          at_b, at_2b, base7):
        got = recorded["%s|Conservative|%s" % (cid, field)]
        assert got == pytest.approx(abs(doubled - own)), field
        if abs(doubled - own) != pytest.approx(abs(doubled - seven)):
            assert got != pytest.approx(abs(doubled - seven)), field


# == CASE 3 -- an independently stable control ============================

def test_R2_independently_stable_seeds_still_converge(wide, supplement,
                                                      tmp_path, monkeypatch):
    """CASE 3. Each seed's own B-to-2B movement is within tolerance, so the
    B axis may converge -- the repair tightens the question, it does not
    refuse everything."""
    cap = _Capture(monkeypatch)
    result = _go(wide, supplement, tmp_path)
    report = cap.report
    assert report.quantile_drift_ok is True
    assert report.converged is True
    assert result.seal_candidate
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        at_b = cap.quantiles("seed_%d" % seed)
        at_2b = cap.quantiles(cap.doubled_label(seed))
        assert _worst(at_2b, at_b) <= _tolerance(at_b[0])


def test_R2_a_seed_wide_shift_that_is_stable_within_itself_still_converges(
        wide, supplement, tmp_path, monkeypatch):
    """The other half of CASE 3, and the one a blunt repair would break: a
    seed may sit away from the base seed and still be stable within itself.
    `flat` alone moves both of that seed's arms together, so the within-seed
    movement is zero and rule (c) has nothing to refuse."""
    cap = _Capture(monkeypatch)
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]
    _Shift(monkeypatch, victim, base_b=mcc.B_WORLDS_FROZEN, flat=TRAP_FLAT)
    _go(wide, supplement, tmp_path)
    at_b = cap.quantiles("seed_%d" % victim)
    at_2b = cap.quantiles(cap.doubled_label(victim))
    assert _worst(at_2b, at_b) == pytest.approx(0.0)
    assert cap.report.quantile_drift_ok is True
    assert cap.report.converged is True


# == CASE 4 -- the shared-baseline trap, stated as the property ===========

def test_R2_the_shared_baseline_shortcut_is_gone_for_every_seed(
        wide, supplement, tmp_path, monkeypatch):
    """CASE 4. Every doubled arm records the reference it was measured
    against, so the pairing is checkable from the report rather than from the
    source -- and no doubled arm is paired with another seed's baseline."""
    cap = _Capture(monkeypatch)
    _go(wide, supplement, tmp_path)
    refs = dict(cap.report.drift_reference_by_axis)
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert refs["seed_%d_double_B" % seed] == "seed_%d" % seed, seed
    # the BASE seed is not exempt: its doubled arm is paired with its own
    # base-scale arm too, so the rule has no privileged seed left.
    assert refs["seed_%d_double_B" % mcc.BASE_MASTER_SEED] == \
        "seed_%d" % mcc.BASE_MASTER_SEED
    # and the cross-seed comparisons keep their ratified reference
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        assert refs["seed_%d" % seed] == "base"
    assert refs["double_B"] == "base" and refs["double_K"] == "base"


def test_R2_the_base_seeds_own_doubled_arm_is_also_within_seed(
        wide, supplement, tmp_path, monkeypatch):
    """SEED 7's pairing, asserted numerically rather than by label alone."""
    cap = _Capture(monkeypatch)
    _go(wide, supplement, tmp_path)
    seed = mcc.BASE_MASTER_SEED
    at_b = cap.quantiles("seed_%d" % seed)
    at_2b = cap.quantiles(cap.doubled_label(seed))
    recorded = cap.report.drift_by_axis["seed_%d_double_B" % seed]
    cid = sorted(cap.arms["base"].results)[0]
    for field, own, doubled in zip(mcc.KEY_QUANTILE_FIELDS, at_b, at_2b):
        assert recorded["%s|Conservative|%s" % (cid, field)] == \
            pytest.approx(abs(doubled - own)), field


def test_R2_a_within_seed_drift_at_the_base_seed_also_refuses(
        wide, supplement, tmp_path, monkeypatch):
    """And it is not merely reported for the base seed -- it refuses."""
    _Shift(monkeypatch, mcc.BASE_MASTER_SEED, base_b=mcc.B_WORLDS_FROZEN,
           flat=TRAP_FLAT, extra=TRAP_EXTRA)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "main_channel_not_converged"


# == CASE 5 -- the two levels are separate computations ===================

def test_R2_a_within_seed_failure_is_not_absorbed_by_cross_seed_agreement(
        wide, supplement, tmp_path, monkeypatch):
    """CASE 5, first direction. Rule (b) agrees at both scales and rule (c)
    still refuses. Before the repair this configuration converged, because
    the only thing looking at the doubled arm was measuring it against
    another seed."""
    cap = _Capture(monkeypatch)
    _Shift(monkeypatch, RESEARCH_BOOTSTRAP_SEEDS[1],
           base_b=mcc.B_WORLDS_FROZEN, flat=TRAP_FLAT, extra=TRAP_EXTRA)
    with pytest.raises(mcc.MCInputError):
        _go(wide, supplement, tmp_path)
    report = cap.report
    assert report.category_same_across_seeds is True       # (b) is content
    assert report.quantile_drift_ok is False               # (c) is not
    assert report.converged is False


def test_R2_a_cross_seed_failure_still_refuses_on_its_own(
        wide, supplement, tmp_path, monkeypatch):
    """CASE 5, other direction. A doubled-scale category disagreement fails
    rule (b) and withholds the seal whatever rule (c) found, so neither level
    can hide the other."""
    cap = _Capture(monkeypatch)
    _Shift(monkeypatch, RESEARCH_BOOTSTRAP_SEEDS[2],
           base_b=mcc.B_WORLDS_FROZEN, extra=5000.0)
    with pytest.raises(mcc.MCInputError) as ei:
        _go(wide, supplement, tmp_path)
    assert ei.value.code == "main_channel_not_converged"
    report = cap.report
    assert report.category_same_across_seeds is False
    assert dict(report.seeds_agree_by_scale)["doubled"] is False
    assert report.converged is False


def test_R2_the_two_levels_read_different_inputs(wide, supplement, tmp_path,
                                                 monkeypatch):
    """Stated on the report rather than in prose: (c) is a per-arm table of
    deltas with a named reference per arm, and (b) is a pair of booleans over
    CATEGORIES across seeds. They are computed from different things and
    reported as different fields."""
    cap = _Capture(monkeypatch)
    _go(wide, supplement, tmp_path)
    report = cap.report
    assert set(report.drift_by_axis) == set(report.drift_reference_by_axis)
    assert set(report.seeds_agree_by_scale) == {"base", "doubled"}
    assert isinstance(report.quantile_drift_ok, bool)
    assert isinstance(report.category_same_across_seeds, bool)
    # no doubled arm's reference is another seed's arm
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        ref = report.drift_reference_by_axis["seed_%d_double_B" % seed]
        others = {"seed_%d" % s for s in RESEARCH_BOOTSTRAP_SEEDS
                  if s != seed} | {"base"}
        assert ref not in others, (seed, ref)


# == the previous repair's properties are preserved =======================

def test_R2_every_governed_seed_still_has_its_own_B_and_2B(wide, supplement,
                                                           tmp_path):
    result = _go(wide, supplement, tmp_path)
    assert set(result.b_scales_by_seed) == set(RESEARCH_BOOTSTRAP_SEEDS)
    scales = set(result.b_scales_by_seed.values())
    assert len(scales) == 1
    at_b, at_2b = scales.pop()
    assert at_2b == 2 * at_b


def test_R2_no_4B_arm_was_introduced(wide, supplement, tmp_path, monkeypatch):
    seen = []
    real = run._mcc.run_epistemic

    def spy(prepared, **kw):
        seen.append(kw["B"])
        return real(prepared, **kw)

    monkeypatch.setattr(run._mcc, "run_epistemic", spy)
    _go(wide, supplement, tmp_path)
    base_b = min(seen)
    assert sorted(set(seen)) == [base_b, 2 * base_b]


def test_R2_no_new_tolerance_was_introduced(wide, supplement, tmp_path,
                                            monkeypatch):
    """The ratified tolerance is unchanged and is still the only one: the
    repair moved WHAT is compared, never HOW MUCH movement is allowed."""
    assert mcc.CONV_ABS_USD == 25.0 and mcc.CONV_REL == 0.05
    assert mcc.KEY_QUANTILE_FIELDS == ("p5", "median", "p95")
    cap = _Capture(monkeypatch)
    _Shift(monkeypatch, RESEARCH_BOOTSTRAP_SEEDS[1],
           base_b=mcc.B_WORLDS_FROZEN, flat=TRAP_FLAT, extra=TRAP_EXTRA)
    with pytest.raises(mcc.MCInputError):
        _go(wide, supplement, tmp_path)
    # the movement that refused is above the ratified bound, and the one that
    # did not is below it -- 26 against 24.9, with 25 between them
    victim = RESEARCH_BOOTSTRAP_SEEDS[1]
    at_b = cap.quantiles("seed_%d" % victim)
    at_2b = cap.quantiles(cap.doubled_label(victim))
    assert _worst(at_2b, at_b) > mcc.CONV_ABS_USD
    assert _worst(at_b, cap.quantiles("base")) < mcc.CONV_ABS_USD
