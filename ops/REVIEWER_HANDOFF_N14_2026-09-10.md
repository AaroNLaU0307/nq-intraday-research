# REVIEWER HANDOFF -- N14 -- SUPERSEDED BY THE CARRIER'S SECTION 0-A

```
RECORD_TYPE=POINTER
STATUS=SUPERSEDED_SAME_DAY, content moved rather than withdrawn
MOVED_TO=ops/OFF_LIMITS_N14_EXACT_TREE_2026-09-10.md section 0-A
```

**The reviewer-facing payload for N14 is section 0-A of the read-allowlist
carrier**, `ops/OFF_LIMITS_N14_EXACT_TREE_2026-09-10.md`. What the Owner sends is
the text inside the fence between `BEGIN PASTE BLOCK` and `END PASTE BLOCK` there,
and nothing else.

**Why it moved, in one line:** a review may register exactly one delivery document
and pin derivation excludes exactly that one, so only one file can state the freeze
pin truthfully -- and the file that pins the 93 allowlisted paths has to be it. The
payload therefore lives inside the document that defines the read surface rather
than beside it, which is strictly better: it is not merely *on* the surface, it *is*
part of it. Recorded as `DEC-N14-ATTEMPT1-4`.

This file pins no bytes and instructs no one. It exists so that the committed ledger
rows citing this path still resolve; a reader who follows one arrives here and is
sent to the right place, which is the whole job of a pointer.
