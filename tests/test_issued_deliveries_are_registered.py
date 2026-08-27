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


def _settled_in_head(rel):
    """Is this delivery's content already settled in HEAD — same bytes?

    THE DEADLOCK THIS RESOLVES. A delivery must be registered, and a register
    entry needs `unchanged_since`: the commit that last touched the path. That
    commit is the one being made. So arming ALWAYS lags the delivery's own
    commit by exactly one commit — that is the workflow, not a shortcut, and
    without an exemption no delivery could ever be committed without
    `--no-verify`. A rule whose normal use requires bypassing it is not a rule.

    HIT TWICE, WIDENED ONCE. The first version asked only "does HEAD have this
    path", which covered CREATING a delivery and not RE-ISSUING one: a packet
    already in HEAD, retracted for repair, is ISSUED-and-unarmed at the moment
    its repair is committed. Same wall, one hour later.

    So the exemption is: the bytes are changing in THIS commit. It closes the
    instant they stop, which is the next commit, always.

    NOT a standing loophole. Staying exempt would mean editing the delivery in
    every single commit — and the bytes a reviewer holds changing on every
    commit is the incident itself, not a way around it.
    """
    import subprocess
    out = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel],
                         capture_output=True)
    if out.returncode != 0:
        return False                      # not in HEAD at all: being created
    try:
        now = (REPO / rel).read_bytes()
    except OSError:
        return False
    nl = b"\r\n"
    return out.stdout.replace(nl, b"\n") == now.replace(nl, b"\n")


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
            rel = path.relative_to(REPO).as_posix()
            if not _settled_in_head(rel):
                continue          # see _settled_in_head
            if status.group(1) == "ISSUED" and review.group(1) not in live:
                unarmed.append(f"{rel} (review_id {review.group(1)})")
        self.assertEqual([], unarmed,
                         "these deliveries say ISSUED but the register is not "
                         "armed for them; a reviewer is holding bytes nothing "
                         "is protecting:\n  " + "\n  ".join(unarmed))

    def test_the_new_file_exemption_is_exactly_one_commit_wide(self):
        """The exemption in `_settled_in_head` is the only way past this guard, so
        its width is the thing to prove rather than assert.

        Measured against the repository itself: every delivery that HAS been
        committed is subject to the check. If that set were empty the
        exemption would be unbounded and nobody would notice, because the
        guard above would simply skip everything."""
        committed = [p.relative_to(REPO).as_posix()
                     for p, _t, _r in _deliveries()
                     if _settled_in_head(p.relative_to(REPO).as_posix())]
        self.assertGreater(
            len(committed), 8,
            f"only {len(committed)} deliveries are in HEAD; the new-file "
            "exemption is covering more than it should")

    def test_a_delivery_in_head_is_not_exempt(self):
        """Directly: pick a committed ISSUED delivery and confirm `_settled_in_head`
        says so, i.e. it went through the check rather than around it."""
        issued_in_head = [
            p.relative_to(REPO).as_posix()
            for p, t, _r in _deliveries()
            if (_STATUS.search(t) and _STATUS.search(t).group(1) == "ISSUED"
                and _settled_in_head(p.relative_to(REPO).as_posix()))]
        armed = {e["review_id"] for e in _entries()}
        for rel in issued_in_head:
            text = (REPO / rel).read_text(encoding="utf-8")
            self.assertIn(_REVIEW_ID.search(text).group(1), armed,
                          f"{rel} is committed, ISSUED, and unarmed — the "
                          "exemption did not cover it and must not")

    def test_no_armed_review_already_has_a_verdict_on_disk(self):
        """THE ONE THAT WOULD HAVE CAUGHT THREE OF TODAY'S FOUR REPEATS.

        The pattern, four times on 2026-08-27: a review returns, the builder
        starts repairing what it found, and the register is still armed on
        the very files being repaired. The freeze guard catches it — after
        the edits, sometimes minutes later, once at full-machine-check time.
        The rule it enforces is right; what was missing is the rule ABOUT
        the rule:

            a review whose verdict is already on disk is over,
            and an over review must not still be armed.

        Detected without inventing a convention: an outcome record is an
        ops document that names the review_id and carries a RULING= or
        VERDICT= line, and is not the delivery document itself. Once that
        exists the register entry is stale by construction — nobody holds
        those bytes any more, and leaving them frozen only means the next
        repair collides with a review that already finished.

        Ordering, written down so it stops being folklore:
        verdict returns -> clear the register -> then repair.
        """
        entries = _entries()
        if not entries:
            return
        # This guard's own premise. `test_no_vacuous_guards` flagged the
        # sister-repository version of it within minutes of it being
        # written, for asserting over a glob it never proved was non-empty.
        records = sorted(OPS.glob("*.md"))
        self.assertGreater(len(records), 40,
                           "the verdict scan reached %d ops records; at that "
                           "count it proves nothing" % len(records))
        armed = {e["review_id"] for e in entries}
        docs = {e["path"] for e in entries
                if e.get("role", "delivery") == "delivery"}
        verdict = re.compile(r"^(RULING|VERDICT)=", re.M)
        over = set()
        for path in records:
            rel = path.relative_to(REPO).as_posix()
            if rel in docs:
                continue
            text = path.read_text(encoding="utf-8")
            review = _REVIEW_ID.search(text)
            if not review or review.group(1) not in armed:
                continue
            if verdict.search(text):
                over.add("%s: already ruled in %s" % (review.group(1), rel))
        self.assertEqual([], sorted(over),
                         "the register is armed for reviews that are already "
                         "over; clear it BEFORE repairing, not after the "
                         "freeze guard notices:\n  " + "\n  ".join(sorted(over)))

    def test_every_registered_review_has_a_delivery_that_claims_it(self):
        """The other direction. A register entry for a review nobody issued
        is a stale entry, and stale entries are how a register stops being
        believed."""
        claimed = set()
        for _path, text, _rows in _deliveries():
            review = _REVIEW_ID.search(text)
            status = _STATUS.search(text)
            if review and status and status.group(1) == "ISSUED":
                claimed.add(review.group(1))   # armed-or-not, it is live
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
            if not _settled_in_head(me):
                continue
            if me not in registered:
                gaps.append(f"{me}: the delivery document itself is not "
                            "registered under its own review_id, so the "
                            "bytes the reviewer was told to hash are "
                            "unprotected")
        self.assertEqual([], gaps, "\n  ".join(gaps))


if __name__ == "__main__":
    unittest.main()
