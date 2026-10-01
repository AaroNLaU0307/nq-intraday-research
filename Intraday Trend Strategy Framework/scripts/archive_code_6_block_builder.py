"""Build the canonical block for the sixth ARCHIVE_CODE amendment.

WHY A BUILDER AND NOT TYPING. R4 v1 was HOLD'd partly because its block was
RECITED by hand and eight fields were missed, so the text never formed a
hashable artifact. The block is generated here and its sha256 computed from
the same bytes, under the ruled convention:

    the lines BETWEEN `BEGIN_<MARKER>` and `END_<MARKER>` (exclusive),
    joined with LF, LF-terminated, UTF-8, verbatim per line.

`tests/test_a_proposal_states_the_hash_of_its_own_block.py` enforces that
convention against the already-approved R3 hash before trusting anything
else, so a number produced here is checked against a known-good baseline
rather than against itself.

RUNS NOTHING, AUTHORIZES NOTHING. It prints a block and a digest.
"""
from __future__ import annotations

import hashlib
import sys

MARKER = "ARCHIVE_CODE_6_CANONICAL_BLOCK"

#: The sixth member. Named for the STRUCTURAL FACT it records, in the same
#: shape as the five it joins. It is spelled exactly like the C_BUILD_3
#: finding that produces it, deliberately: a translation table between two
#: names for one fact is a place for drift, and this repository has paid for
#: drift between a name and its meaning more than once this month.
NEW_CODE = "archived_bytes_deleted"

BLOCK = [
    "AMENDMENT_ID=ARCHIVE-CODE-6",
    "AMENDS=supplement_contract.ARCHIVE_CODES  (ratified CLOSED enum,",
    "       ND1 §D.3.2 P4 `ARCHIVE_CODE_ENUM`)",
    "STATUS=PROPOSED  (not approved; nothing implemented)",
    "",
    "# ---- 1. THE ENUM GAINS ONE MEMBER -------------------------------",
    "ARCHIVE_CODES_BEFORE=inventory_unavailable, file_unreadable,",
    "                     file_digest_mismatch, set_equality_refused,",
    "                     set_equality_unreached",
    "ARCHIVE_CODES_AFTER=inventory_unavailable, file_unreadable,",
    "                    file_digest_mismatch, set_equality_refused,",
    "                    set_equality_unreached, " + NEW_CODE,
    "NEW_MEMBER=" + NEW_CODE,
    "",
    "# ---- 2. THE ENUM'S DOCUMENTED INVARIANT WIDENS -------------------",
    "# The five existing members carry a stated property: each maps to a",
    "# STRUCTURALLY DISTINGUISHABLE state of an `ArchiveReport`, and",
    "# `classify_archive_report` is the ONE classifier that produces them.",
    "# The new member does NOT satisfy that: the report says `archive_ok`",
    "# while the C_BUILD_3 checkpoint finds bytes archived by an EARLIER",
    "# run are gone. Adding the member without saying so would leave the",
    "# enum asserting something false about itself.",
    "INVARIANT_BEFORE=every member is produced by classify_archive_report",
    "                 from a structurally distinguishable ArchiveReport state",
    "INVARIANT_AFTER=every member is produced EITHER by",
    "                classify_archive_report from a structurally",
    "                distinguishable ArchiveReport state, OR by the C_BUILD_3",
    "                checkpoint from a recomputation the report does not",
    "                cover. Each member names which of the two produces it.",
    "PRODUCER_OF_NEW_MEMBER=C_BUILD_3 checkpoint (day_strata_pipeline",
    "                       .run_c_build_3), NOT classify_archive_report",
    "",
    "# ---- 3. THE NEW MEMBER'S ONLY EXIT IS AX -------------------------",
    "# A1 has two exits: A2 (recovered) and AX (permanently failed -> F3).",
    "# A2 asserts `source_and_archive_exact_inventory_match` and",
    "# `per_file_sha256_match` for THIS run's copy, and says nothing about",
    "# bytes an earlier run archived -- so it could declare recovery while",
    "# the loss stands. That must be impossible, not merely discouraged.",
    "A2_FORBIDDEN_FOR=" + NEW_CODE,
    "AX_IS_THE_ONLY_EXIT_FOR=" + NEW_CODE,
    "MECHANISM=a new mapping layered OVER the closed enum, in the manner",
    "          `CHECKPOINT_OF` and `ROUTER_OF` already use. The transition",
    "          planner keys on (from_short_id, outcome) and cannot see an",
    "          archive_code today, so the constraint cannot live there",
    "          without changing that signature.",
    "",
    "# ---- 4. WHAT IS NOT AMENDED --------------------------------------",
    "EVENTS_TABLE=unchanged",
    "TRANSITION_PLANNER_EDGES=unchanged  (A1 -> AX already exists)",
    "A2_REQUIRED_FIELDS=unchanged",
    "ROUTER_OF=unchanged  (archive_policy_a stays with Router B)",
    "GATE_TABLE=unchanged",
    "VERIFICATION_FAILURE_CODES=unchanged",
    "",
    "# ---- 5. WHAT APPROVING THIS DOES NOT AUTHORIZE -------------------",
    "NOT_AUTHORIZED=real Development data read; supplement execution;",
    "               live P2; directory creation under the governed roots;",
    "               strategy build; any registry append",
]


def canonical_sha256(lines) -> str:
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def main() -> int:
    print("BEGIN_" + MARKER)
    for line in BLOCK:
        print(line)
    print("END_" + MARKER)
    print()
    print("CANONICAL_SHA256=" + canonical_sha256(BLOCK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
