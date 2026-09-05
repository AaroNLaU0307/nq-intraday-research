"""The PRODUCTION prepare caller (R2.1 PHASE F — the non-test caller that
proves the formal prepare path consumes the EXTERNAL custody authority).

Order is the whole point:
  1. guards (G9 + second-copy attestations);
  2. for the REAL MC only, the real-MC authorization gate — which refuses
     DETERMINISTICALLY today, so the sealed bundle bytes are NEVER read on
     that path. N09's supplement path carries the real-data guards and NOT
     that gate, per Aaron's 2026-09-05 ruling: the MC is downstream of N09,
     so gating N09 on it inverted the approved order;
  3. only then: load the typed custody authority from the blind post-run
     attestation (outside the bundle under review) and prepare.

This module performs no computation of its own and owns no test seams.
"""
from __future__ import annotations

from pathlib import Path

from itsf.mc import consumer as mcc

# the sealed S0-T001 run directory (L-5 ruled roots)
SEALED_RUN_DIR = Path(
    r"C:\Users\Aaron\quant-data\itsf-runs\runs\S0-T001_20260813T170432Z")


def _assemble_from_sealed_run() -> "mcc.PreparedMCInput":
    """The assembly itself, with NO authorization gate of its own.

    R2.2 PHASE E: the SOLE formal entry — raw attestation bytes go in, and
    the authority is constructed and pinned INSIDE `prepare_mc_input`. This
    computes nothing and runs no Monte Carlo; it reads the sealed S0 run and
    hands its structural facts to the formal prepare.

    Factored out on 2026-09-05 so that the two callers can carry DIFFERENT
    gates without either copying the assembly. Which gate applies is the
    caller's question, and the answer differs -- see both below.
    """
    attestation_bytes = (mcc._REPO_ROOT / mcc.ATTESTATION_PATH).read_bytes()
    authority = mcc.load_custody_authority_from_attestation(
        attestation_bytes=attestation_bytes)
    bundle = {p.name: p.read_bytes() for p in SEALED_RUN_DIR.iterdir()
              if p.is_file()}
    snapshot = {"trial_id": authority.trial_id,
                "authorized_commit": authority.authorized_commit}
    return mcc.prepare_mc_input(bundle, authorization_snapshot=snapshot,
                                attestation_bytes=attestation_bytes)


def prepare_real_mc_input() -> "mcc.PreparedMCInput":
    """Gate-first production prepare FOR THE REAL MC. Unreachable past the
    authorization gate until Aaron + Codex introduce the MC registry
    vocabulary.

    UNCHANGED by the 2026-09-05 ruling, deliberately: that ruling was about
    where the gate does NOT belong, not about weakening it where it does.
    The real MC still may not run without `MC_RUN_AUTHORIZED`.
    """
    from itsf.guards import G9_FLAG, SECOND_COPY_FLAG, assert_real_run_allowed
    assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)
    # Invariant 5 of dec-registry-migration-2026-08-27 — one construction
    # site, and absence now refuses instead of reading as empty.
    from .registry_boundary import read_snapshot
    mcc.authorize_real_mc(read_snapshot().text)
    # --- unreachable today (authorize_real_mc always raises) -------------
    return _assemble_from_sealed_run()


def prepare_supplement_mc_input() -> "mcc.PreparedMCInput":
    """N09's prepared input. Real-data gate YES, MC-run gate NO.

    AARON'S RULING, 2026-09-05. The day-strata supplement reading the sealed
    S0 bundle to assemble structural facts does not require the real MC to
    have been authorized. The approved dependency order is
    `N09 -> N10 -> N11 -> N13`, and the real MC, KReplayEvidence and grid
    replay all sit DOWNSTREAM of N09; `consumer` records the same direction
    from the other end -- the K axis is unblocked by "GRID-B supplement
    sealed", which is N09's own output.

    So routing N09 through `prepare_real_mc_input` put the MC-RUN gate in
    front of an input assembly that precedes the MC, which inverted the
    approved order and closed a cycle: N09 needed the MC authorized, a real
    MC needs the K axis, and the K axis needs N09's sealed supplement. That
    inversion was introduced when this session wired the entry, not by the
    ratified design.

    WHAT IS STILL ENFORCED. `assert_real_run_allowed` stays -- this reads
    real bytes and the real-data attestations still gate it. What the
    supplement then takes from the bundle is STRUCTURAL: day sequences,
    traded day sets, digests and custody identity. `prepare_mc_input` runs
    no Monte Carlo and reduces no metric.
    """
    from itsf.guards import G9_FLAG, SECOND_COPY_FLAG, assert_real_run_allowed
    assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)
    return _assemble_from_sealed_run()
