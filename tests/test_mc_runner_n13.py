"""N13 — the full MC runner, exercised synthetically end to end.

Everything here is synthetic: a fabricated 8-day bundle at B=2, a synthetic
registry chain, and a synthetic DAY_STRATA supplement. No real MC is executed,
no governed registry is read or written, and any verdict or region below is an
artifact of the fixtures — NOT a research result.

The two properties worth stating plainly, because they are what make the
runner safe rather than merely working:

  * `execute_full_mc` is GATE-FIRST and the gate is untouched. It refuses
    through `consumer.authorize_real_mc` before it looks at anything else, so
    no arrangement of arguments reaches a real run.
  * the synthetic entry skips ONLY that gate. The authorization still has to
    resolve through `mc_registry`'s fail-closed chain walk, the grid authority
    still has to be minted from a supplement covering the frozen day
    universe, and the seal still runs every check it runs in production.
"""
import hashlib

import pytest

import test_mc_battery_boundary as BB
import test_mc_cold_replay as CR
import test_mc_registry_parser as RP
# The seal accepts ONLY the production attestation's product (B-PROV), so the
# end-to-end tests need the PRODUCTION-shaped battery product. Reused from the
# battery-boundary module rather than rebuilt, so there is one such fixture.
from test_mc_battery_boundary import _fixture_root, prod_like  # noqa: F401
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import day_strata_supplement as ds
from itsf.mc import grid_replay as gr
from itsf.mc import mc_contract as mcx
from itsf.mc import mc_runner as run
from itsf.mc import supplement_authority as sa

OUT_ROOT = "C:/synthetic/n13-output-root"


@pytest.fixture()
def prepared():
    b = CR._bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": CR.TRIAL,
                                   "authorized_commit": CR.COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=CR._calendar())


def _resolution(tmp_path, text, name="TRIAL_REGISTRY.md"):
    """A REAL MediatedResolution over synthetic bytes: written to a file and
    resolved through the boundary, so the C2 one-read discipline is
    exercised rather than bypassed."""
    from itsf.mc.registry_boundary import resolve_registry
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return resolve_registry(path)


@pytest.fixture()
def registry_text(tmp_path):
    """A synthetic chain authorizing MC-R001 at the fixture's own commit."""
    return _resolution(tmp_path,
                       RP.Reg().chain(RP.FULL[:5], commit=CR.COMMIT).text())


@pytest.fixture()
def prod_registry_text(tmp_path):
    return _resolution(tmp_path,
                       RP.Reg().chain(RP.FULL[:5], commit=BB.COMMIT).text())


@pytest.fixture()
def authorization(registry_text, prepared):
    return run.bind_run_authorization(
        registry_text, run_id=mcx.FIRST_RUN_ID,
        expected_commit=prepared.authorized_commit, output_root=OUT_ROOT,
        test_only=True)


@pytest.fixture()
def prod_authorization(prod_registry_text, prod_like):
    return run.bind_run_authorization(
        prod_registry_text, run_id=mcx.FIRST_RUN_ID,
        expected_commit=prod_like.authorized_commit, output_root=OUT_ROOT,
        test_only=True)


def _supplement_for(prepared):
    # the supplement authority has separate entries and each refuses the
    # other's product, so the entry follows the prepared input's own kind
    derive = (sa.derive_supplement_authority_for_tests if prepared.test_only
              else sa.derive_supplement_authority)
    seed_authority = derive(prepared, supplement_id=ds.SUPPLEMENT_ID)
    days, binding = sa.supplement_build_inputs(seed_authority, prepared)
    rows = [{"trade_date": d, "year": int(str(d)[:4]),
             "vol_stratum": ds.VOL_STRATA[i % len(ds.VOL_STRATA)],
             "event_stratum": ds.EVENT_STRATA[i % len(ds.EVENT_STRATA)]}
            for i, d in enumerate(sorted(days))]
    return ds.build_day_strata_supplement_test_only(
        rows, expected_day_set=days, binding=binding,
        supplement_id=ds.SUPPLEMENT_ID)


