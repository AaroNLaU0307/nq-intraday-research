"""N13 — the full MC runner: orchestration over the governed machinery.

WHAT THIS IS. Every piece the Checkpoint-0 statistic needs already existed and
was individually governed; nothing assembled them. This module is that
assembly and nothing else: it holds no statistic, no threshold, no reduction
and no verdict logic of its own. Every number it returns came out of
`consumer`, `feasibility`, `grid_replay` or `verdict`.

WHAT IT ORCHESTRATES, in order:

    PreparedMCInput authority (battery receipt re-verified by the seal)
      -> the six governed arms: base + double_B + double_K + seeds 7/13/31
      -> GridReplayAuthority over the SEALED DAY_STRATA supplement (N11)
      -> KReplayEvidence per seed from two grid passes (N11)
      -> ruled feasibility evidence, composed inside the reduction (B-26)
      -> Checkpoint-0 reduction and category
      -> rules (a)-(d) convergence, K admitted only against the witness
      -> verdict + seal candidate, with the grid section's M7 standing
      -> M10's cross-seed published region

LIFECYCLE: NO NEW STATE MACHINE. N12 landed the ratified MC grammar
(`mc_contract`, `MC_RULING=G1_G8_RATIFIED_2026-08-24`: 16 events, 20 legal
transitions) and its parser (`mc_registry`). The runner READS that chain and
refuses to run unless the registry already entitles it to; it invents no
states of its own and appends no rows. `ops/RESEARCH_STATE.md` §5 describes
the chain coarsely as "PROPOSED -> AUTHORIZED -> STARTED -> SEALED"; that
prose predates the ratified grammar and the grammar is the normative form.

THE AUTHORIZATION BOUNDARY IS UNCHANGED. `execute_full_mc` is gate-first: its
very first call is `consumer.authorize_real_mc`, which refuses
unconditionally today, exactly as `day_strata_supplement.
run_supplement_production` does. Everything after that gate is unreachable
until Aaron issues the authorization sentence, and this module does not touch
that gate -- changing a tier-B authorization gate needs a review seat
(`ops/RESEARCH_STATE.md` §8) and is not N13 build work. The binding logic
BELOW the gate is still exercised, by the synthetic entry, so it is tested
rather than merely written.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as _mcc
from itsf.mc import grid_channel as _gc
from itsf.mc import grid_replay as _gr
from itsf.mc import mc_contract as _mcx
from itsf.mc.atoms import MCInputError

__all__ = ("RunAuthorization", "bind_run_authorization", "RunnerResult",
           "execute_full_mc", "execute_full_mc_for_tests",
           "ARM_LABELS", "runner_readycheck")

#: The arms rule (a)/(b) and M10 require. `double_K` reruns only the grid
#: channel, so its Oracle statistics must equal the base run's bit for bit --
#: convergence enforces that, this module only labels the arms.
#:
#: M10 (b) IS A PER-SEED QUANTIFIER: "B 加倍同样三 seeds 各做（3×{B,2B}
#: 全量）". Only the base seed had a doubled-B arm, so the other two governed
#: seeds ran base B alone and rule (b)'s doubled-scale half had no evidence to
#: evaluate. Their arms are named here; the base seed's doubled-B arm is the
#: ratified `double_B` and is NOT recomputed under a second label, because
#: M10's compute form is 3 x (base full + 2B full) and an extra arm would
#: overstate it.
ARM_LABELS = ("base", "double_B", "double_K",
              "seed_7", "seed_13", "seed_31",
              "seed_13_double_B", "seed_31_double_B")


# ---------------------------------------------------------------------------
# the authorization binding (read-only; appends nothing)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RunAuthorization:
    """One live `MC_RUN_AUTHORIZED` row, bound to what it authorizes.

    A certificate, not a permission: holding one does not open the gate, and
    the gate does not consult one. It records WHICH run id, commit and
    output root the registry says are authorized, so the runner cannot
    silently execute a different tree or write somewhere else.
    """
    run_id: str
    authorized_commit: str
    output_root: str
    branch_policy: str
    registry_detail: str
    test_only: bool


def bind_run_authorization(resolution, *, run_id: str,
                           expected_commit: str, output_root: str,
                           test_only: bool = False) -> RunAuthorization:
    """Bind the live authorization for `run_id`, or refuse.

    Takes a `MediatedResolution`, NOT registry text or a path. C2: this
    module may not resolve the registry itself, because a second read of a
    mutable shared file is the loophole C2 closes -- MC validation could
    pass on one version while the run acted on another. The resolver call
    lives in `registry_boundary.mc_authorization`, and this function
    consumes its answer.

    Every refusal is the boundary's own: no chain, no live row, or more
    than one live row all mean NOT AUTHORIZED, and a tie is refused rather
    than broken. On top of that the commit must be the one the runner is
    about to execute -- an authorization for a different tree authorizes a
    different run.
    """
    if not _mcx.RUN_ID_RE.match(str(run_id)):
        raise MCInputError("mc_run_id_not_canonical",
                           f"{run_id!r} is not a canonical MC run id")
    if not _mcx.COMMIT_RE.match(str(expected_commit)):
        raise MCInputError("mc_run_commit_not_canonical",
                           f"{expected_commit!r} is not a 40-hex commit")
    if not str(output_root).strip():
        raise MCInputError(
            "mc_run_output_root_absent",
            "the authorization binds an output root; an empty one would let "
            "the run write anywhere")
    from .registry_boundary import mc_authorization
    event, commit, detail = mc_authorization(resolution, run_id)
    if event is None or not commit:
        raise MCInputError("mc_run_not_authorized", str(detail))
    if commit != str(expected_commit):
        raise MCInputError(
            "mc_run_authorization_commit_mismatch",
            f"{run_id}: the live authorization binds commit {commit[:12]}, "
            f"the runner is at {str(expected_commit)[:12]} — an "
            "authorization for a different tree authorizes a different run")
    return RunAuthorization(
        run_id=str(run_id), authorized_commit=commit,
        output_root=str(output_root),
        branch_policy=_mcx.BRANCH_POLICY_TOKEN,
        registry_detail=str(detail), test_only=bool(test_only))


def runner_readycheck(resolution, *, run_id: str) -> dict:
    """The `MC_RUNNER_READYCHECKED` fact, computed rather than asserted.

    Reports what the registry currently entitles this run id to, using the
    ratified transition table. It appends nothing and decides nothing; it
    exists so a readycheck row can quote a measured state instead of a
    builder's claim.
    """
    from .registry_boundary import mc_authorization
    event, commit, detail = mc_authorization(resolution, run_id)
    authorized = event is not None and bool(commit)
    return MappingProxyType({
        "run_id": str(run_id),
        "ruling": _mcx.MC_RULING,
        "ruling_delegated": _mcx.MC_RULING_DELEGATED,
        "live_authorization": authorized,
        "authorized_commit": commit if authorized else "",
        "detail": str(detail),
        # the ONLY transition the runner itself may cause, and only from a
        # live authorization. Everything else in the chain is somebody's
        # row to append, not the runner's to assume.
        "may_start": authorized and (("MC_RUN_AUTHORIZED", "MC_RUN_STARTED")
                                     in _mcx.LEGAL_TRANSITIONS),
    })


# ---------------------------------------------------------------------------
# the result
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RunnerResult:
    """What one complete MC run produced. Carries no research value of its
    own beyond the seal candidate the governed seal built."""
    run_id: str
    authorized_commit: str
    output_root: str
    seal_candidate: Mapping
    verdict: str
    grid_seal_status: str
    may_support_h1_entry: bool
    published_region_by_kind: Mapping
    #: THE CROSS-SEED GRID STANDING the two fields above are read from.
    #: They used to come from the base seed's witness alone, which made the
    #: other two seeds' doubled-scale results unable to affect the outcome.
    grid_convergence: object
    #: THE FULL PER-SEED GRID EVIDENCE: every governed seed, every cell, the
    #: statistics where they exist and the absence metadata where they do
    #: not. The merged maps above remain, and do not replace this.
    grid_evidence_by_seed: Mapping
    #: M10 (b) COVERAGE AS A FINAL OBSERVABLE: master_seed -> the B scales
    #: that seed actually ran a FULL arm at, taken from the RunEvidence the
    #: seal consumed rather than from the labels it was asked for. The
    #: missing doubled-B arms were invisible at this boundary, which is
    #: part of why they survived two repairs and a green suite.
    b_scales_by_seed: Mapping
    arm_labels: tuple
    test_only: bool

    @property
    def sealed(self) -> bool:
        """The terminal state of a successful run: a seal candidate exists
        and the grid section has a recorded standing."""
        return bool(self.seal_candidate) and bool(self.grid_seal_status)


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------

def _arm(prepared, *, run_label: str, axis: str, B: int, K: int, seed: int):
    """One governed arm: the COMPLETE Primary combo grid, through the only
    atom producer there is. No caller narrows the day set or the phase
    support -- `run_observation_set` refuses that by construction."""
    results = {}
    for platform, policy in _mcc.PRIMARY_COMBOS:
        for engine in _mcc.ENGINES:
            cons = _mcc.run_epistemic(
                prepared, platform=platform, engine=engine,
                scenario="Conservative", channel=_mcc.PRIMARY_THETA_CHANNEL,
                B=B, master_seed=seed, run_label=run_label)
            stress = _mcc.run_epistemic(
                prepared, platform=platform, engine=engine,
                scenario="Stress", channel=_mcc.PRIMARY_THETA_CHANNEL,
                B=B, master_seed=seed, run_label=run_label)
            results[f"{platform}|{engine}|{policy}"] = (cons, stress)
    return _mcc.RunEvidence(
        run_label=run_label, axis=axis, B=B,
        M=len(prepared.calendar.first_month_offsets), K=K, master_seed=seed,
        prepared_digest=_mcc.prepared_digest(prepared), results=results)


def _witness(prepared, *, supplement: Mapping, sealed_artifact_sha256: str,
             B: int, cells: tuple, production: bool):
    """Mint the GridReplayAuthority, RUN both grid passes, and derive a
    KReplayEvidence per seed.

    B-27: the passes are no longer an input. The runner executes them itself
    through `grid_channel.run_grid_pass`, which composes the adopted
    Cartesian M x K support inside every B world for each cell and seed, so
    the witness is produced by the governed path rather than handed in.

    The authority is minted from the SEALED supplement, so the runner cannot
    license grid replay from a table it assembled; the witnesses are computed
    from the two passes it just ran, so a witness cannot carry a convergence
    claim nobody computed (N11). `doublings=1` is the 2K pass and its first K
    draws are the K pass's, by the frozen streams.
    """
    # THE AUTHORITY FOLLOWS THE PREPARED INPUT'S OWN KIND, not the entry.
    #
    # F04. The synthetic entry used to force a TEST-ONLY authority even for a
    # production-shaped prepared input -- which is what the seal requires,
    # because only the production battery's product passes `
    # _assert_seal_provenance`. The result was a production-shaped run whose
    # grid evidence was test-only, sealed CONVERGED with H1 support: exactly
    # the admission hole. The supplement authority already resolves its entry
    # this way, and this now matches it.
    derive_authority = (_gr.derive_grid_replay_authority_for_tests
                        if prepared.test_only
                        else _gr.derive_grid_replay_authority)
    authority = derive_authority(
        prepared, supplement,
        sealed_artifact_sha256=sealed_artifact_sha256)
    # (e)'s BOUND, read off the ruled policy rather than written here.
    from itsf import contracts as _contracts
    max_doublings = int(_contracts.aaron_ruled_methods()
                        .grid_policy.max_doublings)
    chains, passes = {}, {}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        chains[seed] = []
        seed_passes = {}
        for attempt in range(max_doublings):
            witness, arms = _attempt(
                prepared, authority, supplement, master_seed=seed, B=B,
                cells=cells, doublings=attempt)
            chains[seed].append(witness)
            seed_passes["attempt_%d" % attempt] = arms
            # THE RETRY IS CONDITIONAL, which is what makes it rule (e)'s
            # escalation rather than a fixed two-pass ritual: it happens only
            # while the region has not converged, and it stops at the bound.
            if witness.grid_converged:
                break
        passes[seed] = MappingProxyType(seed_passes)
    return (authority,
            MappingProxyType({s: tuple(c) for s, c in chains.items()}),
            MappingProxyType(passes))


def _attempt(prepared, authority, supplement, *, master_seed: int, B: int,
             cells: tuple, doublings: int):
    """ONE authorized comparison: the arm at `doublings` against the arm at
    `doublings` + 1, and the witness derived from them.

    Attempt 0 is K vs 2K. Attempt 1 -- run only when attempt 0 did not
    converge -- is 2K vs 4K. There is no attempt 2: the ruled
    `max_doublings` is the bound and the caller stops there.
    """
    seed = master_seed
    at_k = _gc.run_grid_pass(prepared, authority, supplement,
                             master_seed=seed, B=B, doublings=doublings,
                             cells=cells)
    at_2k = _gc.run_grid_pass(prepared, authority, supplement,
                              master_seed=seed, B=B, doublings=doublings + 1,
                              cells=cells)
    base_k = int(authority.k_per_seed) * (2 ** int(doublings))
    witness = _gr.derive_k_replay_evidence(
        authority, master_seed=seed, cells_at_k=at_k, cells_at_2k=at_2k,
        k=base_k, k_doubled=2 * base_k)
        # The witness REPORTS k and 2k. Check it against the draws actually
        # executed, or the evidence could claim a pass size nobody ran —
        # which is the same class of defect as outer metadata impersonating
        # an axis. In production both are the ruled `k_per_seed`; they can
        # only diverge if the draw policy and the prepared input disagree,
        # and that is worth refusing rather than sealing.
    ran = _gc.drawn_count(prepared, authority, supplement,
                          master_seed=seed, cells=cells,
                          doublings=doublings)
    if ran is None:
        # F1-R2-01. No cell of this pass prescribed a draw. The sealed rule
        # licenses that only when EVERY grid point is marked
        # `infeasible_by_sample` — marked, skipped, reported in full — and
        # then there is nothing for the count guard to reconcile, because
        # nothing was sampled anywhere to compare against.
        #
        # The absence is CORROBORATED from the passes rather than taken on
        # `drawn_count`'s word. Trusting it would make `None` a hole in the
        # guard: a future change that returned it for the wrong reason would
        # skip the check silently. So "all skipped" must be visible in the
        # evidence itself, and anything else is a refusal.
        sampled = sorted(
            {key for pas in (at_k, at_2k)
             for key, cell in pas.cells.items()
             if not _gr.is_infeasible(cell)})
        if sampled:
            # Every offending cell is named, not a slice of them: this is a
            # fail-closed refusal and the full list is what a human needs.
            # A slice would also add a numeric constant to a module whose
            # own guard keeps it free of them.
            raise MCInputError(
                "mc_run_draw_count_absent_but_cells_sampled",
                f"seed {seed}: no cell prescribed a draw, yet "
                f"{len(sampled)} cell(s) carry statistics — an absent draw "
                "count is lawful only when every grid point is marked "
                f"{_gr.INFEASIBLE_BY_SAMPLE}: {sampled}")
    elif ran != (witness.k, witness.k_doubled):
        raise MCInputError(
            "mc_run_draw_count_mismatch",
            f"seed {seed}: the passes executed {ran[0]} and {ran[1]} "
            f"draws, the witness reports {witness.k} and "
            f"{witness.k_doubled}")
    return witness, MappingProxyType({"at_k": at_k, "at_2k": at_2k})


def _execute(prepared, *, authorization: RunAuthorization,
             supplement: Mapping, sealed_artifact_sha256: str,
             production: bool, cells: tuple = _gr.GRID_CELL_KEYS
             ) -> RunnerResult:
    """THE run. Everything here delegates; nothing here decides."""
    if not isinstance(authorization, RunAuthorization):
        raise MCInputError(
            "mc_run_authorization_required",
            f"{type(authorization).__name__} is not a RunAuthorization — the "
            "runner executes against a bound authorization, never a bare "
            "run id")
    if _mcc.prepared_digest(prepared) != _mcc.prepared_digest(prepared):
        raise MCInputError("prepared_digest_instability", "unstable identity")

    base_seed = _mcc.BASE_MASTER_SEED
    base = _arm(prepared, run_label="base", axis="base",
                B=_mcc.B_WORLDS_FROZEN, K=prepared.k_per_seed, seed=base_seed)
    doubled = {
        "B": _arm(prepared, run_label="double_B", axis="B",
                  B=2 * _mcc.B_WORLDS_FROZEN, K=prepared.k_per_seed,
                  seed=base_seed),
        # the K arm reruns the GRID channel only; its Oracle statistics must
        # come out identical, and convergence checks exactly that.
        "K": _arm(prepared, run_label="double_K", axis="K",
                  B=_mcc.B_WORLDS_FROZEN, K=2 * prepared.k_per_seed,
                  seed=base_seed),
    }
    seed_runs = {seed: _arm(prepared, run_label=f"seed_{seed}", axis="seed",
                            B=_mcc.B_WORLDS_FROZEN, K=prepared.k_per_seed,
                            seed=seed)
                 for seed in RESEARCH_BOOTSTRAP_SEEDS}
    # M10 (b) -- EVERY GOVERNED SEED GETS ITS OWN DOUBLED-B ARM.
    #
    # The base seed's already exists: `doubled["B"]` is a full run at 2B on
    # exactly this seed, and rule (a) binds it to the base run. Filing it
    # here as that seed's doubled-B evidence costs nothing and keeps M10's
    # stated compute form -- 3 seeds x (base full + 2B full) -- exact. The
    # other governed seeds get a new arm each, at 2B and at nothing else:
    # {B, 2B} is the whole of the frozen B quantifier and there is no 4B.
    #
    # Each arm carries its OWN master seed, which is what convergence
    # checks: a map that satisfied the seed set by repeating one seed's
    # evidence would leave the other seeds unmeasured just as surely as
    # omitting them did.
    if doubled["B"].master_seed != base_seed:
        raise MCInputError(
            "mc_run_doubled_b_base_seed_mismatch",
            f"the double_B arm carries master_seed="
            f"{doubled['B'].master_seed}, not the base seed {base_seed}")
    seed_doubled_runs = {}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        if seed == base_seed:
            seed_doubled_runs[seed] = doubled["B"]
            continue
        seed_doubled_runs[seed] = _arm(
            prepared, run_label=f"seed_{seed}_double_B", axis="seed_B",
            B=2 * _mcc.B_WORLDS_FROZEN, K=prepared.k_per_seed, seed=seed)

    authority, chains, grid_passes_by_seed = _witness(
        prepared, supplement=supplement,
        sealed_artifact_sha256=sealed_artifact_sha256,
        B=_mcc.B_WORLDS_FROZEN, cells=cells, production=production)
    # THE K ARM BINDS TO THE FROZEN-BASE ATTEMPT; THE STANDING CONSUMES THE
    # FINAL ONE. The outer `double_K` RunEvidence is produced at the frozen
    # scales, so the witness it is bound to is the base seed's FIRST attempt.
    # A seed that needed rule (e)'s retry ends on a later attempt, and that
    # later attempt is what the grid section's standing must reflect --
    # conflating the two would either break the K-arm binding or hide the
    # escalation.
    witness = chains[base_seed][0]
    grid_convergence = _gr.aggregate_k_replay_evidence(chains)
    # THE TEST-ONLY BOUNDARY, at the one place that knows which path this is.
    # A synthetic authority marks every witness it mints `test_only`, and a
    # production run may not seal that evidence. The synthetic entry passes
    # `production=False` and is unaffected.
    if production and grid_convergence.test_only:
        raise MCInputError(
            "mc_run_grid_evidence_test_only",
            "the grid evidence is test_only and this is a production run; "
            "synthetic grid evidence may not cross the production seal "
            "boundary")

    seal_candidate = _mcc.verdict_and_seal_from_evidence(
        prepared, base=base, doubled_by_axis=doubled, seed_runs=seed_runs,
        seed_doubled_runs=seed_doubled_runs,
        k_witness=witness, grid_convergence=grid_convergence)

    # M10: publish the cross-seed region from all three seeds' maps -- the
    # COMPARISON-ADJUSTED ones the witness carries, not a fresh `region_map`
    # over the raw K pass. Rebuilding from the raw pass dropped every cell M8
    # had relabelled `boundary_band`, so the third frozen class could be
    # created by the comparison and never appear in the published result.
    published = {}
    for kind in _gr.REGION_KINDS:
        published[kind] = _gr.publish_region(kind, {
            # the FINAL authorized attempt's adjusted map, so publication
            # reflects the comparison the standing was actually taken from
            seed: chains[seed][-1].adjusted_map(kind)
            for seed in RESEARCH_BOOTSTRAP_SEEDS})

    return RunnerResult(
        run_id=authorization.run_id,
        authorized_commit=authorization.authorized_commit,
        output_root=authorization.output_root,
        seal_candidate=MappingProxyType(dict(seal_candidate)),
        # the seal's own shape: {"verdict": {"category", "reason"}}
        verdict=str(seal_candidate["verdict"]["category"]),
        grid_seal_status=grid_convergence.grid_seal_status,
        may_support_h1_entry=grid_convergence.may_support_h1_entry,
        published_region_by_kind=MappingProxyType(published),
        grid_convergence=grid_convergence,
        grid_evidence_by_seed=_gr.per_seed_grid_report(
            grid_passes_by_seed, chains),
        b_scales_by_seed=MappingProxyType({
            seed: (int(seed_runs[seed].B),
                   int(seed_doubled_runs[seed].B))
            for seed in RESEARCH_BOOTSTRAP_SEEDS}),
        arm_labels=ARM_LABELS, test_only=authorization.test_only)


def execute_full_mc(prepared, *, run_id: str, output_root: str,
                    supplement: Mapping, sealed_artifact_sha256: str,
                    cells: tuple = _gr.GRID_CELL_KEYS) -> RunnerResult:
    """PRODUCTION entry. GATE-FIRST, and the gate is untouched.

    The first call is `consumer.authorize_real_mc`, which refuses
    unconditionally today — the same discipline
    `day_strata_supplement.run_supplement_production` uses. Nothing below
    the gate can be reached until Aaron issues the authorization sentence,
    and this function does not weaken, parse around, or best-effort satisfy
    it. The binding beneath it is the same code the synthetic entry runs, so
    it is exercised rather than merely present.
    """
    from .registry_boundary import resolve_registry
    resolution = resolve_registry()
    _mcc.authorize_real_mc(resolution.snapshot.text)
    # --- unreachable today (authorize_real_mc always raises) -------------
    authorization = bind_run_authorization(
        resolution, run_id=run_id,
        expected_commit=prepared.authorized_commit, output_root=output_root)
    return _execute(prepared, authorization=authorization,
                    supplement=supplement,
                    sealed_artifact_sha256=sealed_artifact_sha256,
                    production=True, cells=cells)


def execute_full_mc_for_tests(prepared, *, authorization: RunAuthorization,
                              supplement: Mapping,
                              sealed_artifact_sha256: str,
                              cells: tuple = _gr.GRID_CELL_KEYS
                              ) -> RunnerResult:
    """Synthetic entry: the SAME `_execute`, reached with an authorization
    the caller bound from synthetic registry text.

    It skips exactly one thing — the real-run gate — and nothing else. The
    authorization still has to resolve through `mc_registry`'s fail-closed
    chain walk, the authority is still minted from a supplement that must
    cover the frozen day universe, and the seal still runs every check it
    runs in production. A `test_only` authorization is marked as such and
    rides into the result.
    """
    return _execute(prepared, authorization=authorization,
                    supplement=supplement,
                    sealed_artifact_sha256=sealed_artifact_sha256,
                    production=False, cells=cells)
