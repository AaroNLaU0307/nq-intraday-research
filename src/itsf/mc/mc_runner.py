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

#: The six arms rule (a)/(b) and M10 require. `double_K` reruns only the grid
#: channel, so its Oracle statistics must equal the base run's bit for bit --
#: convergence enforces that, this module only labels the arms.
ARM_LABELS = ("base", "double_B", "double_K",
              "seed_7", "seed_13", "seed_31")


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
    derive_authority = (_gr.derive_grid_replay_authority if production
                        else _gr.derive_grid_replay_authority_for_tests)
    authority = derive_authority(
        prepared, supplement,
        sealed_artifact_sha256=sealed_artifact_sha256)
    witnesses, passes = {}, {}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        at_k = _gc.run_grid_pass(prepared, authority, supplement,
                                 master_seed=seed, B=B, doublings=0,
                                 cells=cells)
        at_2k = _gc.run_grid_pass(prepared, authority, supplement,
                                  master_seed=seed, B=B, doublings=1,
                                  cells=cells)
        passes[seed] = MappingProxyType({"at_k": at_k, "at_2k": at_2k})
        witness = _gr.derive_k_replay_evidence(
            authority, master_seed=seed, cells_at_k=at_k, cells_at_2k=at_2k)
        # The witness REPORTS k and 2k. Check it against the draws actually
        # executed, or the evidence could claim a pass size nobody ran —
        # which is the same class of defect as outer metadata impersonating
        # an axis. In production both are the ruled `k_per_seed`; they can
        # only diverge if the draw policy and the prepared input disagree,
        # and that is worth refusing rather than sealing.
        ran = _gc.drawn_count(prepared, authority, supplement,
                              master_seed=seed, cells=cells)
        if ran != (witness.k, witness.k_doubled):
            raise MCInputError(
                "mc_run_draw_count_mismatch",
                f"seed {seed}: the passes executed {ran[0]} and {ran[1]} "
                f"draws, the witness reports {witness.k} and "
                f"{witness.k_doubled}")
        witnesses[seed] = witness
    return authority, MappingProxyType(witnesses), MappingProxyType(passes)


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

    authority, witnesses, grid_passes_by_seed = _witness(
        prepared, supplement=supplement,
        sealed_artifact_sha256=sealed_artifact_sha256,
        B=_mcc.B_WORLDS_FROZEN, cells=cells, production=production)
    # the base arm's seed is what convergence binds the witness to
    witness = witnesses[base_seed]

    seal_candidate = _mcc.verdict_and_seal_from_evidence(
        prepared, base=base, doubled_by_axis=doubled, seed_runs=seed_runs,
        k_witness=witness)

    # M10: publish the cross-seed region from all three seeds' maps.
    published = {}
    for kind in _gr.REGION_KINDS:
        published[kind] = _gr.publish_region(kind, {
            seed: _gr.region_map(grid_passes_by_seed[seed]["at_k"], kind)
            for seed in RESEARCH_BOOTSTRAP_SEEDS})

    return RunnerResult(
        run_id=authorization.run_id,
        authorized_commit=authorization.authorized_commit,
        output_root=authorization.output_root,
        seal_candidate=MappingProxyType(dict(seal_candidate)),
        # the seal's own shape: {"verdict": {"category", "reason"}}
        verdict=str(seal_candidate["verdict"]["category"]),
        grid_seal_status=witness.grid_seal_status,
        may_support_h1_entry=witness.may_support_h1_entry,
        published_region_by_kind=MappingProxyType(published),
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
