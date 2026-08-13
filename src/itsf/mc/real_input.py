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
    registry = mcc._REPO_ROOT / "ops" / "TRIAL_REGISTRY.md"
    mcc.authorize_real_mc(
        registry.read_text(encoding="utf-8") if registry.exists() else "")
    # --- unreachable today (authorize_real_mc always raises) -------------
    authority = mcc.load_custody_authority_from_attestation()
    bundle = {p.name: p.read_bytes() for p in SEALED_RUN_DIR.iterdir()
              if p.is_file()}
    snapshot = {"trial_id": authority.trial_id,
                "authorized_commit": authority.authorized_commit}
    return mcc.prepare_mc_input(bundle, authorization_snapshot=snapshot,
                                custody_authority=authority)
