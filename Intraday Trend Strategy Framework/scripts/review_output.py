# -*- coding: utf-8 -*-
"""The reviewer's WORKSPACE: supplied explicitly by the dispatcher, never found.

WHAT THIS IS. The sealed review object does not work out where the review seat
can write. It is TOLD, exactly once, as a launch parameter, and its whole job is
to validate that capability, take one fresh child inside it, prove the child
works by using it, and bind the child to this delivery. Everything else here is
a refusal.

WHY DISCOVERY IS GONE ENTIRELY, which took four deliveries to earn. A
bundle-local `return/` failed because a restricted token cannot write inside the
delivery whatever its ACL says. `tempfile.gettempdir()` failed because it
consults TMPDIR, TEMP and TMP -- measured: with those pointed elsewhere the
output root followed them. `GetTempPathW` and `GetTempPath2W` would have failed
the same way; their documented order is TMP, TEMP, USERPROFILE, Windows
directory, and being a Windows API does not make a function
environment-independent. A known-folder lookup avoided the environment but still
GUESSED, from profile structure, at something only the dispatcher actually
knows. Four different APIs, one mistake: inferring authority instead of
receiving it.

So there is NO default, NO fallback, NO environment read, NO known folder and NO
profile inference in this file. If the parameter is absent the delivery fails and
stops, before the guard arms and before any substantive review.

WHAT THE DISPATCHER OWNS AND WHAT THE RUNNER OWNS. The dispatcher supplies the
BASE. The runner creates and owns exactly one fresh CHILD under it. It never
reuses a child, never deletes a pre-existing one, and never enumerates the base:
every check below is a stat on one named path, not a listing.

THE PATH IS EXECUTION PROVENANCE, NOT REVIEW IDENTITY. Two seats may run the
same delivery at different absolute paths and review the same bytes, which is
why the binding carries digests and the path is deliberately not one of them.
"""
from __future__ import annotations

import json
from pathlib import Path

#: The one fixed segment under the supplied base, so a delivery's work lands in
#: a place named for it and nothing else in the base is touched.
NAMESPACE = "itsf-review"

#: The launch parameter. One spelling, no abbreviation, no environment twin.
PARAMETER = "--review-output-base"

#: What every retained reviewer artifact is bound to. The PATH is absent on
#: purpose: it is provenance, not identity.
BINDING_FIELDS = ("review_id", "manifest_sha256", "runtime_manifest_sha256",
                  "substantive_round")

BINDING_FILE = "OUTPUT_BINDING.json"
SCRATCH_NAME = ".scratch"

#: The reviewer's retained returns, named here so the runner can assert they
#: never end up inside the ephemeral directory.
RETAINED_ARTIFACTS = ("INITIAL_FINDINGS.md", "FREEZE.json", "ATTESTATION.md")


class OutputRootRefused(RuntimeError):
    """The workspace cannot be established. Always a DELIVERY FAILURE."""


# ----------------------------------------------------------------- W1 supply
def parse_workspace_base(argv) -> str:
    """Exactly one explicitly supplied workspace base. No default.

    Accepts `--review-output-base <path>` and `--review-output-base=<path>`,
    because a reviewer typing the launch line by hand should not lose a round
    to a spelling. It accepts nothing else: an unknown argument is a refusal
    rather than something to ignore, and a second occurrence is a refusal
    rather than last-one-wins.
    """
    args = [str(a) for a in argv]
    found = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == PARAMETER:
            if i + 1 >= len(args):
                raise OutputRootRefused("%s was given with no value" % PARAMETER)
            found.append(args[i + 1])
            i += 2
            continue
        if arg.startswith(PARAMETER + "="):
            found.append(arg[len(PARAMETER) + 1:])
            i += 1
            continue
        raise OutputRootRefused(
            "unrecognised launch argument %r. The only argument this runner "
            "takes is %s <authorized writable base>" % (arg, PARAMETER))
    if not found:
        raise OutputRootRefused(
            "no review workspace was supplied. This delivery does not discover "
            "one: the dispatcher must pass %s <authorized writable base>. "
            "There is deliberately no default and no fallback, and TMP, TEMP "
            "and TMPDIR are never read as authority" % PARAMETER)
    if len(found) > 1:
        raise OutputRootRefused(
            "%s was supplied %d times (%s). Exactly one workspace base is "
            "accepted, so that what was authorised is never ambiguous"
            % (PARAMETER, len(found), found))
    value = found[0].strip().strip('"')
    if not value:
        raise OutputRootRefused("%s was supplied empty" % PARAMETER)
    return value


