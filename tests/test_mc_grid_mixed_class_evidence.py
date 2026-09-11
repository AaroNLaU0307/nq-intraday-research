"""What the K/2K comparison ACTUALLY does with a mixed infeasible/statistics cell.

WHY THIS FILE EXISTS, and what it is not. The N14 Round-1 independent review
raised a blocking O7/O12 finding: that `compare_region_maps` could silently skip
a cell whose class is `InfeasibleCell` on one side and `CellStatistics` on the
other, so the disagreement would vanish and convergence could be reported True
while another cell remained sampleable.

Reproduced on the exact reviewed bytes, that failure path did not occur. Every
mixed arrangement, both frozen region kinds, reported `converged=False` with the
mixed key in `flipped_cells`. The Owner ruled on 2026-09-11 that NO source
repair is authorised for the stated defect, and that the behaviour be frozen as
evidence instead. So these tests change nothing and prove nothing about who was
right -- they pin what the implementation does, so Round 2 can check it for
itself rather than re-deriving it from an argument.

THEY DO NOT ERASE THE ROUND-1 FINDING. A review finding and a mechanically
reproduced defect are different things, and the Round-1 HOLD stands exactly as
issued. What these add is the measurement the finding lacked.

The mechanism, for a reader who wants to check the claim rather than the test:
`cell_category` labels an `InfeasibleCell` `infeasible_by_sample` and a
`CellStatistics` `in` or `out`. Those are different labels, so the two region
maps differ at that key, and `residual` -- computed AFTER band relabelling, which
a mixed cell never enters -- is non-empty. `converged` is
`not residual and not drift`, so it is False before drift is even consulted.
"""
from __future__ import annotations

import pytest

from itsf.mc import grid_replay as gr

COMBO = "lucid|E1|P2"
MIXED = gr.GRID_CELL_KEYS[0]
ORDINARY = gr.GRID_CELL_KEYS[1]


def _stats(p5: float, median: float, feasible: bool = True):
    return gr.CellStatistics(conservative_p5={COMBO: p5},
                             stress_median={COMBO: median},
                             feasible={COMBO: feasible},
                             identity={"n_tp": 10, "n_fp": 5})


def _marked(key):
    """The sealed marked-and-skipped cell, carrying the arithmetic that
    decided it exactly as `InfeasibleCell` requires."""
    return gr.InfeasibleCell(reason=gr.INFEASIBLE_BY_SAMPLE, q_mil=int(key[0]),
                             r_mil=int(key[1]), master_seed=1, doublings=0,
                             n_tp=10, n_fp=999, fp_available=5,
                             detail="synthetic: quota exceeds the pool")


def _grid():
    """A full frozen grid of ordinary, sampleable, IN cells."""
    return {key: _stats(100.0, 50.0) for key in gr.GRID_CELL_KEYS}


def _compare(kind, cell_k, cell_2k):
    """One mixed cell against a grid that is otherwise ordinary.

    `ORDINARY` is left sampleable and identical on both sides on purpose: the
    finding was that a mixed cell disappears WHILE another cell remains
    sampleable, so the other cell has to actually be there.
    """
    at_k, at_2k = _grid(), _grid()
    at_k[MIXED], at_2k[MIXED] = cell_k, cell_2k
    return gr.compare_region_maps(kind, at_k, at_2k, k=64, k_doubled=128)


# ---------------------------------------------------------------------------
# The two mixed cases, both region kinds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", gr.REGION_KINDS)
@pytest.mark.parametrize("label,stats", [("2K classifies OUT", (-10.0, -10.0)),
                                         ("2K classifies IN", (100.0, 50.0))])
def test_case_1_k_infeasible_2k_statistics_does_not_converge(kind, label,
                                                             stats):
    """CASE 1: marked at K, sampled at 2K. Both 2K classes are covered, so
    the result cannot depend on which side of the region the 2K cell landed."""
    cmp = _compare(kind, _marked(MIXED), _stats(*stats))
    assert cmp.converged is False, label
    assert MIXED in cmp.flipped_cells, (label, cmp.flipped_cells)
    assert MIXED not in cmp.boundary_band_cells, (
        "a mixed-class cell must never be exempted as a boundary cell: it "
        "has no statistics on one side to hug zero with")
    assert cmp.map_at_k[MIXED] == gr.INFEASIBLE_BY_SAMPLE
    assert cmp.map_at_2k[MIXED] in (gr.IN_REGION, gr.OUT_OF_REGION)
    # The other cell is genuinely sampleable and genuinely agrees, so the
    # False above is attributable to the mixed cell alone.
    assert cmp.map_at_k[ORDINARY] == cmp.map_at_2k[ORDINARY]
    assert ORDINARY not in cmp.flipped_cells


@pytest.mark.parametrize("kind", gr.REGION_KINDS)
@pytest.mark.parametrize("label,stats", [("K classifies OUT", (-10.0, -10.0)),
                                         ("K classifies IN", (100.0, 50.0))])