@pytest.fixture()
def supplement(prepared):
    return _supplement_for(prepared)


@pytest.fixture()
def prod_supplement(prod_like):
    return _supplement_for(prod_like)


def _sha(supplement):
    return hashlib.sha256(
        ds.canonical_supplement_bytes(supplement)).hexdigest()


def _grid(p5=100.0, median=50.0):
    return {key: gr.CellStatistics(conservative_p5={"c": p5},
                                   stress_median={"c": median},
                                   feasible={"c": True})
            for key in gr.GRID_CELL_KEYS}


@pytest.fixture()
def grid_passes():
    """Two identical passes per seed: a converged synthetic grid."""
    return {seed: {"at_k": _grid(), "at_2k": _grid()}
            for seed in RESEARCH_BOOTSTRAP_SEEDS}


@pytest.fixture()
def small_scale(monkeypatch):
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)


# ---------------------------------------------------------------------------
# the authorization boundary
# ---------------------------------------------------------------------------

def test_the_production_entry_is_gate_first_and_the_gate_still_refuses(
        prepared, supplement, grid_passes):
    """No arrangement of arguments reaches a real run. The refusal is the
    existing tier-B gate, untouched by N13."""
    from itsf.s0.handoff import McConsumerAbsent
    with pytest.raises((McConsumerAbsent, mcc.MCInputError)) as ei:
        run.execute_full_mc(
            prepared, run_id=mcx.FIRST_RUN_ID, output_root=OUT_ROOT,
            supplement=supplement,
            sealed_artifact_sha256=_sha(supplement))
    assert "MC_RUN_AUTHORIZED" in str(ei.value)
    # and the gate is reached BEFORE anything else — it is the first call
    import inspect
    body = inspect.getsource(run.execute_full_mc)
    gate = body.index("authorize_real_mc")
    for later in ("bind_run_authorization", "_execute("):
        assert body.index(later) > gate, later


def test_an_unauthorized_registry_refuses(prepared, tmp_path):
    """Fail-closed straight out of `mc_registry`: no chain, no live row."""
    with pytest.raises(mcc.MCInputError) as ei:
        run.bind_run_authorization(
            _resolution(tmp_path, RP.Reg().text()),
            run_id=mcx.FIRST_RUN_ID,
            expected_commit=prepared.authorized_commit, output_root=OUT_ROOT)
    assert ei.value.code == "mc_run_not_authorized"


def test_an_authorization_for_another_commit_refuses(
        prepared, registry_text, tmp_path):
    """An authorization for a different tree authorizes a different run."""
    other = _resolution(
        tmp_path, RP.Reg().chain(RP.FULL[:5], commit="b" * 40).text())
    with pytest.raises(mcc.MCInputError) as ei:
        run.bind_run_authorization(
            other, run_id=mcx.FIRST_RUN_ID,
            expected_commit=prepared.authorized_commit, output_root=OUT_ROOT)
    assert ei.value.code == "mc_run_authorization_commit_mismatch"
    # the matching one binds
    bound = run.bind_run_authorization(
        registry_text, run_id=mcx.FIRST_RUN_ID,
        expected_commit=prepared.authorized_commit, output_root=OUT_ROOT)
    assert bound.authorized_commit == prepared.authorized_commit


def test_a_malformed_run_id_or_empty_output_root_refuses(prepared,
                                                         registry_text):
    for bad_id in ("MC-R1", "mc-r001", "MC-DS-S001", ""):
        with pytest.raises(mcc.MCInputError) as ei:
            run.bind_run_authorization(
                registry_text, run_id=bad_id,
                expected_commit=prepared.authorized_commit,
                output_root=OUT_ROOT)
        assert ei.value.code == "mc_run_id_not_canonical"
    with pytest.raises(mcc.MCInputError) as ei:
        run.bind_run_authorization(
            registry_text, run_id=mcx.FIRST_RUN_ID,
            expected_commit=prepared.authorized_commit, output_root="   ")
    assert ei.value.code == "mc_run_output_root_absent"


