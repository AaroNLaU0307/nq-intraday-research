"""Artifacts handed to a reviewer must not move while the review is out.

WHY THIS EXISTS — a real failure, 2026-08-24. A delegated Sol session was
given four anchor files by SHA-256. Its opening precheck matched all four.
While it worked, the builder (me) appended a new section to one of them
and committed twice more. Its closing recheck found:

    EXPECTED 8DC87212...  ACTUAL E2493F1A...
    HEAD_AT_START 154c9b73  HEAD_AT_FINAL_RECHECK 79a05390
    STATUS=STOP_HASH_MISMATCH   DELEGATED_RULING_ISSUED=NO

The reviewer behaved correctly and stopped. A whole review session was
spent and produced no filable ruling, because of a builder-side edit.

The standing artifact-transport rule says an artifact must exist as a
durable file with a recorded hash and that the receiver must recompute it.
It does NOT say the sender must then leave it alone -- that was the gap,
and "I will remember" is not a control. New findings during a review go
into a NEW record, the way registry corrections do.

TO USE: add an entry when you hand an artifact to a reviewer; delete the
entry when the review returns. An empty register is the normal state.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REGISTER = Path(__file__).resolve().parent.parent / "ops" / \
    "ARTIFACTS_UNDER_REVIEW.json"


def _entries():
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]


def test_every_artifact_under_review_still_hashes_to_what_was_sent():
    repo = REGISTER.parent.parent
    moved = []
    for e in _entries():
        target = repo / e["path"]
        if not target.exists():
            moved.append(f"{e['path']}: MISSING (sent to {e['issued_to']})")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual.lower() != e["sha256"].lower():
            moved.append(
                f"{e['path']}: sent {e['sha256'][:16]}... to "
                f"{e['issued_to']} on {e['issued_at']}, now "
                f"{actual[:16]}...")
    assert not moved, (
        "an artifact moved while a reviewer holds it -- their recheck will "
        "STOP and the review is wasted:\n  " + "\n  ".join(moved)
        + "\n\nPut new findings in a NEW record. If the review has already "
          "returned, remove the entry from ops/ARTIFACTS_UNDER_REVIEW.json.")


def test_the_register_is_well_formed():
    """A malformed register silently guards nothing."""
    for e in _entries():
        for field in ("path", "sha256", "issued_to", "issued_at",
                      "review_id", "unchanged_since"):
            assert e.get(field), f"entry missing {field!r}: {e}"
        assert len(e["sha256"]) == 64, e["sha256"]
        assert re.fullmatch(r"[0-9a-f]{40}", e["unchanged_since"]), \
            e["unchanged_since"]


def _git(repo, *args) -> str:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                         text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def derive_pin(repo, paths) -> str:
    """THE pin for a review set, derived — never typed.

    A pin is only meaningful if it is at or after every reviewed path's
    last change. Typing one invites the failure it is supposed to prevent,
    so it is computed from git: the most recent among each path's
    last-change commit. `git log <pin>..HEAD -- <paths>` is then empty by
    construction.

    Refuses a path that has never been committed. That refusal is the
    load-bearing part: it makes the sequencing mistake IMPOSSIBLE rather
    than merely detectable. You cannot pin an untracked file, so the
    reviewed artifacts must be committed BEFORE the register and the
    prompt are written — which is exactly the order that keeps the pin
    true.
    """
    last = {}
    for path in paths:
        commit = _git(repo, "log", "-1", "--format=%H", "--", path)
        assert commit, (
            f"{path} has never been committed, so it cannot be pinned. "
            "Commit the reviewed artifacts FIRST, then register them.")
        last[path] = commit
    return max(last.values(),
               key=lambda c: int(_git(repo, "log", "-1", "--format=%ct", c)))


def test_the_pin_is_the_derived_one_not_a_typed_one():
    """MEASURED FAILURE, 2026-08-25 — the third transport stop in one day.

    I registered six artifacts with `unchanged_since` set to the then-HEAD,
    ran this file's guards, saw them pass, committed, and handed over. A
    fresh Sol stopped: the range was not empty.

    The pin was wrong the moment it was written — one reviewed artifact did
    not exist at that commit. And the range guard could not catch it: at the
    time I ran it, nothing had been committed, so the range was TRIVIALLY
    empty. A guard checked at a moment when it cannot fail is not a check.

    This test closes that by construction. The pin is recomputed from git
    every run, so a hand-typed, stale, or too-early value fails immediately
    — including a value that happens to leave the range empty."""
    repo = REGISTER.parent.parent
    entries = _entries()
    if not entries:
        return

    by_review = {}
    for e in entries:
        by_review.setdefault(e["review_id"], []).append(e)

    wrong = []
    for review_id, group in sorted(by_review.items()):
        declared = {e["unchanged_since"] for e in group}
        if len(declared) != 1:
            wrong.append(f"{review_id}: {len(declared)} different pins in "
                         "one review set")
            continue
        expected = derive_pin(repo, [e["path"] for e in group])
        if declared.pop() != expected:
            wrong.append(f"{review_id}: pinned "
                         f"{group[0]['unchanged_since'][:12]}, derived "
                         f"{expected[:12]}")
    assert not wrong, (
        "a review pin disagrees with the one git derives; the reviewer's "
        "history check will not be empty:\n  " + "\n  ".join(wrong))


def test_no_commit_has_touched_a_reviewed_path_since_its_declaration():
    """THE HOLE THE HASH CHECK LEFT, and it cost a review session.

    2026-08-25: all six artifacts hashed correctly, the worktree was clean,
    and a Sol session STOPped anyway — the prompt pinned a bare HEAD, and
    the builder then committed twice, including committing the prompt
    itself. `test_every_artifact_under_review_still_hashes_to_what_was_sent`
    passed throughout. It compares bytes; it says nothing about the repo
    the reviewer is asked to reason about.

    Pinning HEAD cannot be the fix — committing the prompt moves HEAD, so
    the pin is stale before it is read. What is pinned instead is
    `unchanged_since`: no commit after it may touch a reviewed path. That
    stays true as unrelated work lands, and the reviewer can verify it with
    the same one-line git command rather than trusting a claim.
    """
    repo = REGISTER.parent.parent
    entries = _entries()
    if not entries:
        return

    touched = []
    for e in entries:
        out = subprocess.run(
            ["git", "log", "--oneline", f"{e['unchanged_since']}..HEAD",
             "--", e["path"]],
            cwd=repo, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        if out.stdout.strip():
            touched.append(f"{e['path']} (sent to {e['issued_to']}, "
                           f"unchanged_since {e['unchanged_since'][:12]}):\n"
                           + "\n".join("      " + l
                                       for l in out.stdout.splitlines()))
    assert not touched, (
        "a commit landed on a path a reviewer is holding; their declaration "
        "no longer describes the tree:\n  " + "\n  ".join(touched))


def test_a_review_prompt_never_pins_a_bare_head():
    """The authoring defect itself, banned mechanically.

    A bare `HEAD: <40-hex>` inside a transport block reads as a matched
    field — Sol matched it and stopped; Fable read the same shape as
    informational and proceeded. Two reviewers, one rule, opposite
    behaviour, because the prompt was ambiguous. A prompt for a LIVE review
    must declare `REVIEWED_SET_UNCHANGED_SINCE` instead, which does not go
    stale.

    Liveness is keyed on `review_id`, not on whether a prompt happens to
    mention a registered path. Keying on paths was the first attempt and it
    flagged a CLOSED review's prompt that merely names the same record — a
    guard that fires on finished work trains people to ignore it.
    """
    entries = _entries()
    if not entries:
        return
    live_ids = {e["review_id"] for e in entries}

    problems = []
    for prompt in sorted(REGISTER.parent.glob("*PROMPT*.md")):
        text = prompt.read_text(encoding="utf-8")
        if not any(rid in text for rid in live_ids):
            continue                     # not a prompt for a live review
        for m in re.finditer(r"^HEAD\s*[:=]\s*`?[0-9a-f]{40}`?",
                             text, re.M):
            problems.append(f"{prompt.name}: {m.group(0)[:24]}… — a bare "
                            "HEAD pin; use REVIEWED_SET_UNCHANGED_SINCE")
        if "REVIEWED_SET_UNCHANGED_SINCE" not in text:
            problems.append(f"{prompt.name}: references a registered "
                            "artifact but declares no "
                            "REVIEWED_SET_UNCHANGED_SINCE")
    assert not problems, "\n  ".join([""] + problems)


def test_a_live_prompt_tells_the_reviewer_to_read_it_from_disk():
    """MEASURED, 2026-08-25 — the wasted session this one is for.

    The prompt was re-issued with a corrected pin, committed, and the file
    on disk was right. The reviewer stopped anyway, quoting a pin that
    appeared nowhere in the file: it had been given the EARLIER text as a
    paste.

    The transport rule says chat-carried bytes are never a source of truth.
    Two sessions were spent before anyone noticed the rule was being
    applied to the artifacts and not to the document that declares them.

    A prompt cannot stop itself from being pasted. What it can do is tell
    the reader to open the file, and name the line that proves the copy is
    current — so this asserts both, and asserts the line number is the real
    one, because a self-check that has drifted is another stale declaration.
    """
    entries = _entries()
    if not entries:
        return
    live_ids = {e["review_id"] for e in entries}
    pins = {e["unchanged_since"] for e in entries}

    problems = []
    for prompt in sorted(REGISTER.parent.glob("*PROMPT*.md")):
        text = prompt.read_text(encoding="utf-8")
        if not any(rid in text for rid in live_ids):
            continue
        lines = text.splitlines()
        if "read" not in text.lower() or "from disk" not in text.lower():
            problems.append(f"{prompt.name}: does not tell the reviewer to "
                            "read it from disk")
        actual = [i for i, ln in enumerate(lines, 1)
                  if ln.startswith("REVIEWED_SET_UNCHANGED_SINCE")]
        cited = re.findall(r"line (\d+) of it must read", text)
        if not cited:
            problems.append(f"{prompt.name}: carries no line-number "
                            "self-check for a stale paste")
        elif len(actual) != 1 or int(cited[0]) != actual[0]:
            problems.append(
                f"{prompt.name}: self-check cites line {cited[0]}, the "
                f"declaration is on {actual or 'no'} — the self-check has "
                "drifted and is itself a stale declaration")
        for pin in pins:
            if pin not in text:
                problems.append(f"{prompt.name}: does not carry the "
                                f"registered pin {pin[:12]}")
    assert not problems, "\n  ".join([""] + problems)


#: A transport table row in a review prompt: hash, byte count, path.
_PROMPT_ROW_RE = re.compile(
    r"\|\s*`([0-9a-fA-F]{64})`\s*\|\s*(\d+)\s*\|\s*`([^`]+)`")


def test_no_review_prompt_carries_a_hash_the_register_disagrees_with():
    """A stale hash in a prompt wastes a review as surely as a moved file.

    The register and the prompt are two copies of the same claim, written
    minutes apart, and the second drifts the moment the builder touches a
    file again. Measured, 2026-08-25: three of five hashes in a prompt went
    stale inside the hour it was written, and only a hand-run cross-check
    caught it. A hand-run cross-check is not a control.
    """
    repo = REGISTER.parent.parent
    expected = {e["path"]: e["sha256"].lower() for e in _entries()}
    if not expected:
        return                      # nothing under review, nothing to check

    drift = []
    for prompt in sorted(REGISTER.parent.glob("*PROMPT*.md")):
        text = prompt.read_text(encoding="utf-8")
        for digest, size, path in _PROMPT_ROW_RE.findall(text):
            if path not in expected:
                continue
            if digest.lower() != expected[path]:
                drift.append(f"{prompt.name} -> {path}: says {digest[:16]}"
                             f"..., register says {expected[path][:16]}...")
            actual = (repo / path).stat().st_size
            if int(size) != actual:
                drift.append(f"{prompt.name} -> {path}: says {size} bytes, "
                             f"the file is {actual}")
    assert not drift, (
        "a review prompt carries a hash or size the register disagrees "
        "with; the reviewer will STOP on its opening precheck:\n  "
        + "\n  ".join(drift))