# ---------------------------------------------------------- W2 disjointness
def canonical(path) -> Path:
    """One spelling of one location, for comparison purposes.

    `resolve()` follows junctions, reparse points and symlinks, so a base that
    is a link into a forbidden root is judged by where it actually points --
    the same reason the execution guard resolves before it compares. It works
    on paths that do not exist, which matters: a forbidden root must stay
    forbidden whether or not it happens to be present on this seat.
    """
    if path is None or not str(path).strip():
        raise OutputRootRefused("an empty path is not a location")
    try:
        return Path(str(path).strip().strip('"')).expanduser().resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        raise OutputRootRefused("%r cannot be canonicalised: %s" % (path, exc))


def _parts(path: Path) -> tuple:
    """Case-folded path COMPONENTS.

    Comparing whole strings would make `quant-data-2` look like it sits under
    `quant-data`, and a case-sensitive comparison would miss `C:\\USERS\\...`
    on a filesystem that does not care. Comparing folded components does
    neither.
    """
    return tuple(p.casefold() for p in path.parts)


def contains_or_equals(outer: Path, inner: Path) -> bool:
    a, b = _parts(outer), _parts(inner)
    return b[:len(a)] == a


def assert_disjoint(base: Path, forbidden: dict) -> list:
    """Neither inside, nor containing. BOTH directions, every forbidden root.

    A base INSIDE a forbidden root would put reviewer output in a sealed or
    governed place. A base that CONTAINS one would put a sealed or governed
    place inside the writable surface. Checking one direction leaves the other
    open, and each fails differently, so both are checked.

    Nothing here enumerates anything: every check is a comparison between two
    canonical paths.
    """
    checked = []
    for raw, label in sorted(forbidden.items()):
        if raw is None or not str(raw).strip():
            continue
        other = canonical(raw)
        checked.append("%s (%s)" % (other, label))
        if contains_or_equals(other, base):
            raise OutputRootRefused(
                "the supplied workspace base %s lies INSIDE %s (%s). Reviewer "
                "output may not land in a sealed or governed location; supply "
                "a base outside it" % (base, other, label))
        if contains_or_equals(base, other):
            raise OutputRootRefused(
                "the supplied workspace base %s CONTAINS %s (%s). A writable "
                "workspace may not enclose a sealed or governed location; "
                "supply a narrower base" % (base, other, label))
    return checked


def forbidden_roots(bundle_root: Path, manifest: dict) -> dict:
    """Everything the supplied base must be disjoint from, as path -> label.

    Most of it is DERIVED from where the delivery actually sits, so it stays
    true if the delivery moves: the bundle itself, the portable runtime beside
    it, and the directory that holds sibling review deliveries. The rest is
    DECLARED in the sealed manifest, because a sealed object cannot derive the
    live repository or the research-data roots from its own location.
    """
    bundle_root = canonical(bundle_root)
    roots = {str(bundle_root): "the sealed delivery",
             str(bundle_root.parent): "the review-delivery directory"}
    runtime_id = (manifest.get("review_runtime") or {}).get("runtime_id")
    if runtime_id:
        roots[str(bundle_root.parent / runtime_id)] = "the portable runtime"
    declared = (manifest.get("write_surfaces") or {}).get(
        "forbidden_workspace_roots") or {}
    for path, label in declared.items():
        roots[str(path)] = label
    return roots


# ------------------------------------------------------------ W3 fresh child
def _safe_segment(text: str) -> str:
    keep = [c if (c.isalnum() or c in "-_.") else "-" for c in str(text)]
    return "".join(keep)[:64].strip("-.") or "review"


def child_for(base, review_id: str, manifest_sha256: str) -> Path:
    """`<base>/itsf-review/<REVIEW_ID>-<first 12 of the manifest digest>`."""
    if not review_id or not manifest_sha256:
        raise OutputRootRefused(
            "a review workspace needs both a review id and a manifest digest; "
            "got %r / %r" % (review_id, manifest_sha256))
    return (Path(base) / NAMESPACE
            / ("%s-%s" % (_safe_segment(review_id),
                          _safe_segment(manifest_sha256)[:12])))


def create_child(base, review_id: str, manifest_sha256: str) -> Path:
    """Create exactly ONE fresh child, and refuse a pre-existing one.

    An existing child is refused even when empty, and is left exactly as it
    was. Reuse is how one run's artifacts get read as another's; deleting
    someone else's directory to make room is worse than refusing; and an empty
    directory is not evidence that it is unused -- a run may be in progress.
    """
    child = child_for(base, review_id, manifest_sha256)
    if child.exists():
        raise OutputRootRefused(
            "the review workspace %s ALREADY EXISTS. It is never reused and "
            "never removed by this runner, empty or not: a directory left by "
            "another attempt would make two runs' artifacts indistinguishable. "
            "Remove it deliberately, or supply a different workspace base"
            % child)
    try:
        child.mkdir(parents=True)
    except OSError as exc:
        raise OutputRootRefused(
            "the review workspace %s could not be created: %s" % (child, exc))
    return child


