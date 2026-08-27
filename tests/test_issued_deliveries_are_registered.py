"""A delivery that pins bytes must be registered while it is out.

THE INCIDENT THIS GENERALISES. Window-2 round 4 returned TRANSPORT_STOP: the
builder committed a change to a file the prompt had pinned, while a reviewer
was holding it. The sister repository had no freeze register; one was built
there the same day.

THE SAME ERROR REPEATED HOURS LATER, HERE. The S5/R4 decision packet went out
declaring five hashed artifacts, and this repository's register — which DOES
exist, and whose guards DO work — was empty. The mechanism was fine. The
discipline of arming it did not travel with the packet.

WHY THE EXISTING GUARDS COULD NOT CATCH IT. Every freeze guard begins
`if not entries: return`, which is correct: an empty register is the normal
state and most of the time nothing is out. So the whole family goes inert
exactly when a delivery is issued and not registered — the one case that
matters. Measured: 13 tests in this suite early-return on an empty register
or an empty document set.

WHAT THIS ASSERTS INSTEAD. A delivery document declares its own status. If it
says ISSUED, the register must be armed for its review_id. The register alone
could never know what was issued; the document knows, and now has to say.

Deliberately NOT inferred from timestamps or "most recent file" — a delivery
stays on disk after the review returns, so recency cannot distinguish
"issued and unregistered" from "returned and cleared". The status line is the
only thing that can, which is why it is required rather than optional.
"""

import io
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"
REGISTER = OPS / "ARTIFACTS_UNDER_REVIEW.json"

#: A document that pins other files' bytes is a delivery: it is telling a
#: reviewer "these exact bytes". Detected by the hash table, not by filename,
#: because the naming convention has drifted twice already.
_HASH_ROW = re.compile(r"\|\s*`([0-9a-f]{64})`\s*\|\s*`?(\d+)`?\s*\|")
_REVIEW_ID = re.compile(r"^REVIEW_ID=(\S+)", re.M)
#: WHAT `ISSUED` MEANS, because leaving it vague cost a red test within the
#: hour. It means FINALISED FOR HANDOVER: the bytes are the ones a seat will
#: hash, so they must not move. It does NOT mean "a seat is currently
#: reading it" — the builder cannot know that, and a definition that depends
#: on unobservable state cannot be enforced.
#:
#: The consequence is the one that bit: once a delivery is marked ISSUED and
#: registered, editing it requires clearing the register first. That is the
#: point. If the edit is legitimate, clearing costs one step; if it is not,
#: the guard is what stops it.
_STATUS = re.compile(r"^DELIVERY_STATUS=(ISSUED|RETURNED)\s*$", re.M)


def _deliveries():
    """Every ops document that pins at least two files by hash."""
    out = []
    for path in sorted(OPS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        rows = _HASH_ROW.findall(text)
        if len(rows) >= 2:
            out.append((path, text, rows))
    return out


def _entries():
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]


class TestEveryDeliveryDeclaresItsStatus(unittest.TestCase):

    def test_a_document_that_pins_bytes_says_whether_it_is_out(self):
        """Without this, the guard below cannot tell an unregistered live
        delivery from a returned one, and would have to guess."""
        missing = []
        for path, text, _rows in _deliveries():
            if not _STATUS.search(text):
                missing.append(path.relative_to(REPO).as_posix())
        self.assertEqual([], missing,
                         "these documents pin other files' bytes but declare "
                         "no DELIVERY_STATUS=ISSUED|RETURNED, so nothing can "
                         "tell whether a reviewer is holding them:\n  "
                         + "\n  ".join(missing))

    def test_a_delivery_that_pins_bytes_names_its_review(self):
        missing = []
        for path, text, _rows in _deliveries():
            if not _REVIEW_ID.search(text):
                missing.append(path.relative_to(REPO).as_posix())
        self.assertEqual([], missing,
                         "these deliveries declare no REVIEW_ID, so the "
                         "register cannot be keyed to them:\n  "
                         + "\n  ".join(missing))


class TestAnIssuedDeliveryIsArmed(unittest.TestCase):
    """THE ONE THAT WOULD HAVE CAUGHT TODAY'S REPEAT."""

    def test_every_issued_delivery_has_register_entries(self):
        live = {e["review_id"] for e in _entries()}
        unarmed = []
        for path, text, _rows in _deliveries():
            status = _STATUS.search(text)
            review = _REVIEW_ID.search(text)
            if not status or not review:
                continue          # the tests above own that failure
            if status.group(1) == "ISSUED" and review.group(1) not in live:
                unarmed.append(f"{path.relative_to(REPO).as_posix()} "
                               f"(review_id {review.group(1)})")
        self.assertEqual([], unarmed,
                         "these deliveries say ISSUED but the register is not "
                         "armed for them; a reviewer is holding bytes nothing "
                         "is protecting:\n  " + "\n  ".join(unarmed))

    def test_every_registered_review_has_a_delivery_that_claims_it(self):
        """The other direction. A register entry for a review nobody issued
        is a stale entry, and stale entries are how a register stops being
        believed."""
        claimed = set()
        for _path, text, _rows in _deliveries():
            review = _REVIEW_ID.search(text)
            status = _STATUS.search(text)
            if review and status and status.group(1) == "ISSUED":
                claimed.add(review.group(1))
        orphans = sorted({e["review_id"] for e in _entries()} - claimed)
        self.assertEqual([], orphans,
                         "the register is armed for reviews no ISSUED "
                         "delivery claims:\n  " + "\n  ".join(orphans))

    def test_an_issued_delivery_registers_the_files_it_pins(self):
        """Arming the register for the right review but the wrong files is
        the same hole one level down."""
        by_review = {}
        for entry in _entries():
            by_review.setdefault(entry["review_id"], set()).add(entry["path"])
        gaps = []
        for path, text, _rows in _deliveries():
            status = _STATUS.search(text)
            review = _REVIEW_ID.search(text)
            if not status or not review or status.group(1) != "ISSUED":
                continue
            registered = by_review.get(review.group(1), set())
            me = path.relative_to(REPO).as_posix()
            if me not in registered:
                gaps.append(f"{me}: the delivery document itself is not "
                            "registered under its own review_id, so the "
                            "bytes the reviewer was told to hash are "
                            "unprotected")
        self.assertEqual([], gaps, "\n  ".join(gaps))


if __name__ == "__main__":
    unittest.main()
