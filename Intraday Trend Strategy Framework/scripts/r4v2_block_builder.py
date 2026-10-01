"""Build the R4 v2 canonical block and hash it under the RULED convention.

The convention is not guessed: `CANONICAL_BYTES=BEGIN 与 END 两行之间的行
（不含这两行），LF 结尾，UTF-8，逐行原样`, and applying it to the R3 block
reproduces c251335f... exactly. The same code path produces both hashes here,
so the new one cannot be computed a different way from the one it replaces.
"""
import hashlib
import io
from pathlib import Path

SRC = Path(r"C:\Users\Aaron\OneDrive\Desktop\Quant trade"
           r"\Intraday Trend Strategy Framework\ops"
           r"\PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md")

lines = SRC.read_text(encoding="utf-8").split("\n")
begin = lines.index("BEGIN_ND1_CR1_GRAMMAR_R3")
end = lines.index("END_ND1_CR1_GRAMMAR_R3")
r3 = lines[begin + 1:end]


def canonical(inner):
    return ("\n".join(inner) + "\n").encode("utf-8")


assert hashlib.sha256(canonical(r3)).hexdigest() == (
    "c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483"), (
    "the convention does not reproduce the approved hash; stop and re-read "
    "CANONICAL_BYTES rather than inventing a variant")

ANCHOR = (
    "CR1_REGISTRY_REPOSITORY_ANCHOR=the registry repository is identified in "
    "TWO parts and they are not the same thing. DISCOVERY: the framework "
    "repository's ops/TRIAL_REGISTRY.md is a tombstone bearing "
    "REGISTRY_MOVED_NOT_A_REGISTRY and stating where the registry repository "
    "is; that stated location is the ONLY means of finding it, it is machine-"
    "specific, and if the repository is moved without the tombstone being "
    "updated a cold reader cannot find it - this residual is NOT closed by "
    "this grammar and moving the repository is therefore a governed act that "
    "must update the tombstone. VERIFICATION: once found, the repository is "
    "confirmed by the S4 cross-pin ruled in dec-registry-migration-2026-08-27 "
    "- it contains commit N1 carrying ops/TRIAL_REGISTRY.md, and N1's message "
    "names the framework repository's pre-migration HEAD O0. A commit hash "
    "confirms identity inside an object database already located; it cannot "
    "locate one")

PREIMAGE = (
    "CR1_REGISTRY_INTACT_PREIMAGE=the complete on-disk bytes of "
    "ops/TRIAL_REGISTRY.md IN THE REGISTRY REPOSITORY "
    "(CR1_REGISTRY_REPOSITORY_ANCHOR), read once, immediately BEFORE the CR1 "
    "row is appended; no normalization, no encoding change, no line-ending "
    "rewrite; the value is therefore never part of its own preimage. WHICH "
    "REPOSITORY is a repository-selection criterion, not a restatement of the "
    "intact criterion: a file at the same relative path in the framework "
    "repository is the tombstone, which parses as an empty registry and would "
    "therefore FAIL the intact criterion against any non-empty witness rather "
    "than pass it. The hazard is not that a tombstone looks intact - it is "
    "that a reader who never applies the witness criterion never finds out")

COLD = (
    "CR1_REGISTRY_INTACT_COLD_RECOMPUTE=the preimage is recoverable from git "
    "history of ops/TRIAL_REGISTRY.md at the commit preceding this row, and "
    "the witness file is append-only, so a cold reader can recompute both "
    "sides. WHICH history: N1 is the commit that first carries the file in "
    "the registry repository, its parent carries no such file, and N1 "
    "appended no CR1 row - it moved a file. So rows appended STRICTLY AFTER "
    "N1 recompute in the registry repository, and rows appended at or before "
    "O0 recompute in the framework repository, whose blobs remain in place "
    "because the migration rewrote no history")

v2 = []
for line in r3:
    if line.startswith("CR1_REGISTRY_INTACT_PREIMAGE="):
        v2.append(PREIMAGE)
        v2.append(ANCHOR)            # the anchor the preimage now cites
    elif line.startswith("CR1_REGISTRY_INTACT_COLD_RECOMPUTE="):
        v2.append(COLD)
    else:
        v2.append(line)              # every other field VERBATIM

untouched = [a for a, b in zip(r3, [x for x in v2 if x != ANCHOR]) if a == b]
print("R3 lines            :", len(r3))
print("v2 lines            :", len(v2), "(one added: the anchor)")
print("carried VERBATIM    :", len(untouched), "of", len(r3))
changed = [a for a, b in zip(r3, [x for x in v2 if x != ANCHOR]) if a != b]
print("changed fields      :", [c.split("=")[0] for c in changed])
body = canonical(v2)
print()
print("R4_V2_CANONICAL_SHA256 =", hashlib.sha256(body).hexdigest())
print("R4_V2_CANONICAL_BYTES  =", len(body))
# VERIFY AGAINST THE PROPOSAL rather than writing a second copy. The block
# already lives inside R4_PROPOSAL_V2, which is the artifact under review. A
# second file on disk would be a mirror of derived data, and mirrors are what
# keep going stale here -- v1 died on exactly that.
proposal = SRC.parent / "R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md"
plines = proposal.read_text(encoding="utf-8").split("\n")
inner = plines[plines.index("BEGIN_ND1_CR1_GRAMMAR_R4") + 1:
               plines.index("END_ND1_CR1_GRAMMAR_R4")]
print()
print("the proposal's block matches this build:", inner == v2)
print("re-hashed from the proposal            :",
      hashlib.sha256(canonical(inner)).hexdigest())
assert inner == v2, (
    "the proposal's block is not what this script builds. One of them is "
    "stale, so the hash under review is not the hash of the reviewed bytes.")