# -------------------------------------------------------- W4 capability proof
def prove_capability(child) -> list:
    """CREATE, WRITE, RENAME, DELETE -- performed, never inferred from an ACL.

    Three deliveries carried a surface whose ACL said writable and whose
    restricted token said otherwise, so the only evidence accepted here is the
    operation succeeding. It runs inside a probe directory and removes it, so
    the fresh child is still empty when the reviewer sees it.
    """
    child = Path(child)
    proved = []
    probe = child / ".capability_probe"
    try:
        probe.mkdir()
        proved.append("CREATE")
        one = probe / "a"
        one.write_text("probe", encoding="utf-8")
        proved.append("WRITE")
        one.replace(probe / "b")
        proved.append("RENAME")
        if (probe / "b").read_text(encoding="utf-8") != "probe":
            raise OutputRootRefused(
                "the review workspace %s did not return the bytes written to "
                "it" % child)
        (probe / "b").unlink()
        probe.rmdir()
        proved.append("DELETE")
    except OSError as exc:
        raise OutputRootRefused(
            "the review workspace %s failed the capability proof after %s: %s"
            % (child, proved or ["nothing"], exc))
    if probe.exists():
        raise OutputRootRefused(
            "the capability probe left residue in %s" % child)
    return proved


# -------------------------------------------------------------- W5 binding
def binding_for(manifest: dict) -> dict:
    """Read off the sealed manifest, so it cannot drift from the bytes it
    describes."""
    runtime = manifest.get("review_runtime") or {}
    return {
        "review_id": manifest["review_id"],
        "manifest_sha256": manifest["__manifest_sha256__"],
        "runtime_manifest_sha256": runtime.get("runtime_manifest_sha256", ""),
        "substantive_round": manifest["substantive_round"],
    }


def write_binding(root, binding: dict) -> Path:
    missing = [f for f in BINDING_FIELDS if not binding.get(f)]
    if missing:
        raise OutputRootRefused(
            "the output binding is missing %s; an artifact that cannot name "
            "the object it was produced against is not evidence" % missing)
    path = Path(root) / BINDING_FILE
    payload = {k: binding[k] for k in BINDING_FIELDS}
    payload["note"] = (
        "Everything in this directory was produced against the review object "
        "named above and against no other. The sealed delivery is immutable to "
        "review execution; this workspace was supplied explicitly at launch "
        "and is the only writable surface. The absolute path is execution "
        "provenance and is deliberately NOT part of the review identity above: "
        "two seats may run this delivery at different paths and review the "
        "same bytes.")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def check_binding(root, expected: dict) -> dict:
    """Refuse a workspace that belongs to a different review object."""
    path = Path(root) / BINDING_FILE
    if not path.exists():
        raise OutputRootRefused("%s carries no %s" % (root, BINDING_FILE))
    try:
        found = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise OutputRootRefused("%s is unreadable: %s" % (path, exc))
    wrong = {f: (found.get(f), expected.get(f)) for f in BINDING_FIELDS
             if found.get(f) != expected.get(f)}
    if wrong:
        raise OutputRootRefused(
            "the review workspace %s was bound to a DIFFERENT review object: "
            "%s (found, expected). Artifacts from one delivery must never be "
            "read as another's" % (root, wrong))
    return found


# ----------------------------------------------------------------- the entry
def _manifest_with_digest(bundle_root) -> dict:
    import hashlib
    raw = (Path(bundle_root) / "MANIFEST.json").read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    manifest["__manifest_sha256__"] = hashlib.sha256(raw).hexdigest()
    return manifest


def prepare(bundle_root, supplied_base) -> Path:
    """Validate the SUPPLIED capability, take one fresh child, bind it.

    The order is the argument: canonicalise, prove disjointness both ways,
    create a fresh child, exercise it, bind it, and only then hand it back for
    the guard to freeze. Nothing is discovered and nothing is assumed at any
    step, and the base is stat'd rather than listed.
    """
    bundle_root = canonical(bundle_root)
    manifest = _manifest_with_digest(bundle_root)
    binding = binding_for(manifest)

    base = canonical(supplied_base)
    if not base.is_dir():
        raise OutputRootRefused(
            "the supplied workspace base %s is not an existing directory. The "
            "dispatcher supplies a base that already exists and that it has "
            "authorised; this runner creates only its own child inside it"
            % base)
    assert_disjoint(base, forbidden_roots(bundle_root, manifest))

    child = create_child(base, binding["review_id"],
                         binding["manifest_sha256"])
    prove_capability(child)
    write_binding(child, binding)
    (child / SCRATCH_NAME).mkdir()
    return child