def test_case_2_k_statistics_2k_infeasible_does_not_converge(kind, label,
                                                             stats):
    """CASE 2: the reverse direction. Sampled at K, marked at 2K."""
    cmp = _compare(kind, _stats(*stats), _marked(MIXED))
    assert cmp.converged is False, label
    assert MIXED in cmp.flipped_cells, (label, cmp.flipped_cells)
    assert MIXED not in cmp.boundary_band_cells
    assert cmp.map_at_k[MIXED] in (gr.IN_REGION, gr.OUT_OF_REGION)
    assert cmp.map_at_2k[MIXED] == gr.INFEASIBLE_BY_SAMPLE
    assert cmp.map_at_k[ORDINARY] == cmp.map_at_2k[ORDINARY]
    assert ORDINARY not in cmp.flipped_cells


def test_a_mixed_cell_survives_alongside_a_real_boundary_band_cell():
    """The band relabelling is where a cell could plausibly get lost, since
    that is the one step that rewrites the maps before `residual` reads them.
    A genuine band cell is present here, so the relabelling actually runs."""
    at_k, at_2k = _grid(), _grid()
    at_k[MIXED], at_2k[MIXED] = _marked(MIXED), _stats(-10.0, -10.0)
    at_k[ORDINARY], at_2k[ORDINARY] = _stats(1.0, 1.0), _stats(-1.0, -1.0)
    cmp = gr.compare_region_maps(gr.POSITIVE_EV_REGION, at_k, at_2k,
                                 k=64, k_doubled=128)
    assert ORDINARY in cmp.boundary_band_cells, (
        "the band cell is not banded, so this test is not exercising "
        "relabelling and proves less than it claims")
    assert cmp.converged is False
    assert MIXED in cmp.flipped_cells


# ---------------------------------------------------------------------------
# The same-class behaviours the Owner ruling requires to stay put
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", gr.REGION_KINDS)
def test_infeasible_infeasible_remains_legal_and_converges(kind):
    """Existing authority: the sealed infeasibility test is `n_fp >
    sum(fp_available)`, whose terms do not depend on k. A cell marked at K is
    marked at 2K, the classes agree, and there is nothing to compare."""
    cmp = _compare(kind, _marked(MIXED), _marked(MIXED))
    assert cmp.converged is True
    assert cmp.flipped_cells == ()
    assert cmp.map_at_k[MIXED] == gr.INFEASIBLE_BY_SAMPLE
    assert cmp.map_at_2k[MIXED] == gr.INFEASIBLE_BY_SAMPLE


@pytest.mark.parametrize("kind", gr.REGION_KINDS)
def test_statistics_statistics_is_unchanged(kind):
    """Two ordinary cells that agree still converge; two that disagree
    outside the band still do not. Neither is affected by anything here."""
    assert _compare(kind, _stats(100.0, 50.0), _stats(100.0, 50.0)).converged
    flipped = _compare(kind, _stats(100.0, 50.0), _stats(-500.0, -500.0))
    assert flipped.converged is False
    assert MIXED in flipped.flipped_cells


def test_an_all_marked_grid_is_unchanged():
    """Every cell marked on both sides: the existing all-marked handling.
    Nothing to compare anywhere, and the map carries the mark rather than
    OUT -- the distinction `cell_category` exists to preserve."""
    at_k = {key: _marked(key) for key in gr.GRID_CELL_KEYS}
    at_2k = {key: _marked(key) for key in gr.GRID_CELL_KEYS}
    cmp = gr.compare_region_maps(gr.POSITIVE_EV_REGION, at_k, at_2k,
                                 k=64, k_doubled=128)
    assert cmp.converged is True
    assert cmp.flipped_cells == ()
    assert set(cmp.map_at_k.values()) == {gr.INFEASIBLE_BY_SAMPLE}


def test_the_k_witness_carries_the_non_convergence_out():
    """`converged` is only useful if it reaches the consumer. `grid_converged`
    is the property `consumer.py` reads, and it is an AND across both frozen
    kinds -- so a mixed cell in either kind must take it False."""
    at_k, at_2k = _grid(), _grid()
    at_k[MIXED], at_2k[MIXED] = _marked(MIXED), _stats(-10.0, -10.0)
    by_kind = {kind: gr.compare_region_maps(kind, at_k, at_2k, k=64,
                                            k_doubled=128).converged
               for kind in gr.REGION_KINDS}
    assert by_kind == {kind: False for kind in gr.REGION_KINDS}
    assert not all(by_kind.values())


# ---------------------------------------------------------------------------
# The separate observation, recorded rather than repaired
# ---------------------------------------------------------------------------

def test_cell_drift_violations_reports_nothing_for_a_mixed_cell():
    """RECORDED AS NON-BLOCKING, NOT REPAIRED (Owner ruling, 2026-09-11).

    The public `cell_drift_violations` shares the same `continue` branch and
    returns no entry for a mixed cell. That is silence, and it was found while
    reproducing the Round-1 finding -- but it cannot produce a false
    convergence, because `compare_region_maps` computes
    `not residual and not drift` and residual has already fired.

    This test pins the CURRENT behaviour so a future change to it is a
    deliberate decision with a visible diff, not a side effect. It asserts no
    opinion about whether the silence should stay.
    """
    at_k, at_2k = _grid(), _grid()
    at_k[MIXED], at_2k[MIXED] = _marked(MIXED), _stats(-10.0, -10.0)
    assert gr.cell_drift_violations(gr.POSITIVE_EV_REGION, at_k, at_2k) == ()
    # And the comparison that consults it still refuses to converge.
    assert gr.compare_region_maps(gr.POSITIVE_EV_REGION, at_k, at_2k,
                                  k=64, k_doubled=128).converged is False
