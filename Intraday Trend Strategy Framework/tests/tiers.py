"""The tier map: which test files the run gate does NOT execute.

QROS-CF v2 §2.6 (DEC-0006 I4). Three tiers, carried by markers rather than
by directory moves (Aaron's boundary: no test-tree moves before N10):

    validity    (A)  research-validity tests -- leakage, data identity,
                     no look-ahead, reproducibility, numerical invariants,
                     production-vs-reference identity, strategy logic
    safety      (B)  execution-safety tests -- run isolation, atomic writes,
                     authorization binding, registry legality, refusals
    governance  (C)  document / index / packet / naming guards

ONLY `GOVERNANCE_FILES` is enumerated. Every test file NOT listed here is
tier A or B and runs inside the run gate; an unmapped file is therefore
in the gate by default (fail-closed). Placement rule (converged §6.1): a
test is tier A if deleting it could let a wrong research number pass, tier
B if deleting it could let an unauthorized or unsafe write happen, and
tier C otherwise.

THIS FILE IS PART OF THE GOVERNED-EXECUTION IDENTITY. Moving a test into
tier C removes it from the identity, so the move itself is visible as an
identity change (`itsf.execution_identity`).

Created at P2 with an EMPTY governance list so the identity has a map to
read; populated at P4 (I4) with the files whose subject is a document, an
index, a packet, a prompt, a seat ledger or a review register.
"""

#: Tier C. File names under tests/, exactly. Populated at P4 (I4) with the
#: files whose SUBJECT is a document, an index, a packet, a prompt, a seat
#: ledger, a review register, a ratification record or source formatting.
#: Nothing here reads a research number, a gate, a refusal, a registry
#: parser or a witness: those stay in the gate by default.
GOVERNANCE_FILES = (
    "test_a_prompts_measured_numbers_are_current.py",
    "test_a_prompts_range_claim_actually_holds.py",
    "test_a_proposal_states_the_hash_of_its_own_block.py",
    "test_artifacts_under_review_are_frozen.py",
    "test_cited_records_exist.py",
    "test_delivery_names_no_quarantined_path.py",
    "test_every_approval_is_accounted_for.py",
    "test_exposure_discoverability.py",
    "test_exposure_ledger_migration.py",
    "test_feasibility_errata_register.py",
    "test_governance_docs.py",
    "test_issued_deliveries_are_registered.py",
    "test_nd1_profile_revision_chain.py",
    "test_no_committed_walk_reaches_the_quarantine.py",
    "test_no_settled_question_is_sent_to_adjudication.py",
    "test_ops_index_is_complete.py",
    "test_quarantine_register_identity_survives_migration.py",
    "test_recovery_anchor_is_clean.py",
    "test_review_artifacts_are_outcome_clean.py",
    "test_source_line_endings.py",
    "test_the_delivery_cannot_pin_itself.py",
    "test_the_main_block_is_last.py",
    "test_the_precommit_hook_is_installed.py",
    "test_the_ratified_preimage_is_reconstructible.py",
    "test_the_register_speaks_one_vocabulary.py",
    "test_the_review_round_cap_is_respected.py",
    "test_the_seat_ledger_ids_are_unique.py",
    "test_the_seat_ledger_is_not_shipped_to_seats.py",
)

#: Tier A, named for the record (informational marker; the gate runs every
#: file not in GOVERNANCE_FILES regardless). The 2026-09-05 public-release
#: inventory's PUBLIC_KEEP set.
VALIDITY_FILES = (
    "test_s0_config.py", "test_s0_context.py", "test_s0_dataset.py",
    "test_s0_evidence.py", "test_s0_gridmix.py", "test_s0_handoff.py",
    "test_s0_output_proof.py", "test_s0_report.py", "test_s0_runner.py",
    "test_s0_stability.py", "test_s0_stats.py", "test_s0_study.py",
    "test_features.py", "test_labels.py", "test_costs.py", "test_calendar.py",
    "test_f10_calendar.py", "test_dr2_vol_regime.py", "test_oracle.py",
    "test_dev_boundary.py", "test_loader.py",
    "test_cost_calibration_loader_boundaries.py",
    "test_bootstrap.py", "test_mc_atoms.py", "test_mc_consumer.py",
    "test_mc_convergence_provenance.py", "test_mc_fixed_world_selection.py",
    "test_mc_over_budget_predicate.py", "test_mc_battery_boundary.py",
    "test_mc_bundle_precheck.py", "test_mc_cold_replay.py",
    "test_mc_custody_calendar.py", "test_mc_feasibility_composition.py",
    "test_mc_feasibility_gates.py", "test_mc_node_integration.py",
    "test_mc_r2_2_integration.py", "test_mc_r2_3_evidence.py",
    "test_mc_bprov_seal_provenance.py", "test_mc_supplement_authority.py",
    "test_mc_supplement_provenance_battery.py",
    "test_mc_day_strata_supplement.py",
    "test_day_strata_context.py", "test_day_strata_pipeline.py",
    "test_day_strata_rows_producer.py", "test_run_c_build_2.py",
    "test_supplement_chain.py", "test_supplement_inputs.py",
    "test_m6_chain.py", "test_orchestrator.py",
    "test_platform_authoritative_events.py", "test_topstep.py",
    "test_lucid.py", "test_verdict.py", "test_runinfra.py",
    "test_resolve_partial_observed_behaviour.py",
    "test_symbology_rolls.py", "test_vol_threshold_population.py",
    "test_production_supplement_identity.py", "test_production_inputs.py",
    "test_execution_identity.py",
)


def tier_of(filename: str) -> str:
    """'governance' | 'validity' | 'safety' for a tests/ file name."""
    if filename in GOVERNANCE_FILES:
        return "governance"
    if filename in VALIDITY_FILES:
        return "validity"
    return "safety"
