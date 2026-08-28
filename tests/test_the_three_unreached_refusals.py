"""Three refusals no test literal could match, now exercised.

FOUND by scanning every `raise SomeError("code", ...)` in `src/` and asking
which codes no test string literal can match. THE SCAN WAS WRONG THE FIRST
TIME, and the correction matters more than the result:

    exact-string absence          59 codes "never mentioned"
    regex-search semantics         3 codes

`pytest.raises(..., match="duplicate_minute_slot")` is a re.search, so a
partial literal matches the full code. Checking for the whole code string
counted every partial match as a miss — off by a factor of ~19. On the
first count `src/itsf/s0/costs.py` looked like 6-of-6 uncovered and was
about to be written up; all six are matched by partial literals.

That near-miss is the same shape as §12.5 of the N09 design: measure one
thing (the exact string is absent), state another (it is untested). Caught
by opening the test file instead of trusting the scan.

WHAT THIS FILE DOES NOT CLAIM. A literal that COULD match is not proof the
raise is reached; only line coverage settles that. These three are the ones
where no literal could match at all — a lower bound on the gap, not the
gap.

    atoms.atom_canonical_dict         atom_type_violation
    cold_reducer.parse_jsonl          cold_trace_not_text
    supplement_contract.checkpoint_of gate_not_in_c_build

None of them is a defect. Each is an input-validation refusal that nothing
had ever run. A refusal nobody has executed is a refusal nobody has seen
work.
"""

import unittest

from itsf.mc import atoms, cold_reducer, supplement_contract as sc


class TestAtomTypeViolation(unittest.TestCase):
    """`atom_canonical_dict` insists on the exact type, not a duck.

    `type(atom) is not SimulationPathObservation` — an identity check, so a
    subclass is refused too. That is deliberate: the canonical dict feeds
    sealed bytes, and a subclass could carry extra state that the field
    walk silently drops."""

    def test_a_plain_mapping_is_refused(self):
        with self.assertRaises(atoms.MCInputError) as caught:
            atoms.atom_canonical_dict({"schema": "whatever"})
        self.assertIn("atom_type_violation", str(caught.exception))

    def test_the_message_names_the_type_it_got(self):
        try:
            atoms.atom_canonical_dict(object())
        except atoms.MCInputError as exc:
            text = str(exc)
        self.assertIn("object", text)
        self.assertIn("not an atom", text)

    def test_none_is_refused_rather_than_returning_an_empty_dict(self):
        with self.assertRaises(atoms.MCInputError):
            atoms.atom_canonical_dict(None)

    def test_a_subclass_is_refused_too(self):
        """The identity check, asserted as intent rather than left as an
        accident of `is`. If this ever becomes `isinstance`, a subclass
        with extra state would serialise as its parent and the sealed
        bytes would silently lose it."""

        class Sneaky(atoms.SimulationPathObservation):
            pass

        with self.assertRaises(atoms.MCInputError):
            atoms.atom_canonical_dict(Sneaky.__new__(Sneaky))


class TestColdTraceNotText(unittest.TestCase):
    """`parse_jsonl` refuses bytes rather than decoding them.

    Decoding here would pick an encoding, and the trace is sealed bytes
    whose canonical form is defined elsewhere. Guessing is how two
    components end up disagreeing about what the trace said."""

    def test_bytes_are_refused_not_decoded(self):
        with self.assertRaises(cold_reducer.ColdReducerError) as caught:
            cold_reducer.parse_jsonl(b'{"a": 1}\n')
        self.assertIn("cold_trace_not_text", str(caught.exception))

    def test_the_message_names_the_type(self):
        try:
            cold_reducer.parse_jsonl(b"")
        except cold_reducer.ColdReducerError as exc:
            self.assertIn("bytes", str(exc))

    def test_none_is_refused(self):
        with self.assertRaises(cold_reducer.ColdReducerError):
            cold_reducer.parse_jsonl(None)

    def test_a_real_trace_still_parses(self):
        """The over-reach this guard invites: refusing valid input.

        The row needs the atom schema — my first version used `{"a": 1}`
        and hit `cold_trace_schema`, which proved the schema check works
        rather than that text is accepted. Building the row from the
        module's own constant keeps it true if the schema is versioned."""
        schema = cold_reducer._ATOM_SCHEMA
        text = ('{"schema": %s, "a": 1}\n{"schema": %s, "a": 2}\n'
                % (repr(schema).replace("'", '"'),
                   repr(schema).replace("'", '"')))
        rows = cold_reducer.parse_jsonl(text)
        self.assertEqual(2, len(rows))
        self.assertEqual([schema, schema], [r["schema"] for r in rows])


class TestGateNotInCBuild(unittest.TestCase):
    """`checkpoint_of` partitions C_BUILD only. Asking about another
    stage's gate is a refusal, not `None` — because `None` would flow on
    and be compared against a real checkpoint somewhere downstream."""

    def _a_gate_outside_c_build(self):
        for stage, gates in sc.GATE_TABLE.items():
            if stage == "C_BUILD":
                continue
            for gate in gates:
                if gate not in sc.GATE_TABLE["C_BUILD"]:
                    return gate
        self.skipTest("every declared gate is a C_BUILD gate")

    def test_a_gate_from_another_stage_is_refused(self):
        gate = self._a_gate_outside_c_build()
        with self.assertRaises(sc.SupplementGrammarError) as caught:
            sc.checkpoint_of(gate)
        self.assertIn("gate_not_in_c_build", str(caught.exception))

    def test_the_message_says_checkpoints_partition_c_build(self):
        try:
            sc.checkpoint_of(self._a_gate_outside_c_build())
        except sc.SupplementGrammarError as exc:
            self.assertIn("partition C_BUILD only", str(exc))

    def test_every_c_build_gate_still_answers(self):
        """The partition claim, checked in the direction that matters: if
        a C_BUILD gate had no checkpoint, this refusal would be masking a
        missing entry rather than guarding a boundary."""
        for gate in sc.GATE_TABLE["C_BUILD"]:
            with self.subTest(gate=gate):
                self.assertIn(sc.checkpoint_of(gate), sc.CHECKPOINT_OF.values())

    def test_an_undeclared_name_hits_the_same_refusal(self):
        with self.assertRaises(sc.SupplementGrammarError):
            sc.checkpoint_of("no_such_gate_anywhere")


if __name__ == "__main__":
    unittest.main()
