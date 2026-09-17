"""TASK 15 -- prospective R1 run identity.

What a future S3 run must bind before it may compute anything, and the digest
that makes the binding checkable. Defined now, prospectively, so the run cannot
later be described loosely:

    sealed content commit . seal attestation commit . prereg digest .
    manifest digest . event-calendar digest . data manifest identity .
    event-universe digest (L-6) . code commit . environment identity .
    run configuration . cost scenario definitions . seed set .
    trial-registry identity

Three identities are kept apart on purpose, because conflating them is how a
sealed design quietly becomes whatever the code happens to do:

    CONTENT_COMMIT          the SEALED research content       immutable
    SEAL_ATTESTATION_COMMIT the attestation to it             immutable
    S2_BUILD_COMMIT         the IMPLEMENTATION that runs it   versioned

Post-seal interpretation artifacts -- the errata record and the operational
execution ledger -- are bound here too, and are never part of the S1 sealed
digest set

No real research run is created here, and `RunIdentity.is_real_run` is False
unless an S3 authorization token is supplied -- so a synthetic identity can
never be mistaken for a run that consumed the trial.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from .contract import BOUND_SEAL_ATTESTATION_COMMIT, SealedContract
from .errors import AuthorityError

S3_TOKEN_PREFIX = "S3_RUN_AUTHORIZED_BY_AARON:"


def environment_identity() -> dict[str, str]:
    """Enough of the environment to reproduce, not so much that it is noise."""
    try:
        import numpy
        numpy_version = numpy.__version__
    except Exception:                                   # pragma: no cover
        numpy_version = "absent"
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(terse=True),
        "numpy": numpy_version,
    }


@dataclass(frozen=True)
class RunIdentity:
    run_label: str
    is_real_run: bool

    # sealed identity
    content_commit: str
    seal_attestation_commit: str
    prereg_sha256: str
    manifest_sha256: str
    decision_record_sha256: str
    trial_registry_sha256: str

    # data identity
    event_calendar_sha256: str
    symbology_sha256: str
    data_manifest_sha256: str
    psmv_artifact_sha256: str
    event_universe_digest: str          # L-6: frozen before any outcome

    # code and environment identity -- NEVER confused with the sealed identity
    code_commit: str
    s2_build_commit: str | None            # implementation identity only
    environment: Mapping[str, str]

    # post-seal interpretation artifacts (additive; never part of the S1 seal)
    sealed_errata_sha256: str | None
    operational_ledger_digest: str | None

    # run configuration
    cost_scenarios: Mapping[str, Mapping[str, float]]
    primary_cost_scenario: str
    bootstrap_seeds: tuple[int, ...]
    bootstrap_block_events: int
    bootstrap_resamples: int
    c1_seed_set: tuple[int, ...]
    materiality_m_usd: float
    k: int
    n_structural: int

    # trial accounting
    sample_formal_trial_ordinal: int
    inherited_researcher_exposure_count: int
    trial_consumed: bool = False

    notes: tuple[str, ...] = field(default=())

    def payload(self) -> dict[str, Any]:
        d = asdict(self)
        d["cost_scenarios"] = {k: dict(v) for k, v in self.cost_scenarios.items()}
        d["environment"] = dict(self.environment)
        return d

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(self.payload(), sort_keys=True).encode("utf-8")
        ).hexdigest()


def build_run_identity(contract: SealedContract, *, run_label: str,
                       code_commit: str, data_manifest_sha256: str,
                       event_universe_digest: str,
                       s2_build_commit: str | None = None,
                       sealed_errata_sha256: str | None = None,
                       operational_ledger_digest: str | None = None,
                       s3_authorization: str | None = None,
                       notes: tuple[str, ...] = ()) -> RunIdentity:
    """Build the identity. Real only under an explicit S3 authorization."""
    is_real = isinstance(s3_authorization, str) and \
        s3_authorization.startswith(S3_TOKEN_PREFIX)
    if s3_authorization is not None and not is_real:
        raise AuthorityError("malformed S3 authorization token")

    scenarios = {
        name: {
            "entry_spread_points": s.entry_spread_points,
            "exit_spread_points": s.exit_spread_points,
            "slippage_ticks_per_side": s.slippage_ticks_per_side,
            "friction_multiplier": s.friction_multiplier,
            "platform_fee_rt_usd": s.platform_fee_rt_usd,
            "round_turn_usd": contract.round_turn_cost_usd(name),
        }
        for name, s in contract.cost_scenarios.items()
    }
    return RunIdentity(
        run_label=run_label,
        is_real_run=is_real,
        content_commit=contract.content_commit,
        seal_attestation_commit=BOUND_SEAL_ATTESTATION_COMMIT,
        prereg_sha256=contract.prereg_sha256,
        manifest_sha256=contract.manifest_sha256,
        decision_record_sha256=contract.decision_record_sha256,
        trial_registry_sha256=contract.trial_registry_sha256,
        event_calendar_sha256=contract.event_calendar_sha256,
        symbology_sha256=contract.symbology_sha256,
        data_manifest_sha256=data_manifest_sha256,
        psmv_artifact_sha256=contract.psmv_artifact_sha256,
        event_universe_digest=event_universe_digest,
        code_commit=code_commit,
        s2_build_commit=s2_build_commit,
        environment=environment_identity(),
        sealed_errata_sha256=sealed_errata_sha256,
        operational_ledger_digest=operational_ledger_digest,
        cost_scenarios=scenarios,
        primary_cost_scenario=contract.primary_cost_scenario,
        bootstrap_seeds=contract.bootstrap_seeds,
        bootstrap_block_events=contract.bootstrap_block_events,
        bootstrap_resamples=contract.bootstrap_resamples,
        c1_seed_set=contract.bootstrap_seeds,
        materiality_m_usd=contract.materiality_m_usd,
        k=contract.k,
        n_structural=contract.pre_seal_structural_n,
        sample_formal_trial_ordinal=contract.sample_formal_trial_ordinal,
        inherited_researcher_exposure_count=(
            contract.inherited_researcher_exposure_count),
        trial_consumed=False,
        notes=notes,
    )


def assert_event_set_frozen(identity: RunIdentity,
                            current_universe_digest: str) -> None:
    """L-6: the runner refuses if the event set moved after it was bound."""
    if identity.event_universe_digest != current_universe_digest:
        from .errors import SealIdentityError
        raise SealIdentityError(
            "the event universe changed after the run identity was bound "
            "(L-6). Refuse: an event set that can move after binding is an "
            "outcome-dependent event set.")
