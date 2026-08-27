"""N09 R3 §2–§3 — the two layers that sit on top of the approved enums.

WHY THEY ARE LAYERS AND NOT EDITS. `GATE_TABLE` is an approved closed enum.
Both problems below are about how gates are DISPATCHED and how their
refusals are ROUTED, not about which gates exist — so they are separate
mappings over the same names. Editing the enum would be an R4-level act.

CHECKPOINT_OF closes R2's HOLD. R2 asserted one zero-side-effect rule across
all five C_BUILD gates. That is false by construction for two of them:
staging writes `.partial` before it can verify it, and by the archive gate
the archive attempt has already happened. Three moments, three different
invariants.

ROUTER_OF closes a defect measured while transcribing CR1:
`archive_policy_a` is a GATE, so its refusal routes through
`plan_failure_event` to F2 — while ratified `ND1_ARCHIVE_FAILURE_POLICY=A`
requires A1. `test_routing_it_as_an_ordinary_gate_contradicts_policy_a` in
the R3-facts file executes that contradiction; this file is the layer that
resolves it.

SCOPE. Structure only. Nothing here derives a row, seals, archives, or
appends anything — the buildable scope is still the restrictive reading of
the ruling's closing line, and the wide/narrow question is out for decision.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import supplement_contract as sc


class TestTheApprovedEnumIsUntouched(unittest.TestCase):
    """The property that makes these layers legitimate at all."""

    def test_gate_table_still_holds_exactly_its_ratified_members(self):
        self.assertEqual(13, len(sc.GATE_TABLE["A_PRECHECK"]))
        self.assertEqual(5, len(sc.GATE_TABLE["B_DERIVE"]))
        self.assertEqual(5, len(sc.GATE_TABLE["C_BUILD"]))

    def test_the_layers_add_no_gate_and_remove_none(self):
        declared = {g for stage in sc.STAGE_ENUM for g in sc.GATE_TABLE[stage]}
        self.assertTrue(set(sc.CHECKPOINT_OF) <= declared,
                        "CHECKPOINT_OF names a gate the enum does not")
        self.assertTrue(set(sc.ROUTER_OF) <= declared,
                        "ROUTER_OF names a gate the enum does not")


class TestCheckpointDispatch(unittest.TestCase):

    def test_the_three_moments_partition_c_build_exactly(self):
        """A partition, not a covering: every C_BUILD gate has exactly one
        moment, and no moment is empty."""
        by_moment = {}
        for gate in sc.GATE_TABLE["C_BUILD"]:
            by_moment.setdefault(sc.checkpoint_of(gate), []).append(gate)
        self.assertEqual(
            {sc.CHECKPOINT_C_BUILD_1: ["row_schema_blind", "day_set_exact",
                                       "rows_digest_recompute"],
             sc.CHECKPOINT_C_BUILD_2: ["seal_staging_partial"],
             sc.CHECKPOINT_C_BUILD_3: ["archive_policy_a"]},
            {k: sorted(v, key=sc.GATE_TABLE["C_BUILD"].index)
             for k, v in by_moment.items()})

    def test_asking_a_non_c_build_gate_refuses(self):
        """Checkpoints partition C_BUILD only. Returning None for the other
        eighteen gates would read as 'no checkpoint needed' rather than
        'the question does not apply'."""
        for gate in ("g9_hard_blocker", "source_bundle_digest", "git_clean"):
            with self.assertRaises(sc.SupplementGrammarError):
                sc.checkpoint_of(gate)


class TestRouting(unittest.TestCase):

    def test_the_archive_gate_routes_to_the_post_seal_router(self):
        """THE defect this layer exists for. Ratified policy A: a local seal
        that succeeded while the archive failed becomes A1, never F2."""
        self.assertEqual(sc.ROUTER_POST_SEAL,
                         sc.router_of("archive_policy_a"))

    def test_every_other_gate_routes_to_the_failure_router(self):
        declared = [g for stage in sc.STAGE_ENUM for g in sc.GATE_TABLE[stage]]
        others = [g for g in declared if g != "archive_policy_a"]
        self.assertEqual(22, len(others))
        for gate in others:
            self.assertEqual(sc.ROUTER_GATE_FAILURE, sc.router_of(gate), gate)

    def test_an_undeclared_gate_refuses_rather_than_defaulting_to_a(self):
        """A typo that defaulted to router A would send an archive failure
        to F2 silently — the exact defect, reintroduced through a spelling
        mistake."""
        for bad in ("archive_policy", "Archive_Policy_A", "", "no_such_gate"):
            with self.assertRaises(sc.SupplementGrammarError,
                                   msg=f"{bad!r} was routed"):
                sc.router_of(bad)

    def test_router_b_is_used_by_exactly_one_gate(self):
        """If a second gate ever needs router B, that is a design change
        worth noticing rather than absorbing."""
        declared = [g for stage in sc.STAGE_ENUM for g in sc.GATE_TABLE[stage]]
        on_b = [g for g in declared
                if sc.router_of(g) == sc.ROUTER_POST_SEAL]
        self.assertEqual(["archive_policy_a"], on_b)


class TestTheLayersDoNotExecuteAnything(unittest.TestCase):
    """Scope, asserted rather than promised."""

    def test_the_c_build_gates_all_still_refuse(self):
        from itsf.mc import supplement_runner as sr
        ctx = sr.GateContext(supplement_id="MC-DS-S001", head_commit="0" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        for gate in sc.GATE_TABLE["C_BUILD"]:
            with self.assertRaises(sr.SupplementRunnerError, msg=gate):
                sr.GATES[gate](ctx)

    def test_the_layers_are_pure_lookups(self):
        """No I/O, no state: the same question twice gives the same answer,
        and neither call can have touched anything."""
        for gate in sc.GATE_TABLE["C_BUILD"]:
            self.assertEqual(sc.checkpoint_of(gate), sc.checkpoint_of(gate))
            self.assertEqual(sc.router_of(gate), sc.router_of(gate))


if __name__ == "__main__":
    unittest.main()
