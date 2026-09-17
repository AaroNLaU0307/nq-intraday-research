"""The smallest complete engine: the sealed study, end to end, once.

This is the object S3 would run. It wires the parts in the sealed order and
refuses to run over anything but synthetic bars unless it is handed an S3
authorization token:

    event universe (E0..E3)  ->  signal + E4  ->  primary arm  ->  bootstrap
                             ->  C1 guard     ->  C2 + D       ->  verdict
                             ->  sealed outcome bundle (never printed)

Two things it deliberately does NOT do:

* it never computes the OD-3 power gate from the primary arm. The gate takes
  C2 dispersion only, and `r1.power_gate` has no route to a primary result.
* it never returns the outcome. `run_study` hands back a receipt and the
  verdict inputs it was given; the values live in the run directory behind
  `r1.outcome_seal.reveal`.

The C1 GUARD CRITERION is an implementation-level reading of sealed K.1, which
says only "if C1 also clears M". R1 holds C1 to the SAME bar the Primary must
clear -- the 95 % lower bound of its mean exceeds M -- because "also clears M"
most naturally means "would have been declared supported by the same rule".
The naive alternative (the average random arm's mean exceeds M) is computed and
reported beside it, never instead of it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .bootstrap import Interval, bootstrap_interval, sensitivity_interval
from .contract import SealedContract
from .controls import (C1Result, C2Arm, c2_dispersion, run_c1, run_c2,
                       specificity_difference, tercile_weights, weighted_mean)
from .errors import AuthorityError
from .outcome_seal import SEALED_R1_OUTCOME, SealedOutcomeHandle, seal_outcome
from .signal import apply_e4
from .trade import TradeResult, mean_y_net, run_arm
from .verdict import PrimaryEvidence, Verdict, decide

S3_TOKEN_PREFIX = "S3_RUN_AUTHORIZED_BY_AARON:"


def _require_authorized_source(source, s3_authorization: str | None) -> None:
    if getattr(source, "role", None) == "synthetic":
        return
    if not isinstance(s3_authorization, str) or \
            not s3_authorization.startswith(S3_TOKEN_PREFIX):
        raise AuthorityError(
            "the R1 study may only be executed over real Development bars "
            "under S3 authorization. S2 BUILD runs it on synthetic fixtures.")


@dataclass(frozen=True)
class ArmSummary:
    n: int
    mean_y_net_usd: float
    interval: Interval
    sensitivity: Interval


@dataclass(frozen=True)
class StudySummary:
    """Deliberately carries the DECISION inputs, not a table of outcomes."""
    n_structural: int
    e4_count: int
    n_signal_defined: int
    na_count: int
    verdict: Verdict
    c1_mean_of_draw_means: float
    c1_clears_m_same_bar: bool
    specificity_d: float | None
    handle: SealedOutcomeHandle


def run_primary(source, dates, contract: SealedContract, *,
                cost_scenario: str | None = None,
                s3_authorization: str | None = None
                ) -> tuple[tuple[TradeResult, ...], ArmSummary]:
    """The primary arm and its sealed interval."""
    _require_authorized_source(source, s3_authorization)
    scen = cost_scenario or contract.primary_cost_scenario
    e4 = apply_e4(source, dates, contract,
                  structural_n=contract.pre_seal_structural_n,
                  s3_authorization=s3_authorization)
    directed = [(s.date_et, s.d_event) for s in e4.signals]
    results = run_arm(source, directed, contract, cost_scenario=scen,
                      emit_paths=True)
    values = [r.y_net_usd for r in results]
    return results, ArmSummary(
        n=len(results), mean_y_net_usd=mean_y_net(results),
        interval=bootstrap_interval(values, contract),
        sensitivity=sensitivity_interval(values, contract))


def run_study(source, dates, contract: SealedContract, *, run_dir: Path | str,
              c2_dates=(), event_vol_states=(), c2_vol_states=(),
              a1_sign_holds: bool = True,
              power_gate_resolves_m: bool = True,
              n_shrunk_materially: bool = False,
              c1_seed: int | None = None, c1_draws: int | None = None,
              s3_authorization: str | None = None) -> StudySummary:
    """The whole sealed study, once. Returns decision inputs and a receipt."""
    _require_authorized_source(source, s3_authorization)

    e4 = apply_e4(source, dates, contract,
                  structural_n=contract.pre_seal_structural_n,
                  s3_authorization=s3_authorization)
    directed = [(s.date_et, s.d_event) for s in e4.signals]

    base = run_arm(source, directed, contract,
                   cost_scenario=contract.primary_cost_scenario,
                   emit_paths=True)
    conservative = run_arm(source, directed, contract,
                           cost_scenario=contract.a3_cost_scenario)
    base_values = [r.y_net_usd for r in base]
    base_ci = bootstrap_interval(base_values, contract)

    # C1: the guard. Held to the SAME bar as the Primary (see module docstring).
    c1: C1Result = run_c1(source, [d for d, _ in directed], contract,
                          seed=(c1_seed if c1_seed is not None
                                else contract.bootstrap_seeds[0]),
                          draws=c1_draws)
    c1_ci = bootstrap_interval(list(c1.draw_means), contract)
    c1_clears = c1_ci.clears(contract.materiality_m_usd)

    # C2: specificity. Non-confirmatory; it cannot reach Axis 1.
    d_stat = None
    d_ci = None
    if c2_dates:
        arm: C2Arm = run_c2(source, c2_dates, contract,
                            vol_states=c2_vol_states or None)
        if event_vol_states:
            d_stat = specificity_difference(base, arm, event_vol_states)
            weighted = weighted_mean(arm, tercile_weights(event_vol_states))
            d_values = [v - weighted for v in base_values]
            d_ci = bootstrap_interval(d_values, contract)

    evidence = PrimaryEvidence(
        base_interval=base_ci,
        conservative_point_estimate=mean_y_net(conservative),
        c1_clears_m=c1_clears,
        a1_sign_holds=a1_sign_holds,
        materiality_m=contract.materiality_m_usd,
        power_gate_resolves_m=power_gate_resolves_m,
        n_shrunk_materially=n_shrunk_materially)
    verdict = decide(evidence, d_ci)

    handle = seal_outcome(
        {
            "records": [
                {"date_et": r.date_et, "direction": r.direction,
                 "y_net_usd": r.y_net_usd, "mae_usd": r.mae_usd,
                 "mfe_usd": r.mfe_usd,
                 "close_path_usd": list(r.close_path_usd),
                 "adverse_path_usd": list(r.adverse_path_usd)}
                for r in base],
            "mean_y_net_usd": evidence.conservative_point_estimate,
            "base_interval": [base_ci.lower, base_ci.upper],
            "e4_count": e4.e4_count,
            "verdict_axis1": verdict.axis1,
            "verdict_axis2": verdict.axis2,
        },
        run_dir, output_class=SEALED_R1_OUTCOME,
        synthetic=(getattr(source, "role", None) == "synthetic"),
        s3_authorization=s3_authorization)

    return StudySummary(
        n_structural=e4.pre_seal_structural_n, e4_count=e4.e4_count,
        n_signal_defined=len(base), na_count=len(e4.na_dates),
        verdict=verdict, c1_mean_of_draw_means=c1.mean_of_draw_means,
        c1_clears_m_same_bar=c1_clears, specificity_d=d_stat, handle=handle)


def power_gate_inputs_from_control(c2_arm: C2Arm) -> float:
    """The ONLY bridge to the OD-3 gate: control dispersion, nothing else."""
    return c2_dispersion(c2_arm)
