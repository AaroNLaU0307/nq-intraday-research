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

#: Tier C. File names under tests/, exactly. Empty until P4.
GOVERNANCE_FILES = ()

#: Tier A, named for the record (informational marker; the gate runs every
#: file not in GOVERNANCE_FILES regardless).
VALIDITY_FILES = ()