def test_the_readycheck_reports_the_chain_rather_than_asserting_it(
        registry_text, tmp_path):
    """`MC_RUNNER_READYCHECKED` quotes a measured state. It appends nothing
    and it uses the ratified transition table rather than a local list."""
    ready = run.runner_readycheck(registry_text, run_id=mcx.FIRST_RUN_ID)
    assert ready["live_authorization"] is True
    assert ready["may_start"] is True
    assert ready["ruling"] == mcx.MC_RULING == "G1_G8_RATIFIED_2026-08-24"
    assert ready["ruling_delegated"] is True
    blank = run.runner_readycheck(_resolution(tmp_path, RP.Reg().text()),
                                  run_id=mcx.FIRST_RUN_ID)
    assert blank["live_authorization"] is False and blank["may_start"] is False


def test_the_runner_cannot_execute_on_a_bare_run_id(prepared, supplement,
                                                    grid_passes):
    """A bound authorization, not a string, is what the run executes
    against."""
    with pytest.raises(mcc.MCInputError) as ei:
        run.execute_full_mc_for_tests(
            prepared, authorization="MC-R001", supplement=supplement,
            sealed_artifact_sha256=_sha(supplement))
    assert ei.value.code == "mc_run_authorization_required"


# ---------------------------------------------------------------------------
# end to end
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# the authority boundaries the runner must not be able to talk around
# ---------------------------------------------------------------------------
def test_the_runner_no_longer_takes_grid_passes_from_a_caller(prepared):
    """WAS `test_all_three_seeds_are_required` and
    `test_a_pass_missing_its_doubled_arm_refuses`.

    Both validated a CALLER-SUPPLIED `grid_passes_by_seed` input. B-27
    removed that input: the runner now runs all three seeds' K and 2K passes
    itself through `grid_channel.run_grid_pass`, so "three seeds" and "both
    arms" are properties of the code path rather than of an argument a caller
    might get wrong. The M10 three-seed requirement is asserted where it now
    lives — inside `_witness`, over `RESEARCH_BOOTSTRAP_SEEDS`.
    """
    import inspect

    for entry in (run.execute_full_mc, run.execute_full_mc_for_tests):
        assert "grid_passes_by_seed" not in inspect.signature(entry).parameters
    src = inspect.getsource(run._witness) + inspect.getsource(run._attempt)
    assert "RESEARCH_BOOTSTRAP_SEEDS" in src
    # the arms are now `doublings` and `doublings + 1` of the attempt being
    # run, which is what made rule (e)'s second comparison expressible
    assert "doublings=doublings" in src and "doublings=doublings + 1" in src
    assert "run_grid_pass" in src
    # and the draw count the witness reports is checked against what ran
    assert "mc_run_draw_count_mismatch" in src


def test_the_runner_holds_no_statistic_of_its_own():
    """It orchestrates; it does not decide. No threshold, no comparison
    against a research value, and no verdict logic lives in this module."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(run))
    numbers = {n.value for n in ast.walk(tree)
               if isinstance(n, ast.Constant)
               and isinstance(n.value, (int, float))
               and not isinstance(n.value, bool)}
    # only the doubling factor, index/slice constants, and `commit[:12]`
    assert numbers <= {0, 1, 2, 12}, numbers

    # DOCSTRINGS STRIPPED before the name scan: the module docstring names
    # `verdict` and `feasibility` precisely to say it delegates to them, and
    # a naive source scan would match the explanation instead of the code.
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    code_only = ast.unparse(tree)
    for forbidden in ("apply_verdict", "percentile", "p5", "median",
                      "threshold", "CONV_ABS_USD", "CONV_REL",
                      "combo_feasibility", "cell_category"):
        assert forbidden not in code_only, forbidden
