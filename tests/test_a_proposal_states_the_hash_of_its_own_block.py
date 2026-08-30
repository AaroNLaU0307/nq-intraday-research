"""A canonical block's stated hash must be the hash of the bytes beside it.

WHY THIS EXISTS. R4 v1 was blocked partly because I RECITED the block's
unchanged fields by hand and missed eight of them, so the text did not form a
hashable artifact at all. v2 generates the block instead, and states a
sha256. A stated hash that nobody recomputes is a claim, and this month has
been one long lesson about claims that were true when written.

WHAT IT CHECKS, and the order matters:

1. The ruled convention reproduces the ALREADY-APPROVED hash. If applying
   `CANONICAL_BYTES` to the R3 block does not yield c251335f, then the
   convention being used here is not the ruled one, and every other number
   below is computed the wrong way. That check comes first for that reason.
2. The proposal's own stated hash equals the hash of the block it carries.
3. The unchanged fields really are unchanged -- compared line by line against
   R3, not recited.

A GUARD, NOT A BUILDER. `scripts/r4v2_block_builder.py` builds and verifies;
this runs in the suite so the verification happens whether or not anyone
remembers to run the script.
"""

import hashlib
import re
import unittest
from pathlib import Path

OPS = Path(__file__).resolve().parent.parent / "ops"
R3_DOC = OPS / "PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md"
V2_DOC = OPS / "R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md"
R3_APPROVED = "c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483"


def block(document, marker):
    """The lines BETWEEN begin and end, exclusive -- the ruled convention."""
    lines = document.read_text(encoding="utf-8").split("\n")
    return lines[lines.index("BEGIN_" + marker) + 1:lines.index("END_" + marker)]


def canonical_sha256(lines):
    """`BEGIN 与 END 两行之间的行（不含这两行），LF 结尾，UTF-8，逐行原样`."""
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


class TestTheConventionIsTheRuledOne(unittest.TestCase):
    """First, because everything else is computed with it."""

    def test_it_reproduces_the_approved_R3_hash(self):
        self.assertEqual(
            R3_APPROVED, canonical_sha256(block(R3_DOC, "ND1_CR1_GRAMMAR_R3")),
            "applying the ruled CANONICAL_BYTES to the R3 block does not "
            "give the approved hash, so this file is hashing a different way "
            "than the approval did -- fix the convention, do not adjust the "
            "expected value")

    def test_the_block_is_not_empty(self):
        """Vacuity: an empty list hashes to a stable value and would sail
        through every comparison below."""
        self.assertGreater(len(block(R3_DOC, "ND1_CR1_GRAMMAR_R3")), 10)


class TestTheProposalStatesItsOwnHash(unittest.TestCase):

    def test_the_stated_sha256_is_the_hash_of_the_carried_block(self):
        text = V2_DOC.read_text(encoding="utf-8")
        stated = re.search(r"^R4_CANONICAL_SHA256=([0-9a-f]{64})$", text, re.M)
        self.assertIsNotNone(stated, "the proposal states no R4_CANONICAL_SHA256")
        self.assertEqual(
            stated.group(1), canonical_sha256(block(V2_DOC, "ND1_CR1_GRAMMAR_R4")),
            "the proposal states a hash that is not the hash of the block "
            "printed beside it. Whichever is stale, the bytes a reviewer "
            "reads and the value they are asked to approve are not the same "
            "thing.")

    def test_the_stated_byte_count_is_true_as_well(self):
        text = V2_DOC.read_text(encoding="utf-8")
        stated = re.search(r"^R4_CANONICAL_BYTE_COUNT=(\d+)$", text, re.M)
        self.assertIsNotNone(stated)
        lines = block(V2_DOC, "ND1_CR1_GRAMMAR_R4")
        self.assertEqual(int(stated.group(1)),
                         len(("\n".join(lines) + "\n").encode("utf-8")))

    def test_it_voids_the_hash_it_replaces(self):
        """Condition (a) of the ruling, checked rather than assumed."""
        text = V2_DOC.read_text(encoding="utf-8")
        self.assertIn(R3_APPROVED, text,
                      "the proposal replaces an approved block without "
                      "naming the hash it voids")


class TestTheUNCHANGEDFieldsReallyAre(unittest.TestCase):
    """Compared line by line against R3. v1's failure was reciting this set
    from memory and dropping eight of them."""

    def _pair(self):
        r3 = block(R3_DOC, "ND1_CR1_GRAMMAR_R3")
        v2 = block(V2_DOC, "ND1_CR1_GRAMMAR_R4")
        key = lambda line: line.split("=", 1)[0]
        return {key(l): l for l in r3}, {key(l): l for l in v2}

    def test_only_the_declared_fields_changed(self):
        r3, v2 = self._pair()
        changed = sorted(k for k in r3 if k in v2 and r3[k] != v2[k])
        self.assertEqual(
            ["CR1_REGISTRY_INTACT_COLD_RECOMPUTE",
             "CR1_REGISTRY_INTACT_PREIMAGE"], changed,
            "the set of changed fields is not the set the proposal declares")

    def test_no_field_was_dropped(self):
        r3, v2 = self._pair()
        self.assertEqual([], sorted(set(r3) - set(v2)),
                         "a field present in the approved block is missing "
                         "from the replacement")

    def test_exactly_one_field_was_added(self):
        r3, v2 = self._pair()
        self.assertEqual(["CR1_REGISTRY_REPOSITORY_ANCHOR"],
                         sorted(set(v2) - set(r3)))

    def test_the_comparison_covers_the_whole_block(self):
        """Vacuity: a key function that collapsed every line to one key would
        make the three assertions above trivially true."""
        r3, v2 = self._pair()
        self.assertEqual(len(r3), len(block(R3_DOC, "ND1_CR1_GRAMMAR_R3")))
        self.assertEqual(len(v2), len(block(V2_DOC, "ND1_CR1_GRAMMAR_R4")))


if __name__ == "__main__":
    unittest.main()
