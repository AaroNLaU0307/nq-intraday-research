"""The PRODUCTION prepare caller (R2.1 PHASE F — the non-test caller that
proves the formal prepare path consumes the EXTERNAL custody authority).

Order is the whole point:
  1. guards (G9 + second-copy attestations);
  2. the real-MC authorization gate — which refuses DETERMINISTICALLY
     today (no MC_RUN_AUTHORIZED registry vocabulary exists), so the
     sealed bundle bytes below are NEVER read in the current state;
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


def prepare_real_mc_input() -> "mcc.PreparedMCInput":
    """Gate-first production prepare. Unreachable past the authorization
    gate until Aaron + Codex introduce the MC registry vocabulary."""
    from itsf.guards import G9_FLAG, SECOND_COPY_FLAG, assert_real_run_allowed
    assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)
    # Invariant 5 of dec-registry-migration-2026-08-27 — one construction
    # site, and absence now refuses instead of reading as empty.
    from .registry_boundary import read_snapshot
    mcc.authorize_real_mc(read_snapshot().text)
    # --- unreachable today (authorize_real_mc always raises) -------------
    # R2.2 PHASE E: the SOLE formal entry — raw attestation bytes go in,
    # the authority is constructed and pinned INSIDE prepare_mc_input.
    attestation_bytes = (mcc._REPO_ROOT / mcc.ATTESTATION_PATH).read_bytes()
    authority = mcc.load_custody_authority_from_attestation(
        attestation_bytes=attestation_bytes)
    bundle = {p.name: p.read_bytes() for p in SEALED_RUN_DIR.iterdir()
              if p.is_file()}
    snapshot = {"trial_id": authority.trial_id,
                "authorized_commit": authority.authorized_commit}
    return mcc.prepare_mc_input(bundle, authorization_snapshot=snapshot,
                                attestation_bytes=attestation_bytes)
